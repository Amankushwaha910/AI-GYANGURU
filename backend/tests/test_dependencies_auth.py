import pytest
from fastapi import HTTPException
from fastapi.dependencies.utils import get_dependant
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError

from app.core import dependencies


def test_bearer_validation_precedes_database_session_dependency():
    for endpoint_dependency in (
        dependencies.get_current_user,
        dependencies.get_current_user_fast,
    ):
        dependant = get_dependant(path="/", call=endpoint_dependency)
        assert [dependency.call for dependency in dependant.dependencies] == [
            dependencies.get_authenticated_user_id,
            dependencies.get_db,
        ]


@pytest.mark.asyncio
async def test_missing_bearer_credentials_return_401():
    with pytest.raises(HTTPException) as caught:
        await dependencies._decode_user_id(None)

    assert caught.value.status_code == 401
    assert caught.value.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"type": "refresh", "sub": "2d17a763-e461-4a5e-a0e8-c3da0b5184a6"},
        {"type": "access", "sub": "not-a-uuid"},
        {"type": "access"},
    ],
)
async def test_invalid_access_claims_return_401(monkeypatch, payload):
    monkeypatch.setattr(dependencies, "decode_token", lambda _: payload)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="dummy")

    with pytest.raises(HTTPException) as caught:
        await dependencies._decode_user_id(credentials)

    assert caught.value.status_code == 401


@pytest.mark.asyncio
async def test_expired_token_returns_401(monkeypatch):
    def expired(_):
        raise JWTError("expired token")
    monkeypatch.setattr(dependencies, "decode_token", expired)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="dummy")

    with pytest.raises(HTTPException) as caught:
        await dependencies._decode_user_id(credentials)

    assert caught.value.status_code == 401
