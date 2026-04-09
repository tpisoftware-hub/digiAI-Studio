---
name: digirunner-oidc-api-call
description: >
  以 ID Token 和 Access Token 呼叫註冊於 digiRunner 的 API。
  產生帶有 ID-Token Header 和 Bearer Authorization 的 API 請求程式碼。
  觸發時機：使用者提到「呼叫 API」、「call API」、「digiRunner API」、「ID-Token header」、
  「Bearer token」、「API 請求」、「存取 digiRunner 資源」等關鍵字。
---

# 以 Token 呼叫 digiRunner API

## Overview

使用 ID Token 和 Access Token 呼叫註冊於 digiRunner 的 API，需在 HTTP Header 中同時帶入兩種 Token。

## ⚠️ 重要架構原則

```
┌──────────┐     ┌─────────────┐     ┌──────────┐
│  前端    │ ──► │ digiRunner  │ ──► │  後端    │
│ Frontend │     │ API Gateway │     │ Backend  │
└──────────┘     └─────────────┘     └──────────┘
```

**前端絕對不能直接呼叫後端 API！** 所有請求必須經過 digiRunner API Gateway。

**前端 Asset 路徑規則**（產生程式碼時必須遵守）：
- ✗ 錯誤：`/css`、`/js`、`/images`、`/config.js`
- ✗ 錯誤：`/{websiteName}/css`、`/{websiteName}/js`（缺少 `/website/` 前綴）
- ✓ 正確：`/website/{websiteName}/css`、`/website/{websiteName}/js`、`/website/{websiteName}/images`、`/website/{websiteName}/config.js`

> 前端透過反向代理部署於 `https://digirunner-domain/website/{websiteName}/`，所有靜態資源的絕對路徑必須包含 `/website/{websiteName}/` 前綴。

**程式碼產生時的路徑範例**：

```html
<!-- ✗ 錯誤：路徑缺少 /website/{websiteName}/ 前綴 -->
<link rel="stylesheet" href="/css/style.css">
<script src="/js/app.js"></script>
<script src="/config.js"></script>

<!-- ✗ 錯誤：路徑缺少 /website/ 前綴 -->
<link rel="stylesheet" href="/{websiteName}/css/style.css">

<!-- ✓ 正確：路徑包含 /website/{websiteName}/ 前綴 -->
<link rel="stylesheet" href="/website/{websiteName}/css/style.css">
<script src="/website/{websiteName}/js/app.js"></script>
<script src="/website/{websiteName}/config.js"></script>
```

```javascript
// Vite 設定（vite.config.ts）— 必須設定 base 為 /website/{websiteName}/
export default defineConfig({
  base: '/website/{websiteName}/',  // ← 所有 Asset 路徑自動加上此前綴
});
```

> ⚠️ 產生的所有前端程式碼中，靜態資源（CSS/JS/圖片/字型/config）的路徑**必須**包含 `/website/{websiteName}/` 前綴，否則透過 digiRunner 反向代理時將無法載入資源。

## Header 轉換機制

digiRunner APIM 會將前端傳入的 Header 轉換後傳給後端：

```
┌─────────────────────────────────┐
│ 前端傳送                         │
├─────────────────────────────────┤
│ ID-Token: {jwt}                 │
│ Authorization: Bearer {token}   │
└─────────────────────────────────┘
                │
                ▼ digiRunner 轉換
┌─────────────────────────────────┐
│ 後端收到                         │
├─────────────────────────────────┤
│ Authorization: {jwt}            │  ← ID-Token 的值
└─────────────────────────────────┘
```

**後端解碼方式**：從 `Authorization` Header 取出 JWT（原本的 ID-Token），解碼後可取得 `sub`、`name`、`email` 等 claims。

## API 端點格式

```
{METHOD} https://{DIGIRUNNER_DOMAIN}/{apiId}
```

- `DIGIRUNNER_DOMAIN`：digiRunner 伺服器網域
- `apiId`：API 註冊時的 API ID

> ⚠️ 前端 URL 只需 `/{apiId}`，不包含 `moduleName`。`moduleName` 僅用於 digiRunner 內部 API 設定（createApi / enableApi / associateApiGroup）。

## 請求 Header

| 參數 | 類型 | 必要性 | 描述 |
|------|------|--------|------|
| ID-Token | String | Required | ID Token (JWT) |
| Authorization | String | Required | `Bearer {access_token}` |

## 程式碼產生指引

> ⚠️ `DIGIRUNNER_DOMAIN`、`CLIENT_ID`、`MODULE_NAME` 因環境而異，必須從前端環境變數讀取，不可寫死。
> 詳見 `digirunner-oidc-flow-guide` 的 Phase 3 說明。

