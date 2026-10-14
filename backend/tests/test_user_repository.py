from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models.user import Profile, User, UserRole
from app.repositories.user_repository import UserRepository


def test_get_by_email_query_loads_optional_profile_in_one_statement():
    statement = UserRepository._get_by_email_statement("Student@Example.com")
    compiled = statement.compile(dialect=dialect())
    sql = str(compiled)

    assert "LEFT OUTER JOIN profiles" in sql
    assert "users.email =" in sql
    assert list(compiled.params.values()) == ["student@example.com"]


def test_get_by_email_returns_user_with_or_without_optional_profile():
    engine = create_engine("sqlite:///:memory:")
    try:
        Base.metadata.create_all(engine, tables=[User.__table__, Profile.__table__])
        with Session(engine) as session:
            with_profile_id = uuid4()
            without_profile_id = uuid4()
            session.add_all([
                User(
                    id=with_profile_id,
                    email="with-profile@example.com",
                    hashed_password="hash",
                    role=UserRole.student,
                    is_active=True,
                    is_email_verified=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    profile=Profile(
                        id=uuid4(),
                        user_id=with_profile_id,
                        full_name="Learner",
                        preferred_language="en",
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    ),
                ),
                User(
                    id=without_profile_id,
                    email="without-profile@example.com",
                    hashed_password="hash",
                    role=UserRole.student,
                    is_active=True,
                    is_email_verified=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                ),
            ])
            session.commit()

            with_profile = session.execute(
                UserRepository._get_by_email_statement("with-profile@example.com")
            ).scalar_one_or_none()
            without_profile = session.execute(
                UserRepository._get_by_email_statement("without-profile@example.com")
            ).scalar_one_or_none()

            assert with_profile is not None
            assert with_profile.profile is not None
            assert with_profile.profile.full_name == "Learner"
            assert without_profile is not None
            assert without_profile.profile is None
    finally:
        engine.dispose()
