#!/usr/bin/env python3
"""
用授權碼換取 Token 的工具腳本（PKCE Public Client 模式）

向 digiRunner Token 端點發送 POST 請求，換取 Access Token / Refresh Token / ID Token。

Usage:
    python exchange_token.py --domain <domain> --client-id <id> --code <code> --redirect-uri <uri> --code-verifier <verifier> [--no-ssl-verify]
"""

import argparse
import base64
import json
import ssl
import urllib.request
import urllib.parse


def generate_client_secret(client_id: str) -> str:
    """
    產生 client_secret（PKCE Public Client，無密碼）

    公式：Base64Encode(ClientID + ":")
    """
    return base64.b64encode(f"{client_id}:".encode()).decode()


def exchange_token(
    domain: str,
    client_id: str,
    code: str,
    redirect_uri: str,
    code_verifier: str,
    ssl_verify: bool = True,
) -> dict:
    """用授權碼換取 Token"""
    client_secret = generate_client_secret(client_id)

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
    }

    encoded_data = urllib.parse.urlencode(data).encode("utf-8")

    req = urllib.request.Request(
        f"https://{domain}/oauth/token",
        data=encoded_data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {client_secret}",
        },
        method="POST",
    )

    # 開發環境：跳過自簽署憑證驗證
    context = None
    if not ssl_verify:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    with urllib.request.urlopen(req, context=context) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description="用授權碼換取 Token（PKCE Public Client）")
    parser.add_argument("--domain", required=True, help="digiRunner Domain")
    parser.add_argument("--client-id", required=True, help="Client ID")
    parser.add_argument("--code", required=True, help="授權碼")
    parser.add_argument("--redirect-uri", required=True, help="Redirect URI")
    parser.add_argument("--code-verifier", required=True, help="PKCE code_verifier")
    parser.add_argument(
        "--no-ssl-verify",
        action="store_true",
        help="跳過 SSL 憑證驗證（開發環境用）",
    )
    args = parser.parse_args()

    print(f"Client Secret: {generate_client_secret(args.client_id)}")
    print(f"發送 Token 請求至 https://{args.domain}/oauth/token ...")

    try:
        tokens = exchange_token(
            domain=args.domain,
            client_id=args.client_id,
            code=args.code,
            redirect_uri=args.redirect_uri,
            code_verifier=args.code_verifier,
            ssl_verify=not args.no_ssl_verify,
        )
        print("\n✅ Token 取得成功！")
        print(json.dumps(tokens, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"\n❌ Token 取得失敗: {e}")


if __name__ == "__main__":
    main()
