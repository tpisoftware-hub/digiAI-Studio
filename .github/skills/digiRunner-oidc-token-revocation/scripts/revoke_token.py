#!/usr/bin/env python3
"""
撤銷 Token (Revocation) 的工具腳本

向 digiRunner 發送 POST 請求，撤銷 Access Token 或 Refresh Token。

Usage:
    python revoke_token.py --domain <domain> --client-id <id> --token <token> --type access_token [--no-ssl-verify]
"""

import argparse
import json
import urllib.request
import urllib.parse
import ssl


def revoke_token(
    domain: str,
    client_id: str,
    token: str,
    token_type_hint: str,
    ssl_verify: bool = True,
) -> dict:
    """撤銷 Token（access_token 或 refresh_token）"""
    data = {
        "token": token,
        "token_type_hint": token_type_hint,
        "client_id": client_id,
    }

    encoded_data = urllib.parse.urlencode(data).encode("utf-8")

    req = urllib.request.Request(
        f"https://{domain}/oauth/revocation",
        data=encoded_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
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
    parser = argparse.ArgumentParser(description="撤銷 Token (Revocation)")
    parser.add_argument("--domain", required=True, help="digiRunner Domain")
    parser.add_argument("--client-id", required=True, help="Client ID")
    parser.add_argument("--token", required=True, help="要撤銷的 Token")
    parser.add_argument(
        "--type",
        required=True,
        choices=["access_token", "refresh_token"],
        help="Token 類型",
    )
    parser.add_argument(
        "--no-ssl-verify",
        action="store_true",
        help="跳過 SSL 憑證驗證（開發環境用）",
    )
    args = parser.parse_args()

    print(f"撤銷 {args.type} 至 https://{args.domain}/oauth/revocation ...")
    try:
        result = revoke_token(
            domain=args.domain,
            client_id=args.client_id,
            token=args.token,
            token_type_hint=args.type,
            ssl_verify=not args.no_ssl_verify,
        )
        print("\n✅ Token 撤銷完成！")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"\n❌ Token 撤銷失敗: {e}")


if __name__ == "__main__":
    main()
