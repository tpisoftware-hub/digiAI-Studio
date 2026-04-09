---
name: digirunner-oidc-token-refresh
description: >
  使用 Refresh Token 換取新的 Access Token，當 Access Token 過期時自動更新。
  產生向 digiRunner Token 端點發送 POST 請求的程式碼，支援 PKCE (Public Client) 模式。
  觸發時機：使用者提到「刷新 token」、「refresh token」、「更新 access token」、「token 過期」、
  「token expired」、「重新取得 token」、「renew token」等關鍵字。
---

# 應用 Refresh Token

## Overview

當 Access Token 過期時，使用 Refresh Token 向 digiRunner Token 端點取得新的 Access Token，無需使用者重新登入。

## Token 端點

```
POST https://{digiRunner_DOMAIN}/oauth/token
Content-Type: application/x-www-form-urlencoded
Authorization: Basic {client_secret}
```

## 請求參數

| 參數 | 類型 | 必要性 | 描述 |
|------|------|--------|------|
| client_secret | String | Required | 見下方產生方式（放在 `Authorization: Basic` Header 中） |
| grant_type | String | Required | 固定值 `refresh_token` |
| refresh_token | String | Required | 與要重新發布的 Access Token 對應的 Refresh Token。如果 Refresh Token 過期，您必須提示使用者重新登錄以生成新的 Access Token |

## client_secret 產生方式（PKCE + Public Client）

使用 PKCE 且於 digiRunner 的 OAuth Grant Type 欄位勾選 **Public Client (With PKCE)** 時，無需輸入 Client 密碼：

```
公式：Base64Encode(ClientID + ":")

步驟：
  1. 將 Client ID 加上 ":"，無需 Client Password
  2. 範例：
     Client ID: tspclient
     Client Password: ""（空字串）
     Base64Encode("tspclient:") = dHNwY2xpZW50Og==
```

> 此公式與 `digirunner-oidc-token-exchange` 中的 client_secret 產生方式相同。

## 成功回應格式

重新整理成功，回傳新的 Access Token：

```json
{
    "access_token": "eyJ0eXAi...",
    "expires_in": 86399,
    "jti": "41fa8a7b-b21d-4598-b254-5ffbed8b619f",
    "node": "executor1",
    "org_id": "100000",
    "refresh_token": "eyJ0eXAi...",
    "scope": "2000000006",
    "stime": 1684742522981,
    "token_type": "bearer"
}
```

## 錯誤回應格式

如 Refresh Token 已過期，回傳 401 Unauthorized：

```json
{
    "error": "invalid_token",
    "error_description": "Invalid refresh token (expired): eyJ0eXAi..."
}
```

> ⚠️ 當 Refresh Token 過期時，必須提示使用者重新登錄以生成新的 Access Token。

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
 * 使用 Refresh Token 換取新的 Access Token
 */
async function refreshAccessToken(refreshToken: string): Promise<any> {
  const clientSecret = btoa(`${CLIENT_ID}:`);

  const fetchOptions: RequestInit = {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      Authorization: `Basic ${clientSecret}`,
    },
    body: new URLSearchParams({
      grant_type: "refresh_token",
      refresh_token: refreshToken,
    }),
  };

  // 開發環境：跳過自簽署憑證驗證（僅 Node.js 環境）
  if (!SSL_VERIFY && typeof process !== "undefined") {
    (fetchOptions as any).agent = new https.Agent({ rejectUnauthorized: false });
  }

  const response = await fetch(
    `https://${DIGIRUNNER_DOMAIN}/oauth/token`,
    fetchOptions
  );

  if (!response.ok) {
    const error = await response.json();
    if (error.error === "invalid_token") {
      throw new Error("Refresh Token 已過期，請重新登入");
    }
    throw new Error(`Token 刷新失敗: ${response.status}`);
  }

  return response.json();
}

// 使用範例：Access Token 過期時刷新
const tokens = await refreshAccessToken(currentRefreshToken);
const newAccessToken = tokens.access_token;
const newRefreshToken = tokens.refresh_token;
```

### Python

```python
import requests
import base64
import os

DIGIRUNNER_DOMAIN = os.environ["DIGIRUNNER_DOMAIN"]
CLIENT_ID = os.environ["CLIENT_ID"]
SSL_VERIFY = os.environ.get("DIGIRUNNER_SSL_VERIFY", "true").lower() == "true"

def refresh_access_token(refresh_token: str) -> dict:
    """使用 Refresh Token 換取新的 Access Token"""
    # 產生 client_secret（PKCE Public Client，無密碼）
    client_secret = base64.b64encode(f"{CLIENT_ID}:".encode()).decode()

    response = requests.post(
        f"https://{DIGIRUNNER_DOMAIN}/oauth/token",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {client_secret}",
        },
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        verify=SSL_VERIFY,  # 開發環境 False 跳過自簽署憑證驗證
    )

    if response.status_code == 401:
        error = response.json()
        if error.get("error") == "invalid_token":
            raise Exception("Refresh Token 已過期，請重新登入")

    response.raise_for_status()
    return response.json()

# 使用範例
tokens = refresh_access_token(current_refresh_token)
new_access_token = tokens["access_token"]
new_refresh_token = tokens["refresh_token"]
```

### Java (Spring Boot)

```java
String digiRunnerDomain = System.getenv("DIGIRUNNER_DOMAIN");
String clientId = System.getenv("CLIENT_ID");

// 產生 client_secret（PKCE Public Client，無密碼）
String clientSecret = Base64.getEncoder().encodeToString(
    (clientId + ":").getBytes());

HttpHeaders headers = new HttpHeaders();
headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);
headers.set("Authorization", "Basic " + clientSecret);

MultiValueMap<String, String> body = new LinkedMultiValueMap<>();
body.add("grant_type", "refresh_token");
body.add("refresh_token", refreshToken);

try {
    ResponseEntity<Map> response = restTemplate.postForEntity(
        "https://" + digiRunnerDomain + "/oauth/token",
        new HttpEntity<>(body, headers), Map.class);
    Map tokens = response.getBody();
    String newAccessToken = (String) tokens.get("access_token");
    String newRefreshToken = (String) tokens.get("refresh_token");
} catch (HttpClientErrorException.Unauthorized e) {
    // Refresh Token 已過期，需重新登入
    throw new RuntimeException("Refresh Token 已過期，請重新登入");
}
```

### cURL

```bash
curl -v -X POST 'https://{digiRunner_DOMAIN}/oauth/token' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -H 'Authorization: Basic {client_secret}' \
  -d 'grant_type=refresh_token' \
  -d 'refresh_token={refresh_token}' \
  -k   # 開發環境：跳過自簽署憑證驗證（生產環境移除 -k）
```

## 注意事項

- `grant_type` 固定為 `refresh_token`，不可更改
- `client_secret` 產生公式與 Token Exchange 相同：`Base64Encode(ClientID + ":")`
- Refresh Token 過期後必須引導使用者重新登入，無法透過此 API 更新
- 建議在 Access Token 過期前主動刷新，避免使用者體驗中斷
- 刷新成功後，應同時更新儲存的 Access Token 和 Refresh Token
