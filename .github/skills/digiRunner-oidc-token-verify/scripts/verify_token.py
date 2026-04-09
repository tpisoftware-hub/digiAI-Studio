#!/usr/bin/env python3
"""
驗證 ID Token 的工具腳本

透過呼叫 digiRunner 驗證 API 確認 ID Token 是否合法。

Usage:
    python verify_token.py --domain <domain> --id-token <token> [--no-ssl-verify]
"""

import argparse
import json
import ssl
import urllib.request
import urllib.parse


def verify_id_token(domain: str, id_token: str, ssl_verify: bool = True) -> dict:
    """呼叫 digiRunner 驗證 API 確認 ID Token 合法性"""
    url = f"https://{domain}/dgrv4/ssotoken/gtwidp/verify"

    data = urllib.parse.urlencode({"id_token": id_token}).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
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
    parser = argparse.ArgumentParser(description="驗證 ID Token")
    parser.add_argument("--domain", required=True, help="digiRunner Domain")
    parser.add_argument("--id-token", required=True, help="ID Token (JWT)")
    parser.add_argument(
        "--no-ssl-verify",
        action="store_true",
        help="跳過 SSL 憑證驗證（開發環境用）",
    )
    args = parser.parse_args()

    print(f"驗證 ID Token 至 https://{args.domain}/dgrv4/ssotoken/gtwidp/verify ...")
    try:
        result = verify_id_token(args.domain, args.id_token, ssl_verify=not args.no_ssl_verify)
        print("\n✅ ID Token 驗證成功！")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"\n❌ ID Token 驗證失敗: {e}")


if __name__ == "__main__":
    main()