> ⚠️ digiRunner 的 Protocol **必須**為 `https://`，禁止使用 `http://`。

> ⚠️ 開發環境使用自簽署憑證時，需根據 `DIGIRUNNER_SSL_VERIFY` 環境變數決定是否跳過 SSL 驗證。

### ★ 推薦：使用 Axios Instance + 攔截器（集中管理 Headers）

使用 Axios 攔截器（Interceptor）集中管理 `ID-Token` 和 `Authorization` headers，避免在每個 API 呼叫中重複撰寫。

```typescript
// digiRunnerClient.ts — 建立一次，全專案共用
import axios from "axios";
import https from "https";

const DIGIRUNNER_DOMAIN = import.meta.env.VITE_DIGIRUNNER_DOMAIN;
const SSL_VERIFY = import.meta.env.VITE_DIGIRUNNER_SSL_VERIFY !== "false";

/**
 * digiRunner API Client（Axios Instance）
 * 透過 Request Interceptor 自動帶入 ID-Token 和 Authorization headers
 */
const digiRunnerClient = axios.create({
  baseURL: `https://${DIGIRUNNER_DOMAIN}`,
  headers: { "Content-Type": "application/json" },
  // 開發環境：跳過自簽署憑證驗證（僅 Node.js / SSR 環境）
  ...(typeof process !== "undefined" && !SSL_VERIFY
    ? { httpsAgent: new https.Agent({ rejectUnauthorized: false }) }
    : {}),
});

// ── Request Interceptor：自動帶入 Token Headers ──
digiRunnerClient.interceptors.request.use((config) => {
  // 從 Token 儲存位置讀取（localStorage / sessionStorage / store）
  const idToken = localStorage.getItem("id_token");
  const accessToken = localStorage.getItem("access_token");

  if (idToken) config.headers["ID-Token"] = idToken;
  if (accessToken) config.headers["Authorization"] = `Bearer ${accessToken}`;

  return config;
});

// ── Response Interceptor：處理 401 自動刷新 Token ──
digiRunnerClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // 401 且尚未重試 → 嘗試用 Refresh Token 換取新 Token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // 使用 digiRunner-oidc-token-refresh skill 的邏輯
        const refreshToken = localStorage.getItem("refresh_token");
        const CLIENT_ID = import.meta.env.VITE_CLIENT_ID;
        const clientSecret = btoa(`${CLIENT_ID}:`);

        const { data: tokens } = await axios.post(
          `https://${DIGIRUNNER_DOMAIN}/oauth/token`,
          new URLSearchParams({
            grant_type: "refresh_token",
            refresh_token: refreshToken!,
          }),
          {
            headers: {
              "Content-Type": "application/x-www-form-urlencoded",
              Authorization: `Basic ${clientSecret}`,
            },
          }
        );

        // 更新儲存的 Token
        localStorage.setItem("access_token", tokens.access_token);
        localStorage.setItem("refresh_token", tokens.refresh_token);
        if (tokens.id_token) localStorage.setItem("id_token", tokens.id_token);

        // 用新 Token 重試原始請求
        return digiRunnerClient(originalRequest);
      } catch {
        // Refresh Token 也過期 → 導向重新登入
        window.location.href = "/login";
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  }
);

export default digiRunnerClient;
```

**使用方式**（所有 API 呼叫不再需要手動帶入 headers）：

```typescript
import digiRunnerClient from "./digiRunnerClient";

// ✓ 簡潔：自動帶入 ID-Token 和 Authorization headers
const { data: profile } = await digiRunnerClient.get("/get-user-profile");
const { data: orders } = await digiRunnerClient.post("/create-order", { items: [...] });
const { data: report } = await digiRunnerClient.get("/get-report", { params: { month: "2026-03" } });
```

### Python（推薦：使用 requests.Session 集中管理 Headers）

```python
import requests
import os

DIGIRUNNER_DOMAIN = os.environ["DIGIRUNNER_DOMAIN"]
SSL_VERIFY = os.environ.get("DIGIRUNNER_SSL_VERIFY", "true").lower() == "true"

# 建立 Session（集中管理 headers，類似 Axios Instance）
session = requests.Session()
session.verify = SSL_VERIFY  # 開發環境 False 跳過自簽署憑證驗證
session.headers.update({
    "ID-Token": id_token,
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
})

