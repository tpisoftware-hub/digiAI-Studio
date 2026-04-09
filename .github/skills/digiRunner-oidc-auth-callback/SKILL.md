---
name: digirunner-oidc-auth-callback
description: >
  處理 OIDC 授權回應 (Authorization Callback)，解析授權碼或錯誤回應。
  用於實作 Redirect URI callback endpoint、解析授權碼 (code)、驗證 state、處理錯誤碼。
  觸發時機：使用者提到「callback」、「授權回應」、「授權碼」、「authorization code」、
  「redirect_uri 處理」、「錯誤回應處理」等關鍵字。
---

# OIDC 授權回應處理 (Authorization Callback)

## Overview

處理 digiRunner OIDC 授權碼流程的第二步：在 Redirect URI (callback) 接收並解析授權碼或錯誤回應。

## 成功回應格式

使用者通過身份驗證並完成授權後，瀏覽器會被重定向至 Redirect URL：

```
https://{DIGIRUNNER_DOMAIN}/website/{websiteName}/callback?code={code}&state={state}
```

| 參數 | 類型 | 描述 |
|------|------|------|
| code | String | 用於獲取 Token 的授權代碼，10 分鐘有效，只能使用一次 |
| state | String | 必須與發送授權請求時的 state 值相同，需驗證一致性 |

## 錯誤回應格式

使用者拒絕授權時，瀏覽器會被重定向至：

```
https://{DIGIRUNNER_DOMAIN}/website/{websiteName}/callback?rtn_code={rtn_code}&msg={msg}
```

| 參數 | 類型 | 描述 |
|------|------|------|
| rtn_code | String | 錯誤碼 |
| msg | String | Base64URL 編碼的錯誤訊息，需 Decode 取得原文 |

### 錯誤碼對照表

| 錯誤碼 | 描述 | User 動作 |
|--------|------|-----------|
| error | 不允許應用程式要求授權碼 | User 帳號或密碼錯誤或其他錯誤 |
| cancel | 資源擁有者拒絕同意 | User 在同意畫面按下取消 |

## 程式碼產生指引

### Python (Flask)

```python
from flask import Flask, request, session, redirect
import base64

app = Flask(__name__)

@app.route("/callback")
def callback():
    # 檢查是否為錯誤回應
    rtn_code = request.args.get("rtn_code")
    if rtn_code:
        msg_encoded = request.args.get("msg", "")
        # Base64URL Decode 錯誤訊息
        msg = base64.urlsafe_b64decode(msg_encoded + "==").decode("utf-8")
        return {"error": rtn_code, "message": msg}, 400

    # 取得授權碼
    code = request.args.get("code")
    state = request.args.get("state")

    if not code or not state:
        return {"error": "missing_params"}, 400

    # 驗證 state 是否與 session 中儲存的一致（防 CSRF）
    if state != session.get("oauth_state"):
        return {"error": "invalid_state"}, 403

    # 授權碼取得成功，進入下一步：用 code 換取 Token
    return {"code": code, "state": state}
```

### Node.js (Express)

```typescript
import express from "express";

const app = express();

app.get("/callback", (req, res) => {
  const { code, state, rtn_code, msg } = req.query;

  // 檢查錯誤回應
  if (rtn_code) {
    const decodedMsg = Buffer.from(msg as string, "base64url").toString("utf-8");
    return res.status(400).json({ error: rtn_code, message: decodedMsg });
  }

  if (!code || !state) {
    return res.status(400).json({ error: "missing_params" });
  }

  // 驗證 state（防 CSRF）
  if (state !== req.session?.oauthState) {
    return res.status(403).json({ error: "invalid_state" });
  }

  // 授權碼取得成功
  res.json({ code, state });
});
```

### Java (Spring Boot)

```java
@GetMapping("/callback")
public ResponseEntity<?> callback(
    @RequestParam(required = false) String code,
    @RequestParam(required = false) String state,
    @RequestParam(name = "rtn_code", required = false) String rtnCode,
    @RequestParam(required = false) String msg,
    HttpSession session) {

    // 檢查錯誤回應
    if (rtnCode != null) {
        String decodedMsg = new String(Base64.getUrlDecoder().decode(msg), StandardCharsets.UTF_8);
        return ResponseEntity.badRequest().body(Map.of("error", rtnCode, "message", decodedMsg));
    }

    // 驗證 state
    String savedState = (String) session.getAttribute("oauth_state");
    if (!state.equals(savedState)) {
        return ResponseEntity.status(403).body(Map.of("error", "invalid_state"));
    }

    // 授權碼取得成功，進入 Token Exchange
    return ResponseEntity.ok(Map.of("code", code));
}
```

## API 建立注意事項

若 Callback 端點需要透過 digiRunner 註冊為 API：

- 使用 `digirunner-api-setup` skill 建立 API，`noOAuth` 必須設為 `"Y"`（公開端點，不需 OAuth 驗證）
- 此 API 為公開端點，前端直接使用一般 HTTP Client 呼叫即可，**不需要**使用 `digiRunner-oidc-api-call` skill

## 注意事項

- 授權碼 (code) 有效期僅 10 分鐘，且只能使用一次
- 必須驗證 state 值一致性以防止 CSRF 攻擊
- 錯誤訊息 (msg) 為 Base64URL 編碼，需 Decode 才能閱讀
- 詳細錯誤碼規格請參閱 [references/error-codes.md](references/error-codes.md)
