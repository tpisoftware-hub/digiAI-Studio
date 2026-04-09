#!/usr/bin/env python3
"""
產生 OIDC 授權請求 URL 的工具腳本

此腳本可獨立執行，快速產生包含 PKCE 的授權 URL。
支援自訂 digiRunner Domain、Client ID、Redirect URI 等參數。

Usage:
    python generate_auth_request.py --domain <domain> --client-id <id> --redirect-uri <uri> [--scope <scope>] [--no-pkce]
"""

import argparse
import base64
import hashlib
import secrets
import uuid
import json
from urllib.parse import urlencode


def generate_code_verifier(length: int = 64) -> str:
    """產生 PKCE code_verifier（43~128 字元的隨機字串）"""
    return secrets.token_urlsafe(length)[:128]


def generate_code_challenge(code_verifier: str) -> str:
    """從 code_verifier 產生 code_challenge（Base64URL(SHA256(code_verifier))）"""
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def generate_state() -> str:
    """產生隨機 state 值（UUID 格式）"""
    return str(uuid.uuid4())


def build_auth_url(
    domain: str,
    client_id: str,
    redirect_uri: str,
    scope: str = "openid profile email",
    use_pkce: bool = True,
) -> dict:
    """
    建構完整的授權 URL

    回傳包含 auth_url、state、code_verifier、code_challenge 的 dict
    """
    state = generate_state()

    params = {
        "response_type": "code",
        "client_id": client_id,
        "scope": scope,
        "redirect_uri": redirect_uri,
        "state": state,
    }

    result = {"state": state}

    if use_pkce:
        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier)
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = "S256"
        result["code_verifier"] = code_verifier
        result["code_challenge"] = code_challenge

    auth_url = f"https://{domain}/dgrv4/ssotoken/gtwidp/JDBC/authorization?{urlencode(params)}"
    result["auth_url"] = auth_url

    return result


def main():
    parser = argparse.ArgumentParser(description="產生 OIDC 授權請求 URL")
    parser.add_argument("--domain", required=True, help="digiRunner Domain")
    parser.add_argument("--client-id", required=True, help="Client ID")
    parser.add_argument("--redirect-uri", required=True, help="Redirect URI")
    parser.add_argument("--scope", default="openid profile email", help="OIDC Scope")
    parser.add_argument("--no-pkce", action="store_true", help="停用 PKCE 機制")
    args = parser.parse_args()

    result = build_auth_url(
        domain=args.domain,
        client_id=args.client_id,
        redirect_uri=args.redirect_uri,
        scope=args.scope,
        use_pkce=not args.no_pkce,
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\n授權 URL:\n{result['auth_url']}")
    print(f"\nState（需存入 session）: {result['state']}")
    if "code_verifier" in result:
        print(f"Code Verifier（需存入 session）: {result['code_verifier']}")


if __name__ == "__main__":
    main()
