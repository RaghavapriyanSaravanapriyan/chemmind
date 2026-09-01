from datetime import timedelta
import pytest
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


def test_password_hashing_and_verification():
    raw_password = "SuperSecretChemistPassword123!"
    hashed = get_password_hash(raw_password)

    # Hash should be non-empty and not equal to raw password
    assert hashed != raw_password
    assert len(hashed) > 20

    # Verification should succeed for correct password
    assert verify_password(raw_password, hashed) is True

    # Verification must fail for incorrect password
    assert verify_password("WrongPassword123!", hashed) is False
    assert verify_password("", hashed) is False


def test_jwt_token_creation_and_decoding():
    user_id = "user_chem_789"
    token = create_access_token(subject=user_id)

    assert isinstance(token, str)
    assert len(token.split(".")) == 3  # Header.Payload.Signature

    payload = decode_access_token(token)
    assert payload is not None
    assert payload.get("sub") == user_id
    assert "exp" in payload


def test_jwt_token_expiration():
    user_id = "user_expired_001"
    # Token expired 1 minute ago
    expired_token = create_access_token(
        subject=user_id,
        expires_delta=timedelta(minutes=-1),
    )

    payload = decode_access_token(expired_token)
    # PyJWT raises ExpiredSignatureError which decode_access_token catches and returns None
    assert payload is None


def test_jwt_token_tampering():
    user_id = "user_tamper_001"
    token = create_access_token(subject=user_id)

    parts = token.split(".")
    # Tamper with the payload part
    tampered_token = f"{parts[0]}.eyJhZG1pbiI6dHJ1ZX0.{parts[2]}"

    payload = decode_access_token(tampered_token)
    assert payload is None


def test_jwt_token_malformed_string():
    assert decode_access_token("this.is.not.a.valid.jwt") is None
    assert decode_access_token("") is None
    assert decode_access_token("Bearer xyz") is None
