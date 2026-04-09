#!/usr/bin/env python3
"""
處理 OIDC 授權回應 (Callback) 的工具腳本

解析 Redirect URI 上的 query parameters，判斷授權成功或失敗。

Usage:
    python parse_callback.py --url "https://digirunner.example.com/website/my_app/callback?code=xxx&state=yyy"
    python parse_callback.py --url "https://digirunner.example.com/website/my_app/callback?rtn_code=cancel&msg=xxx"
"""

import argparse
import base64
import json
from urllib.parse import urlparse, parse_qs


def parse_callback_url(url: str) -> dict:
    """
    解析 callback URL，回傳授權碼或錯誤資訊

    回傳 dict 包含：
    - success: bool
    - code: 授權碼（成功時）
    - state: state 值（成功時）
    - error_code: 錯誤碼（失敗時）
    - error_message: 解碼後的錯誤訊息（失敗時）
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    # 檢查是否為錯誤回應
    if "rtn_code" in params:
        rtn_code = params["rtn_code"][0]
        msg_encoded = params.get("msg", [""])[0]

        # Base64URL Decode 錯誤訊息
        try:
            padding = 4 - len(msg_encoded) % 4
            msg_decoded = base64.urlsafe_b64decode(
                msg_encoded + "=" * padding
            ).decode("utf-8")
        except Exception:
            msg_decoded = msg_encoded

        return {
            "success": False,
            "error_code": rtn_code,
            "error_message": msg_decoded,
        }

    # 成功回應
    code = params.get("code", [None])[0]
    state = params.get("state", [None])[0]

    if not code:
        return {"success": False, "error_code": "missing_code", "error_message": "URL 中缺少授權碼"}

    return {
        "success": True,
        "code": code,
        "state": state,
    }


def main():
    parser = argparse.ArgumentParser(description="解析 OIDC Callback URL")
    parser.add_argument("--url", required=True, help="Callback URL")
    args = parser.parse_args()

    result = parse_callback_url(args.url)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if result["success"]:
        print(f"\n✅ 授權成功！")
        print(f"   授權碼: {result['code']}")
        print(f"   State:  {result['state']}")
    else:
        print(f"\n❌ 授權失敗！")
        print(f"   錯誤碼: {result['error_code']}")
        print(f"   錯誤訊息: {result['error_message']}")


if __name__ == "__main__":
    main()
