---
name: digirunner-oidc-auth-request
description: >
  產生 OIDC 授權請求 (Authorization Request) 程式碼，支援 PKCE 機制。
  用於需要建構 digiRunner 授權 URL、產生 state / code_verifier / code_challenge 的場景。
  觸發時機：使用者提到「授權請求」、「authorization request」、「OIDC 登入」、「PKCE」、
  「產生授權 URL」、「redirect 到授權頁」等關鍵字。
---

# OIDC 授權請求 (Authorization Request)

## Overview

產生 digiRunner OIDC 授權碼流程的第一步：建構授權 URL 並將使用者重新導向至授權端點，支援 PKCE 機制。

## 授權端點

```
GET https://{digiRunner_DOMAIN}/dgrv4/ssotoken/gtwidp/JDBC/authorization
```

## 必要參數

| 參數 | 類型 | 必要性 | 描述 |
|------|------|--------|------|
| response_type | String | Required | 固定值 `code` |
| client_id | String | Required | 於 digiRunner 註冊的 Client ID |
| scope | String | Required | OIDC 存取範圍，多個以 URL 編碼空白字符 `%20` 分隔 |
| redirect_uri | String | Required | Client 於 digiRunner 註冊的 Redirect URL (callback)，格式：`https://{DIGIRUNNER_DOMAIN}/website/{websiteName}/callback` |
| state | String | Required | 隨機碼，防止 CSRF 攻擊，每個登錄會話生成一個隨機值（例如 UUID） |

## PKCE 參數（選用）

| 參數 | 類型 | 必要性 | 描述 |
|------|------|--------|------|
| code_challenge | String | Optional | `Base64URL(SHA256(code_verifier))`，code_verifier 為 43~128 隨機字串 |
| code_challenge_method | String | Optional | 固定值 `S256` |

## 程式碼產生指引

根據使用者指定的語言產生對應程式碼。執行 `scripts/generate_auth_request.py` 可快速產生範例。

> ⚠️ `DIGIRUNNER_DOMAIN`、`CLIENT_ID`、`MODULE_NAME` 因環境而異，必須從前端環境變數讀取，不可寫死。
> 詳見 `digirunner-oidc-flow-guide` 的 Phase 3 說明。

> ⚠️ digiRunner 的 Protocol **必須**為 `https://`，禁止使用 `http://`。

### Python

```python
import hashlib, base64, secrets, uuid, os
from urllib.parse import urlencode

# 從環境變數讀取（不可寫死）
DIGIRUNNER_DOMAIN = os.environ["DIGIRUNNER_DOMAIN"]
CLIENT_ID = os.environ["CLIENT_ID"]
REDIRECT_URI = os.environ.get("REDIRECT_URI", "https://{DIGIRUNNER_DOMAIN}/website/{websiteName}/callback")
SCOPE = "openid profile email"

# 產生 state（防 CSRF）
state = str(uuid.uuid4())

# 產生 PKCE code_verifier 與 code_challenge
code_verifier = secrets.token_urlsafe(64)[:128]
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode("ascii")).digest()
).rstrip(b"=").decode("ascii")

params = {
    "response_type": "code",
    "client_id": CLIENT_ID,
    "scope": SCOPE,
    "redirect_uri": REDIRECT_URI,
    "state": state,
    "code_challenge": code_challenge,
    "code_challenge_method": "S256",
}
auth_url = "https://{DIGIRUNNER_DOMAIN}/dgrv4/ssotoken/gtwidp/JDBC/authorization?{urlencode(params)}"
# 將 state 和 code_verifier 存入 session
```

### Node.js / TypeScript

```typescript
import crypto from "crypto";
import { v4 as uuidv4 } from "uuid";

// 從環境變數讀取（前端框架使用對應前綴，如 VITE_、NEXT_PUBLIC_）
const DIGIRUNNER_DOMAIN = import.meta.env.VITE_DIGIRUNNER_DOMAIN; // Vite 範例
const CLIENT_ID = import.meta.env.VITE_CLIENT_ID;
const REDIRECT_URI = import.meta.env.VITE_REDIRECT_URI ?? "https://{DIGIRUNNER_DOMAIN}/website/{websiteName}/callback";

const state = uuidv4();
const codeVerifier = crypto.randomBytes(64).toString("base64url").slice(0, 128);
const codeChallenge = crypto.createHash("sha256").update(codeVerifier).digest("base64url");

const params = new URLSearchParams({
  response_type: "code",
  client_id: CLIENT_ID,
  scope: "openid profile email",
  redirect_uri: REDIRECT_URI,
  state,
  code_challenge: codeChallenge,
  code_challenge_method: "S256",
});
const authUrl = `https://${DIGIRUNNER_DOMAIN}/dgrv4/ssotoken/gtwidp/JDBC/authorization?${params}`;
```

### Java

```java
// 從環境變數或設定檔讀取
String digiRunnerDomain = System.getenv("DIGIRUNNER_DOMAIN");
String clientId = System.getenv("CLIENT_ID");

String state = UUID.randomUUID().toString();
SecureRandom sr = new SecureRandom();
byte[] bytes = new byte[64];
sr.nextBytes(bytes);
String codeVerifier = Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
byte[] digest = MessageDigest.getInstance("SHA-256").digest(codeVerifier.getBytes(StandardCharsets.US_ASCII));
String codeChallenge = Base64.getUrlEncoder().withoutPadding().encodeToString(digest);

String authUrl = String.format(
    "https://%s/dgrv4/ssotoken/gtwidp/JDBC/authorization?response_type=code&client_id=%s&scope=%s&redirect_uri=%s&state=%s&code_challenge=%s&code_challenge_method=S256",
    digiRunnerDomain, clientId,
    URLEncoder.encode(scope, StandardCharsets.UTF_8),
    URLEncoder.encode(redirectUri, StandardCharsets.UTF_8),
    state, codeChallenge);
```

## API 建立注意事項

若授權請求端點需要透過 digiRunner 註冊為 API：

- 使用 `digirunner-api-setup` skill 建立 API，`noOAuth` 必須設為 `"Y"`（公開端點，不需 OAuth 驗證）
- 此 API 為公開端點，前端直接使用一般 HTTP Client 呼叫即可，**不需要**使用 `digiRunner-oidc-api-call` skill

## 注意事項

- `state` 和 `code_verifier` 必須存入 Server-side Session，後續步驟需要驗證
- `scope` 中多個值以空白分隔，URL 中需以 `%20` 編碼
- PKCE 為可選機制，但強烈建議啟用以提升安全性
- 詳細 API 規格請參閱 [references/api-spec.md](references/api-spec.md)
