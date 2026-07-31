from fastapi import APIRouter
from fastapi import Depends
from starlette.responses import Response
from starlette.status import HTTP_204_NO_CONTENT

from apps.auth.dependencies.auth_dependency import auth_dependency
from apps.auth.schemas.user_schema import AuthSchema
from apps.auth.schemas.user_schema import EncodedJWTTokenSchema
from apps.auth.schemas.user_schema import UserSchema
from apps.settings import SETTINGS
from apps.utils.enums.env_enum import EnvEnum

router = APIRouter()


@router.post('/login', response_model=EncodedJWTTokenSchema)
async def login(
    response: Response,
    auth_data: AuthSchema,
) -> EncodedJWTTokenSchema:
    """Авторизация пользователя. Ставим куки и возвращаем ответ."""
    encoded_jwt_token_schema = await auth_dependency.get_token(auth_data=auth_data)

    secure = SETTINGS.ENVIRONMENT not in (EnvEnum.LOCAL, EnvEnum.PYTEST)
    for key, value in (
        ('access_token', encoded_jwt_token_schema.access_token),
        ('refresh_token', encoded_jwt_token_schema.refresh_token),
    ):
        response.set_cookie(
            key=key,
            value=value,
            samesite='lax',
            secure=secure,
            httponly=True,
        )
    return encoded_jwt_token_schema


@router.delete('/logout', status_code=HTTP_204_NO_CONTENT)
async def logout(
    response=Depends(auth_dependency.delete_token),
) -> Response:
    """Удаление токенов из куки.

    Args:
        response (Response, optional): Starlette response.
    """
    response = Response(status_code=HTTP_204_NO_CONTENT)
    response.delete_cookie('refresh_token')
    response.delete_cookie('access_token')
    return response


@router.get(
    '/check_user',
    response_model=UserSchema,
)
async def check_user(
    user_schema: UserSchema = Depends(auth_dependency.check_token),
) -> UserSchema:
    """Получаем пользователя.

    Args:
        user_schema: пользователь
    """
    return user_schema
