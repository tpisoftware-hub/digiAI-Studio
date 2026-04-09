---
name: digirunner-oidc-token-exchange
description: >
  用授權碼 (Authorization Code) 換取 Access Token / Refresh Token / ID Token。
  產生向 digiRunner Token 端點發送 POST 請求的程式碼，支援 PKCE (Public Client) 模式。
  觸發時機：使用者提到「換取 Token」、「token exchange」、「取得 access token」、
  「refresh token」、「id token」、「client_secret」、「token endpoint」等關鍵字。
---

# OIDC Token 交換 (Token Exchange)

## Overview

用授權碼向 digiRunner Token 端點換取 Access Token、Refresh Token 和 ID Token，採用 PKCE (Public Client) 認證模式，無需 Client 密碼。

## Token 端點

```
POST https://{digiRunner_DOMAIN}/oauth/token
Content-Type: application/x-www-form-urlencoded
Authorization: Basic {client_secret}
```

## 請求參數

| 參數 | 類型 | 必要性 | 描述 |
|------|------|--------|------|
| client_secret | String | Required | 見下方產生方式 |
| grant_type | String | Required | 固定值 `authorization_code` |
| code | String | Required | 授權碼，唯一值，每次都會變動 |
| redirect_uri | String | Required | Client 於 digiRunner 註冊的 Redirect URL (callback)，格式：`https://{DIGIRUNNER_DOMAIN}/website/{websiteName}/callback` |
| code_verifier | String | Required | 前一次授權請求產生的 code_verifier |

## client_secret 產生方式（PKCE + Public Client）

使用 PKCE 且於 digiRunner 的 OAuth Grant Type 欄位勾選 Public Client (With PKCE) 時，無需輸入 Client 密碼。

```
公式：Base64Encode(ClientID + ":" + Base64Encode(""))

範例：
  Client ID: tspclient
  結果: dHNwY2xpZW50Og==
```

## 回應格式

```json
{
  "access_token": "eyJ0eXAi...",
  "expires_in": 1799,
  "jti": "me6f1f7...",
  "node": "executor1",
  "refresh_token": "eyJ0eXAi...",
  "scope": "openid email profile 2000000086 2000000088",
  "stime": 1684812470001,
  "token_type": "Bearer",
  "idp_type": "JDBC",
  "id_token": "eyJraWQi..."
}
```

### 回應欄位說明

| 參數 | 類型 | 描述 |
|------|------|------|
| access_token | String | Access Token (JWT) |
| expires_in | Number | Access Token 過期之前的時間量（以秒為單位） |
| jti | String | Access Token ID |
| node | Number | 租容 digiRunner v3 版本之識別資料 |
| refresh_token | String | Refresh Token (JWT)，用於獲取新的 Access Token |
| scope | String | User 授予的權限 |
| stime | Number | Access Token 最開始核發時間（以毫秒為單位） |
| token_type | String | Bearer |
| idp_type | String | JDBC |
| id_token | String | ID Token (JWT)，當 scope 內有指定 openid 或 email 或 profile 時才回傳 |

## 程式碼產生指引

> ⚠️ `DIGIRUNNER_DOMAIN`、`CLIENT_ID`、`MODULE_NAME` 因環境而異，必須從前端環境變數讀取，不可寫死。
> 詳見 `digirunner-oidc-flow-guide` 的 Phase 3 說明。

> ⚠️ digiRunner 的 Protocol **必須**為 `https://`，禁止使用 `http://`。

> ⚠️ 開發環境使用自簽署憑證時，需根據 `DIGIRUNNER_SSL_VERIFY` 環境變數決定是否跳過 SSL 驗證。

### Python

