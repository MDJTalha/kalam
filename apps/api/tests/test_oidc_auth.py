import time

import pytest
from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import RSAKey

from app.api.routes.auth import _validate_oidc_id_token


def _token_fixture(nonce: str = "nonce-123"):
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
