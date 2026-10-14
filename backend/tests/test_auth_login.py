import hashlib
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions import AuthError
from app.models.user import Profile, User, UserRole
from app.schemas.auth import LoginRequest
from app.services import auth_service as auth_service_module
from app.services.auth_service import AuthService


def _run_immediate(coroutine):
    """Drive a service coroutine whose test doubles complete without I/O."""
    try:
        coroutine.send(None)
    except StopIteration as completed:
        return completed.value
    raise AssertionError("test double unexpectedly suspended the service coroutine")


def _test_user() -> User:
    user_id = uuid4()
    return User(
        id=user_id,
        email="learner@example.com",
        hashed_password="stored-hash",
        role=UserRole.student,
        is_active=True,
        is_email_verified=True,
        created_at=datetime.now(timezone.utc),
        profile=Profile(
            id=uuid4(),
            user_id=user_id,
            full_name="Learner",
            preferred_language="en",
        ),
    )


def _service_for_user(user):
    db = SimpleNamespace(add=MagicMock())
    service = AuthService(db)

    class FakeUserRepository:
        async def get_by_email(self, email):
            assert email == "learner@example.com"
            return user

    service.user_repo = FakeUserRepository()
    return service, db


def _patch_password_verification(monkeypatch, result):
    calls = []

    async def dispatch(function, *args):
        calls.append((function, args))
        return function(*args)

    monkeypatch.setattr(auth_service_module, "run_in_threadpool", dispatch)
    monkeypatch.setattr(auth_service_module, "verify_password", lambda *_: result)
    return calls


def test_login_keeps_token_rotation_and_profile_response(monkeypatch):
    user = _test_user()
    service, db = _service_for_user(user)
    verification_calls = _patch_password_verification(monkeypatch, True)
    monkeypatch.setattr(auth_service_module, "create_access_token", lambda **_: "access")
    monkeypatch.setattr(auth_service_module, "create_refresh_token", lambda **_: "refresh")

    result = _run_immediate(
        service.login(LoginRequest(email="learner@example.com", password="valid"))
    )

    assert result.access_token == "access"
    assert result.refresh_token == "refresh"
    assert result.user.profile.full_name == "Learner"
    assert user.refresh_token_hash == hashlib.sha256(b"refresh").hexdigest()
    db.add.assert_called_once_with(user)
    assert verification_calls == [(auth_service_module.verify_password, ("valid", "stored-hash"))]


def test_login_rejects_invalid_password_without_rotating_tokens(monkeypatch):
    user = _test_user()
    service, db = _service_for_user(user)
    _patch_password_verification(monkeypatch, False)

    with pytest.raises(AuthError, match="Invalid email or password"):
        _run_immediate(
            service.login(LoginRequest(email="learner@example.com", password="invalid"))
        )

    db.add.assert_not_called()


def test_refresh_token_validates_and_rotates_stored_hash(monkeypatch):
    user = _test_user()
    user.refresh_token_hash = AuthService._hash_token("presented-refresh")
    service, db = _service_for_user(user)

    class FakeUserRepository:
        async def get_by_id(self, user_id):
            assert user_id == user.id
            return user

        async def rotate_refresh_token_hash(self, user_id, expected_hash, replacement_hash):
            assert user_id == user.id
            assert expected_hash == AuthService._hash_token("presented-refresh")
            user.refresh_token_hash = replacement_hash
            return True

    service.user_repo = FakeUserRepository()
    monkeypatch.setattr(
        "app.core.security.decode_token", lambda _: {"type": "refresh", "sub": str(user.id)}
    )
    monkeypatch.setattr(auth_service_module, "create_access_token", lambda **_: "new-access")
    monkeypatch.setattr(auth_service_module, "create_refresh_token", lambda **_: "rotated-refresh")

    result = _run_immediate(service.refresh_token("presented-refresh"))

    assert result.access_token == "new-access"
    assert result.refresh_token == "rotated-refresh"
    assert user.refresh_token_hash == AuthService._hash_token("rotated-refresh")
    db.add.assert_not_called()


