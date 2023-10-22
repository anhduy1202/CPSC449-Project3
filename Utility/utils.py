import base64
import hashlib
import secrets
import os
import sys
import json
import datetime

from jwcrypto import jwk

ALGORITHM = "pbkdf2_sha256"


def hash_password(password, salt=None, iterations=260000):
    if salt is None:
        salt = secrets.token_hex(16)
    assert salt and isinstance(salt, str) and "$" not in salt
    assert isinstance(password, str)
    pw_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
    )
    b64_hash = base64.b64encode(pw_hash).decode("ascii").strip()
    return "{}${}${}${}".format(ALGORITHM, iterations, salt, b64_hash)


def verify_password(password, password_hash):
    if (password_hash or "").count("$") != 3:
        return False
    algorithm, iterations, salt, b64_hash = password_hash.split("$", 3)
    iterations = int(iterations)
    assert algorithm == ALGORITHM
    compare_hash = hash_password(password, salt, iterations)
    return secrets.compare_digest(password_hash, compare_hash)

def expiration_in(minutes):
    creation = datetime.datetime.now(tz=datetime.timezone.utc)
    expiration = creation + datetime.timedelta(minutes=minutes)
    return creation, expiration


def generate_claims(username, user_id, roles):
    _, exp = expiration_in(20)

    claims = {
        "aud": "krakend.local.gd",
        "iss": "auth.local.gd",
        "sub": username,
        "jti": str(user_id),
        "roles": roles,
        "exp": int(exp.timestamp()),
    }
    token = {
        "access_token": claims,
        "refresh_token": claims,
        "exp": int(exp.timestamp()),
    }

    output = json.dumps(token, indent=4)
    claim_json = json.loads(output)
    print (claim_json)
    return claim_json   


def generate_keys(key_ids):
    keys = [jwk.JWK.generate(kid=key_id, kty="RSA", alg="RS256") for key_id in key_ids]
    exported_keys = [
        key.export(private_key=private) for key in keys for private in [False, True]
    ]
    keys_as_json = [json.loads(exported_key) for exported_key in exported_keys]
    jwks = {"keys": keys_as_json}
    output = json.dumps(jwks, indent=4)
    print(output)