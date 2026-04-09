---
name: digirunner-oidc-token-verify
description: >
  驗證 ID Token 是否合法，透過呼叫 digiRunner 驗證 API 確認 Token 有效性並取得使用者資訊。
  觸發時機：使用者提到「驗證 token」、「verify token」、「ID Token 驗證」、「token 是否合法」、
  「取得使用者資訊」、「validate JWT」等關鍵字。
---

# 驗證 ID Token (Token Verification)

## Overview

透過呼叫 digiRunner 的驗證 API 確認 ID Token 是否合法，並獲取使用者的個人資料和電子郵件。

## 驗證端點

```
POST https://{digiRunner_DOMAIN}/dgrv4/ssotoken/gtwidp/verify
Content-Type: application/x-www-form-urlencoded
```

## 請求參數

| 參數 | 類型 | 必要性 | 描述 |
|------|------|--------|------|
| id_token | String | Required | 待驗證的 ID Token (JWT) |

## 程式碼產生指引

> ⚠️ `DIGIRUNNER_DOMAIN`、`CLIENT_ID`、`MODULE_NAME` 因環境而異，必須從前端環境變數讀取，不可寫死。
> 詳見 `digirunner-oidc-flow-guide` 的 Phase 3 說明。

> ⚠️ digiRunner 的 Protocol **必須**為 `https://`，禁止使用 `http://`。

> ⚠️ 開發環境使用自簽署憑證時，需根據 `DIGIRUNNER_SSL_VERIFY` 環境變數決定是否跳過 SSL 驗證。

### Python

```python
import requests
import os

# 從環境變數讀取（不可寫死）
DIGIRUNNER_DOMAIN = os.environ["DIGIRUNNER_DOMAIN"]
SSL_VERIFY = os.environ.get("DIGIRUNNER_SSL_VERIFY", "true").lower() == "true"

def verify_id_token(id_token: str) -> dict:
    """驗證 ID Token 並取得使用者資訊"""
    response = requests.post(
        f"https://{DIGIRUNNER_DOMAIN}/dgrv4/ssotoken/gtwidp/verify",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"id_token": id_token},
        verify=SSL_VERIFY,  # 開發環境 False 跳過自簽署憑證驗證
    )
    response.raise_for_status()
    return response.json()

# 使用範例
user_info = verify_id_token(id_token)
print(user_info)
```

### Node.js / TypeScript

```typescript
import https from "https";

// 從環境變數讀取（前端框架使用對應前綴，如 VITE_、NEXT_PUBLIC_）
const DIGIRUNNER_DOMAIN = import.meta.env.VITE_DIGIRUNNER_DOMAIN; // Vite 範例
const SSL_VERIFY = import.meta.env.VITE_DIGIRUNNER_SSL_VERIFY !== "false";

async function verifyIdToken(idToken: string): Promise<any> {
  const fetchOptions: RequestInit = {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ id_token: idToken }),
  };

  // 開發環境：跳過自簽署憑證驗證（僅 Node.js 環境）
  if (!SSL_VERIFY && typeof process !== "undefined") {
    (fetchOptions as any).agent = new https.Agent({ rejectUnauthorized: false });
  }

  const response = await fetch(
    `https://${DIGIRUNNER_DOMAIN}/dgrv4/ssotoken/gtwidp/verify`,
    fetchOptions
  );
  if (!response.ok) throw new Error(`Verify failed: ${response.status}`);
  return response.json();
}
```

### Java (Spring Boot)

```java
// 從環境變數或設定檔讀取
String digiRunnerDomain = System.getenv("DIGIRUNNER_DOMAIN");

public Map<String, Object> verifyIdToken(String idToken) {
    HttpHeaders headers = new HttpHeaders();
    headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);

    MultiValueMap<String, String> body = new LinkedMultiValueMap<>();
    body.add("id_token", idToken);

    ResponseEntity<Map> response = restTemplate.postForEntity(
        "https://" + digiRunnerDomain + "/dgrv4/ssotoken/gtwidp/verify",
        new HttpEntity<>(body, headers), Map.class);
    return response.getBody();
}
```

### cURL

```bash
curl -v -X POST 'https://{digiRunner_DOMAIN}/dgrv4/ssotoken/gtwidp/verify' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'id_token={id_token}' \
  -k   # 開發環境：跳過自簽署憑證驗證（生產環境移除 -k）
```

## 注意事項

- 此 API 用於 Server-side 驗證 ID Token 的合法性
- 回應中包含使用者的個人資料資訊和電子郵件
- 建議在每次收到 ID Token 時都進行驗證
- 也可以在 Client 端以 JWT Library 本地驗證簽章，但呼叫 API 為最可靠的方式