# ✓ 簡潔：所有呼叫自動帶入 headers
profile = session.get(f"https://{DIGIRUNNER_DOMAIN}/get-user-profile").json()
orders = session.post(f"https://{DIGIRUNNER_DOMAIN}/create-order", json={"items": [...]}).json()
```

### Java (Spring Boot)（推薦：使用 RestTemplate Interceptor 集中管理 Headers）

```java
// DigiRunnerClientConfig.java — 設定一次，全專案共用
@Configuration
public class DigiRunnerClientConfig {

    @Value("${DIGIRUNNER_DOMAIN}")
    private String digiRunnerDomain;

    @Bean
    public RestTemplate digiRunnerRestTemplate() {
        RestTemplate restTemplate = new RestTemplate();

        // 集中管理 Headers（類似 Axios Request Interceptor）
        restTemplate.setInterceptors(List.of((request, body, execution) -> {
            HttpHeaders headers = request.getHeaders();
            // 從 Token 儲存位置讀取
            String idToken = TokenStore.getIdToken();
            String accessToken = TokenStore.getAccessToken();
            if (idToken != null) headers.set("ID-Token", idToken);
            if (accessToken != null) headers.setBearerAuth(accessToken);
            headers.setContentType(MediaType.APPLICATION_JSON);
            return execution.execute(request, body);
        }));

        return restTemplate;
    }
}

// 使用方式：自動帶入 headers
String url = String.format("https://%s/%s", digiRunnerDomain, apiId);
ResponseEntity<String> response = digiRunnerRestTemplate.getForEntity(url, String.class);
```

### 基本用法：JavaScript / TypeScript（不使用 Axios）

```typescript
const DIGIRUNNER_DOMAIN = import.meta.env.VITE_DIGIRUNNER_DOMAIN;
const API_ID = "get-user-profile";

const response = await fetch(
  `https://${DIGIRUNNER_DOMAIN}/${API_ID}`,
  {
    method: "GET",
    headers: {
      "ID-Token": idToken,
      "Authorization": `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
  }
);
const result = await response.json();
```

### cURL

```bash
# ✓ 正確：呼叫 digiRunner API Gateway（URL 只用 apiId）
curl -X GET 'https://{DIGIRUNNER_DOMAIN}/{apiId}' \
  -H 'ID-Token: {id_token}' \
  -H 'Authorization: Bearer {access_token}' \
  -H 'Content-Type: application/json' \
  -k   # 開發環境：跳過自簽署憑證驗證（生產環境移除 -k）

# ✗ 錯誤：直接呼叫後端
# curl -X GET 'http://backend:8080/api/v1/users/profile'
```

## 注意事項

- **前端必須透過 digiRunner 呼叫 API**，不可直接呼叫後端
- 需同時帶入 `ID-Token` 和 `Authorization` 兩個 Header
- Authorization 格式為 `Bearer {access_token}`
- API 路徑格式：`/{apiId}`（不含 moduleName）
- **推薦使用 Axios Instance + 攔截器集中管理 headers**，避免每次 API 呼叫重複撰寫
- Access Token 過期後使用 `digiRunner-oidc-token-refresh` skill 的 Refresh Token 換取新 Token
- 當 Refresh Token 也過期時，需引導使用者重新登入
- 登出時使用 `digiRunner-oidc-token-revocation` skill 撤銷 Token

## 後端解碼範例

後端從 `Authorization` Header 取出 JWT 並解碼：

### Java (Spring Boot)

```java
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;

// 從 Header 取得 JWT（digiRunner 已將 ID-Token 放入 Authorization）
String jwt = request.getHeader("Authorization");

// 解碼 JWT 取得使用者資訊
Claims claims = Jwts.parserBuilder()
    .setSigningKey(publicKey)  // 使用 digiRunner 公鑰驗證
    .build()
    .parseClaimsJws(jwt)
    .getBody();

String userId = claims.getSubject();           // sub
String userName = claims.get("name", String.class);
String email = claims.get("email", String.class);
```

### Node.js / TypeScript

```typescript
import jwt from 'jsonwebtoken';

// 從 Header 取得 JWT
const token = req.headers['authorization'];

// 解碼 JWT 取得使用者資訊
const decoded = jwt.verify(token, publicKey) as {
  sub: string;
  name: string;
  email: string;
};

const userId = decoded.sub;
const userName = decoded.name;
const email = decoded.email;
```

### Python

```python
import jwt

# 從 Header 取得 JWT
token = request.headers.get("Authorization")

# 解碼 JWT 取得使用者資訊
decoded = jwt.decode(token, public_key, algorithms=["RS256"])

user_id = decoded["sub"]
user_name = decoded["name"]
email = decoded["email"]
```
