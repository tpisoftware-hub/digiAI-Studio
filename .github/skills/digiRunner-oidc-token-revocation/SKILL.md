---
name: digirunner-oidc-token-revocation
description: >
  撤銷 (Revoke) Access Token 或 Refresh Token，使其立即失效。
  當用戶登出應用程式時，撤銷其 Token 以確保安全性。
  觸發時機：使用者提到「撤銷 token」、「revoke token」、「登出」、「logout」、「token 失效」、
  「取消授權」、「revocation」等關鍵字。
---

# 撤銷 Token (Token Revocation)

## Overview

當用戶登出應用程式時，撤銷其 Access Token 或 Refresh Token，使 Token 立即失效，確保安全性。

## 撤銷端點

```
POST https://{digiRunner_DOMAIN}/oauth/revocation
Content-Type: application/x-www-form-urlencoded
```

## 請求參數

| 參數 | 類型 | 必要性 | 描述 |
|------|------|--------|------|
| token | String | Required | 要撤銷的 access token 或 refresh token |
| token_type_hint | String | Required | 說明要撤銷的 Token 類型。撤銷 Access Token 請輸入 `access_token`；撤銷 Refresh Token 請輸入 `refresh_token` |
| client_id | String | Required | 於 digiRunner 註冊的 Client ID |
| client_secret | String | Optional | PKCE + Public Client 流程（無需 Client 密碼）：若 digiRunner 的 OAuth Grant Type 欄位已勾選 **Public Client (With PKCE)**，則可省略此參數 |

## 成功回應格式

```json
{
    "code": "token_revoke_success",
    "message": "access token revoke success, jti: 813a1d99-8a72-40a6-bf42-e26df6eadcb0"
}
```

### 回應欄位說明

| 參數 | 類型 | 描述 |
|------|------|------|
| code | String | revoke 結果碼：`token_revoke_success`（本次 revoke 成功）或 `token_already_revoked`（Token 已為撤銷狀態） |
| message | String | 對此 revoke 結果碼的進一步描述 |

## 錯誤回應格式

如果 client 密碼錯誤，回傳 401 Unauthorized：

```json
{
    "timestamp": "1685332432791",
    "status": 401,
    "error": "Unauthorized",
    "message": "The client account or password is incorrect. clientId: tspclient",
    "path": "/oauth/revocation"
}
```

## 程式碼產生指引

> ⚠️ `DIGIRUNNER_DOMAIN`、`CLIENT_ID` 因環境而異，必須從環境變數讀取，不可寫死。
> ⚠️ digiRunner 的 Protocol **必須**為 `https://`，禁止使用 `http://`。
> ⚠️ 開發環境使用自簽署憑證時，需根據 `DIGIRUNNER_SSL_VERIFY` 環境變數決定是否跳過 SSL 驗證。

### JavaScript / TypeScript（前端）

```typescript
import https from "https";

const DIGIRUNNER_DOMAIN = import.meta.env.VITE_DIGIRUNNER_DOMAIN;
const CLIENT_ID = import.meta.env.VITE_CLIENT_ID;
const SSL_VERIFY = import.meta.env.VITE_DIGIRUNNER_SSL_VERIFY !== "false";

/**
 * 撤銷 Token（Access Token 或 Refresh Token）
 */
async function revokeToken(
  token: string,
  tokenTypeHint: "access_token" | "refresh_token"
): Promise<any> {
  const fetchOptions: RequestInit = {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      token,
      token_type_hint: tokenTypeHint,
      client_id: CLIENT_ID,
    }),
  };

  // 開發環境：跳過自簽署憑證驗證（僅 Node.js 環境）
  if (!SSL_VERIFY && typeof process !== "undefined") {
    (fetchOptions as any).agent = new https.Agent({ rejectUnauthorized: false });
  }

  const response = await fetch(
    `https://${DIGIRUNNER_DOMAIN}/oauth/revocation`,
    fetchOptions
  );
  return response.json();
}

// 登出時撤銷 Access Token
await revokeToken(accessToken, "access_token");
// 也可撤銷 Refresh Token
await revokeToken(refreshToken, "refresh_token");
```

### Python

```python
import requests
import os

DIGIRUNNER_DOMAIN = os.environ["DIGIRUNNER_DOMAIN"]
CLIENT_ID = os.environ["CLIENT_ID"]
SSL_VERIFY = os.environ.get("DIGIRUNNER_SSL_VERIFY", "true").lower() == "true"

def revoke_token(token: str, token_type_hint: str) -> dict:
    """撤銷 Token（access_token 或 refresh_token）"""
    response = requests.post(
        f"https://{DIGIRUNNER_DOMAIN}/oauth/revocation",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "token": token,
            "token_type_hint": token_type_hint,
            "client_id": CLIENT_ID,
        },
        verify=SSL_VERIFY,  # 開發環境 False 跳過自簽署憑證驗證
    )
    response.raise_for_status()
    return response.json()

# 登出時撤銷 Access Token
result = revoke_token(access_token, "access_token")
# 也可撤銷 Refresh Token
result = revoke_token(refresh_token, "refresh_token")
```

### Java (Spring Boot)

```java
String digiRunnerDomain = System.getenv("DIGIRUNNER_DOMAIN");
String clientId = System.getenv("CLIENT_ID");

MultiValueMap<String, String> body = new LinkedMultiValueMap<>();
body.add("token", accessToken);
body.add("token_type_hint", "access_token");
body.add("client_id", clientId);

HttpHeaders headers = new HttpHeaders();
headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);

ResponseEntity<Map> response = restTemplate.postForEntity(
    "https://" + digiRunnerDomain + "/oauth/revocation",
    new HttpEntity<>(body, headers), Map.class);
```

### cURL

```bash
# 撤銷 Access Token
curl -X POST 'https://{digiRunner_DOMAIN}/oauth/revocation' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'token={access_token}' \
  -d 'token_type_hint=access_token' \
  -d 'client_id={client_id}' \
  -k   # 開發環境：跳過自簽署憑證驗證（生產環境移除 -k）

# 撤銷 Refresh Token
curl -X POST 'https://{digiRunner_DOMAIN}/oauth/revocation' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'token={refresh_token}' \
  -d 'token_type_hint=refresh_token' \
  -d 'client_id={client_id}' \
  -k
```

## 注意事項

- 登出流程建議同時撤銷 Access Token 和 Refresh Token
- `token_type_hint` 必須與要撤銷的 Token 類型對應（`access_token` 或 `refresh_token`）
- PKCE + Public Client 模式下不需帶 `client_secret`
- 已撤銷的 Token 再次撤銷會回傳 `token_already_revoked`，不會報錯
- 開發環境使用 `-k`（cURL）或 `verify=False`（Python）跳過自簽署憑證驗證
