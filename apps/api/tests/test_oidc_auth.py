import time

import pytest
from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import RSAKey

from app.api.routes.auth import _validate_oidc_id_token


def _token_fixture(
    nonce: str = "nonce-123",
    overrides: dict | None = None,
    remove_claims: set[str] | None = None,
):
    key = RSAKey.generate_key(auto_kid=True)
    issuer = "https://idp.example.com"
    client_id = "kognivon-client"
    claims = {
        "iss": issuer,
        "aud": client_id,
        "sub": "user-123",
        "email": "user@example.com",
        "email_verified": True,
        "nonce": nonce,
        "iat": int(time.time()),
        "exp": int(time.time()) + 300,
    }
    if overrides:
        claims.update(overrides)
    for claim in remove_claims or set():
        claims.pop(claim, None)
    token = jwt.encode({"alg": "RS256", "kid": key.thumbprint()}, claims, key, algorithms=["RS256"])
    jwks = {"keys": [key.as_dict(private=False)]}
    return token, jwks, issuer, client_id


def test_oidc_id_token_validates_signature_and_claims():
    token, jwks, issuer, client_id = _token_fixture()
    claims = _validate_oidc_id_token(token, jwks, issuer=issuer, client_id=client_id, nonce="nonce-123")
    assert claims["email"] == "user@example.com"


def test_oidc_id_token_rejects_wrong_nonce():
    token, jwks, issuer, client_id = _token_fixture()
    with pytest.raises(JoseError):
        _validate_oidc_id_token(token, jwks, issuer=issuer, client_id=client_id, nonce="wrong-nonce")


def test_oidc_id_token_requires_iat():
    token, jwks, issuer, client_id = _token_fixture(remove_claims={"iat"})
    with pytest.raises(JoseError):
        _validate_oidc_id_token(token, jwks, issuer=issuer, client_id=client_id, nonce="nonce-123")


@pytest.mark.parametrize(
    "overrides",
    [
        {"aud": ["kognivon-client", "another-client"]},
        {"aud": ["kognivon-client", "another-client"], "azp": "another-client"},
    ],
)
def test_oidc_id_token_rejects_missing_or_mismatched_azp(overrides):
    token, jwks, issuer, client_id = _token_fixture(overrides=overrides)
    with pytest.raises(JoseError):
        _validate_oidc_id_token(token, jwks, issuer=issuer, client_id=client_id, nonce="nonce-123")


def test_oidc_id_token_accepts_valid_azp_for_multi_audience_token():
    token, jwks, issuer, client_id = _token_fixture(
        overrides={"aud": [client_id := "kognivon-client", "another-client"], "azp": client_id}
    )
    claims = _validate_oidc_id_token(token, jwks, issuer=issuer, client_id=client_id, nonce="nonce-123")
    assert claims["azp"] == client_id
