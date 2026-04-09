#!/usr/bin/env python3
"""
使用 Refresh Token 換取新 Access Token 的工具腳本（PKCE Public Client 模式）

向 digiRunner Token 端點發送 POST 請求，用 Refresh Token 取得新的 Access Token。

Usage:
    python refresh_token.py --domain <domain> --client-id <id> --refresh-token <token> [--no-ssl-verify]
"""

import argparse
import base64
import json
import urllib.request
import urllib.parse
import ssl


def generate_client_secret(client_id: str) -> str:
    """
    產生 client_secret（PKCE Public Client，無密碼）

    公式：Base64Encode(ClientID + ":")
    """
    return base64.b64encode(f"{client_id}:".encode()).decode()


def refresh_access_token(
    domain: str,
    client_id: str,
    refresh_token: str,
    ssl_verify: bool = True,
) -> dict:
    """使用 Refresh Token 換取新的 Access Token"""
    client_secret = generate_client_secret(client_id)

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
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
    parser = argparse.ArgumentParser(
        description="使用 Refresh Token 換取新 Access Token（PKCE Public Client）"
    )
    parser.add_argument("--domain", required=True, help="digiRunner Domain")
    parser.add_argument("--client-id", required=True, help="Client ID")
    parser.add_argument("--refresh-token", required=True, help="Refresh Token")
    parser.add_argument(
        "--no-ssl-verify",
        action="store_true",
        help="跳過 SSL 憑證驗證（開發環境用）",
    )
    args = parser.parse_args()

    print(f"Client Secret: {generate_client_secret(args.client_id)}")
    print(f"發送 Token 刷新請求至 https://{args.domain}/oauth/token ...")

    try:
        tokens = refresh_access_token(
            domain=args.domain,
            client_id=args.client_id,
            refresh_token=args.refresh_token,
            ssl_verify=not args.no_ssl_verify,
        )
        print("\n✅ Token 刷新成功！")
        print(json.dumps(tokens, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"\n❌ Token 刷新失敗: {e}")


if __name__ == "__main__":
    main()
