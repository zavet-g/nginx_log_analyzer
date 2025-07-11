from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.v1.models.log_entry_model import LogEntryModel
from apps.api.v1.schemas.analytics_schema import (
    StatusCodeStats,
    TopIPsStats,
    TopURLsStats,
    TrafficStats,
    ErrorStats,
    TimeSeriesData
)
from apps.auth.dependencies.auth_dependency import auth_dependency
from apps.auth.schemas.user_schema import UserSchema
from apps.db.session import connector

router = APIRouter()


@router.get("/analytics/status-codes", response_model=List[StatusCodeStats])
async def get_status_code_stats(
    hours: int = Query(24, description="Количество часов для анализа"),
    user: UserSchema = Depends(auth_dependency.check_token),
    db: AsyncSession = Depends(connector.get_pg_session),
) -> List[StatusCodeStats]:
    """Получает статистику по HTTP статус кодам."""
    since = datetime.now() - timedelta(hours=hours)
    
    stmt = (
        select(
            LogEntryModel.status,
            func.count(LogEntryModel.id).label("count")
        )
        .where(LogEntryModel.timestamp >= since)
        .group_by(LogEntryModel.status)
        .order_by(func.count(LogEntryModel.id).desc())
    )
    
    result = await db.execute(stmt)
    return [
        StatusCodeStats(status=row.status, count=row.count)
        for row in result.fetchall()
    ]


@router.get("/analytics/top-ips", response_model=List[TopIPsStats])
async def get_top_ips(
    limit: int = Query(10, description="Количество топ IP адресов"),
    hours: int = Query(24, description="Количество часов для анализа"),
    user: UserSchema = Depends(auth_dependency.check_token),
    db: AsyncSession = Depends(connector.get_pg_session),
) -> List[TopIPsStats]:
    """Получает топ IP адресов по количеству запросов."""
    since = datetime.now() - timedelta(hours=hours)
    
    stmt = (
        select(
            LogEntryModel.remote_addr,
            func.count(LogEntryModel.id).label("requests"),
            func.avg(LogEntryModel.size).label("avg_size")
        )
        .where(LogEntryModel.timestamp >= since)
        .group_by(LogEntryModel.remote_addr)
        .order_by(func.count(LogEntryModel.id).desc())
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    return [
        TopIPsStats(
            ip=row.remote_addr,
            requests=row.requests,
            avg_size=int(row.avg_size or 0)
        )
        for row in result.fetchall()
    ]


@router.get("/analytics/top-urls", response_model=List[TopURLsStats])
async def get_top_urls(
    limit: int = Query(10, description="Количество топ URL"),
    hours: int = Query(24, description="Количество часов для анализа"),
    user: UserSchema = Depends(auth_dependency.check_token),
    db: AsyncSession = Depends(connector.get_pg_session),
) -> List[TopURLsStats]:
    """Получает топ URL по количеству запросов."""
    since = datetime.now() - timedelta(hours=hours)
    
    stmt = (
        select(
            LogEntryModel.uri,
            func.count(LogEntryModel.id).label("requests"),
            func.avg(LogEntryModel.size).label("avg_size")
        )
        .where(LogEntryModel.timestamp >= since)
        .group_by(LogEntryModel.uri)
        .order_by(func.count(LogEntryModel.id).desc())
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    return [
        TopURLsStats(
            url=row.uri,
            requests=row.requests,
            avg_size=int(row.avg_size or 0)
        )
        for row in result.fetchall()
    ]


@router.get("/analytics/traffic", response_model=TrafficStats)
async def get_traffic_stats(
    hours: int = Query(24, description="Количество часов для анализа"),
    user: UserSchema = Depends(auth_dependency.check_token),
    db: AsyncSession = Depends(connector.get_pg_session),
) -> TrafficStats:
    """Получает общую статистику трафика."""
    since = datetime.now() - timedelta(hours=hours)
    
    stmt = (
        select(
            func.count(LogEntryModel.id).label("total_requests"),
            func.sum(LogEntryModel.size).label("total_bytes"),
            func.avg(LogEntryModel.size).label("avg_request_size"),
            func.count(LogEntryModel.remote_addr.distinct()).label("unique_ips")
        )
        .where(LogEntryModel.timestamp >= since)
    )
    
    result = await db.execute(stmt)
    row = result.fetchone()
    
    return TrafficStats(
        total_requests=row.total_requests or 0,
        total_bytes=row.total_bytes or 0,
        avg_request_size=int(row.avg_request_size or 0),
        unique_ips=row.unique_ips or 0,
        period_hours=hours
    )


@router.get("/analytics/errors", response_model=List[ErrorStats])
async def get_error_stats(
    hours: int = Query(24, description="Количество часов для анализа"),
    user: UserSchema = Depends(auth_dependency.check_token),
    db: AsyncSession = Depends(connector.get_pg_session),
) -> List[ErrorStats]:
    """Получает статистику ошибок (4xx, 5xx)."""
    since = datetime.now() - timedelta(hours=hours)
    
    stmt = (
        select(
            LogEntryModel.status,
            LogEntryModel.uri,
            LogEntryModel.remote_addr,
            LogEntryModel.timestamp,
            LogEntryModel.user_agent
        )
        .where(
            and_(
                LogEntryModel.timestamp >= since,
                LogEntryModel.status >= 400
            )
        )
        .order_by(LogEntryModel.timestamp.desc())
        .limit(100)
    )
    
    result = await db.execute(stmt)
    return [
        ErrorStats(
            status=row.status,
            url=row.uri,
            ip=row.remote_addr,
            timestamp=row.timestamp,
            user_agent=row.user_agent
        )
        for row in result.fetchall()
    ]


@router.get("/analytics/time-series", response_model=List[TimeSeriesData])
async def get_time_series_data(
    hours: int = Query(24, description="Количество часов для анализа"),
    interval_minutes: int = Query(5, description="Интервал в минутах"),
    user: UserSchema = Depends(auth_dependency.check_token),
    db: AsyncSession = Depends(connector.get_pg_session),
) -> List[TimeSeriesData]:
    """Получает временные ряды запросов."""
    since = datetime.now() - timedelta(hours=hours)
    
    # Группируем по интервалам времени
    stmt = (
        select(
            func.date_trunc('hour', LogEntryModel.timestamp).label("time_bucket"),
            func.count(LogEntryModel.id).label("requests"),
            func.sum(LogEntryModel.size).label("bytes")
        )
        .where(LogEntryModel.timestamp >= since)
        .group_by(func.date_trunc('hour', LogEntryModel.timestamp))
        .order_by(func.date_trunc('hour', LogEntryModel.timestamp))
    )
    
    result = await db.execute(stmt)
    return [
        TimeSeriesData(
            timestamp=row.time_bucket,
            requests=row.requests,
            bytes=row.bytes or 0
        )
        for row in result.fetchall()
    ] 