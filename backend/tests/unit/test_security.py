from datetime import UTC, datetime

import jwt
import pytest
from src.core.config import settings
from src.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)


def test_password_hash_can_verify_only_the_original_password() -> None:
    password = "example-test-password"
    encoded = hash_password(password)

    assert encoded != password
    assert verify_password(password, encoded)
    assert not verify_password("different-example-password", encoded)


@pytest.mark.parametrize(
    ("create_token", "expected_type", "lifetime_seconds"),
    [
        (create_access_token, "access", settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
        (create_refresh_token, "refresh", settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400),
    ],
)
def test_token_contains_identity_type_and_expiration(
    create_token, expected_type: str, lifetime_seconds: int
) -> None:
    identity = {"sub": "buyer@example.com", "id": 42, "role": "buyer"}
    before = int(datetime.now(UTC).timestamp())
    token = create_token(identity)
    after = int(datetime.now(UTC).timestamp())
    claims = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    assert identity == {"sub": "buyer@example.com", "id": 42, "role": "buyer"}
    assert {key: claims[key] for key in identity} == identity
    assert claims["token_type"] == expected_type
    assert before + lifetime_seconds <= claims["exp"] <= after + lifetime_seconds
