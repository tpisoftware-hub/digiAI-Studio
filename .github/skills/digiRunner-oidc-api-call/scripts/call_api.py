#!/usr/bin/env python3
"""
以 Token 呼叫 digiRunner API 的工具腳本

Usage:
    python call_api.py --domain <domain> --api-path <path> --id-token <token> --access-token <token> [--method POST] [--body '{"key":"value"}'] [--no-ssl-verify]
"""

import argparse
import json
import ssl
import urllib.request


def call_digirunner_api(
    domain: str,
    api_path: str,
    id_token: str,
    access_token: str,
    method: str = "POST",
    body: dict = None,
    ssl_verify: bool = True,
) -> dict:
    """以 ID Token 和 Access Token 呼叫 digiRunner API"""
    url = f"https://{domain}{api_path}"

    headers = {
        "ID-Token": id_token,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    data = json.dumps(body).encode("utf-8") if body else None

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    # 開發環境：跳過自簽署憑證驗證
    context = None
    if not ssl_verify:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    with urllib.request.urlopen(req, context=context) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description="呼叫 digiRunner API")
    parser.add_argument("--domain", required=True, help="digiRunner Domain")
    parser.add_argument("--api-path", required=True, help="API 路徑（例如 /tsmpc/tspTest/postApi）")
    parser.add_argument("--id-token", required=True, help="ID Token")
    parser.add_argument("--access-token", required=True, help="Access Token")
    parser.add_argument("--method", default="POST", help="HTTP Method（預設 POST）")
    parser.add_argument("--body", default=None, help="JSON Request Body")
    parser.add_argument(
        "--no-ssl-verify",
        action="store_true",
        help="跳過 SSL 憑證驗證（開發環境用）",
    )
    args = parser.parse_args()

    body = json.loads(args.body) if args.body else None

    print(f"呼叫 API: https://{args.domain}{args.api_path}")
    try:
        result = call_digirunner_api(
            domain=args.domain,
            api_path=args.api_path,
            id_token=args.id_token,
            access_token=args.access_token,
            method=args.method,
            body=body,
            ssl_verify=not args.no_ssl_verify,
        )
        print("\n✅ API 呼叫成功！")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"\n❌ API 呼叫失敗: {e}")


if __name__ == "__main__":
    main()