def test_refresh_token_rejects_rotated_token_without_changing_hash(monkeypatch):
    user = _test_user()
    user.refresh_token_hash = AuthService._hash_token("current-refresh")
    service, db = _service_for_user(user)

    class FakeUserRepository:
        async def get_by_id(self, user_id):
            return user

    service.user_repo = FakeUserRepository()
    monkeypatch.setattr(
        "app.core.security.decode_token", lambda _: {"type": "refresh", "sub": str(user.id)}
    )
    old_hash = user.refresh_token_hash

    with pytest.raises(AuthError, match="rotated"):
        _run_immediate(service.refresh_token("previous-refresh"))

    assert user.refresh_token_hash == old_hash
    db.add.assert_not_called()



@pytest.mark.asyncio
async def test_concurrent_refresh_requests_only_rotate_once(monkeypatch):
    import asyncio

    user = _test_user()
    original_token = "shared-refresh"
    original_hash = AuthService._hash_token(original_token)
    user.refresh_token_hash = original_hash
    current_hash = original_hash
    read_count = 0
    both_read = asyncio.Event()
    rotation_lock = asyncio.Lock()
    generated = 0

    class FakeUserRepository:
        async def get_by_id(self, user_id):
            nonlocal read_count
            read_count += 1
            snapshot = SimpleNamespace(
                id=user.id, role=user.role, is_active=True,
                refresh_token_hash=current_hash,
            )
            if read_count == 2:
                both_read.set()
            await both_read.wait()
            return snapshot

        async def rotate_refresh_token_hash(self, user_id, expected_hash, replacement_hash):
            nonlocal current_hash
            async with rotation_lock:
                if current_hash != expected_hash:
                    return False
                current_hash = replacement_hash
                return True

    service = AuthService(SimpleNamespace())
    service.user_repo = FakeUserRepository()
    monkeypatch.setattr(
        "app.core.security.decode_token",
        lambda _: {"type": "refresh", "sub": str(user.id)},
    )
    monkeypatch.setattr(auth_service_module, "create_access_token", lambda **_: "access")
    def next_refresh(**_):
        nonlocal generated
        generated += 1
        return f"replacement-{generated}"
    monkeypatch.setattr(auth_service_module, "create_refresh_token", next_refresh)

    outcomes = await asyncio.gather(
        service.refresh_token(original_token),
        service.refresh_token(original_token),
        return_exceptions=True,
    )

    successes = [item for item in outcomes if not isinstance(item, Exception)]
    failures = [item for item in outcomes if isinstance(item, Exception)]
    assert len(successes) == 1
    assert len(failures) == 1 and isinstance(failures[0], AuthError)
    assert current_hash != original_hash



def test_login_returns_user_when_optional_profile_is_missing(monkeypatch):
    user = _test_user()
    user.profile = None
    service, _db = _service_for_user(user)
    _patch_password_verification(monkeypatch, True)
    monkeypatch.setattr(auth_service_module, "create_access_token", lambda **_: "access")
    monkeypatch.setattr(auth_service_module, "create_refresh_token", lambda **_: "refresh")

    result = _run_immediate(
        service.login(LoginRequest(email="learner@example.com", password="valid"))
    )

    assert result.user is not None
    assert result.user.profile is None


def test_logout_clears_the_refresh_token_hash():
    user = _test_user()
    user.refresh_token_hash = AuthService._hash_token("active-refresh")
    service, _db = _service_for_user(user)

    class FakeUserRepository:
        async def update(self, target, **values):
            assert target is user
            for name, value in values.items():
                setattr(target, name, value)
            return target

    service.user_repo = FakeUserRepository()
    _run_immediate(service.logout(user))

    assert user.refresh_token_hash is None