```python
import requests
import base64
import os

# 從環境變數讀取（不可寫死）
DIGIRUNNER_DOMAIN = os.environ["DIGIRUNNER_DOMAIN"]
CLIENT_ID = os.environ["CLIENT_ID"]
REDIRECT_URI = os.environ.get("REDIRECT_URI", "https://{DIGIRUNNER_DOMAIN}/website/{websiteName}/callback")
SSL_VERIFY = os.environ.get("DIGIRUNNER_SSL_VERIFY", "true").lower() == "true"

# 產生 client_secret（PKCE Public Client，無密碼）
client_secret = base64.b64encode(f"{CLIENT_ID}:".encode()).decode()

# 發送 Token 請求
response = requests.post(
    f"https://{DIGIRUNNER_DOMAIN}/oauth/token",
    headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {client_secret}",
    },
    data={
        "grant_type": "authorization_code",
        "code": authorization_code,     # 從 callback 取得的授權碼
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier,  # 授權請求時產生的 code_verifier
    },
    verify=SSL_VERIFY,  # 開發環境 False 跳過自簽署憑證驗證
)
tokens = response.json()
access_token = tokens["access_token"]
refresh_token = tokens["refresh_token"]
id_token = tokens["id_token"]
```

### Node.js / TypeScript

```typescript
import https from "https";

// 從環境變數讀取（前端框架使用對應前綴，如 VITE_、NEXT_PUBLIC_）
const DIGIRUNNER_DOMAIN = import.meta.env.VITE_DIGIRUNNER_DOMAIN; // Vite 範例
const CLIENT_ID = import.meta.env.VITE_CLIENT_ID;
const REDIRECT_URI = import.meta.env.VITE_REDIRECT_URI ?? "https://{DIGIRUNNER_DOMAIN}/website/{websiteName}/callback";
const SSL_VERIFY = import.meta.env.VITE_DIGIRUNNER_SSL_VERIFY !== "false";

// 產生 client_secret（PKCE Public Client，無密碼）
const clientSecret = btoa(`${CLIENT_ID}:`);

const fetchOptions: RequestInit = {
  method: "POST",
  headers: {
    "Content-Type": "application/x-www-form-urlencoded",
    Authorization: `Basic ${clientSecret}`,
  },
  body: new URLSearchParams({
    grant_type: "authorization_code",
    code: authorizationCode,
    redirect_uri: REDIRECT_URI,
    code_verifier: codeVerifier,
  }),
};

// 開發環境：跳過自簽署憑證驗證（僅 Node.js 環境）
if (!SSL_VERIFY && typeof process !== "undefined") {
  (fetchOptions as any).agent = new https.Agent({ rejectUnauthorized: false });
}

const response = await fetch(`https://${DIGIRUNNER_DOMAIN}/oauth/token`, fetchOptions);
const tokens = await response.json();
```

### Java (Spring Boot)

```java
// 從環境變數或設定檔讀取
String digiRunnerDomain = System.getenv("DIGIRUNNER_DOMAIN");
String clientId = System.getenv("CLIENT_ID");

// 產生 client_secret（PKCE Public Client，無密碼）
String clientSecret = Base64.getEncoder().encodeToString(
    (clientId + ":").getBytes());

HttpHeaders headers = new HttpHeaders();
headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);
headers.set("Authorization", "Basic " + clientSecret);

MultiValueMap<String, String> body = new LinkedMultiValueMap<>();
body.add("grant_type", "authorization_code");
body.add("code", authorizationCode);
body.add("redirect_uri", redirectUri);
body.add("code_verifier", codeVerifier);

ResponseEntity<Map> response = restTemplate.postForEntity(
    "https://" + digiRunnerDomain + "/oauth/token",
    new HttpEntity<>(body, headers), Map.class);
```

### cURL

```bash
curl -v -X POST "https://{digiRunner_DOMAIN}/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic {client_secret}" \
  -d "grant_type=authorization_code" \
  -d "code={code}" \
  -d "redirect_uri=https://{DIGIRUNNER_DOMAIN}/website/{websiteName}/callback" \
  -d "code_verifier={code_verifier}" \
  -k   # 開發環境：跳過自簽署憑證驗證（生產環境移除 -k）
```

## 注意事項

- 授權碼只能使用一次，10 分鐘內過期
- client_secret 公式為 `Base64Encode(ClientID + ":" + Base64Encode(""))`，即 `Base64Encode(ClientID + ":")`
- 必須帶入 code_verifier（授權請求時產生的值）
- 詳細規格請參閱 [references/token-spec.md](references/token-spec.md)
