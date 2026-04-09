# Token 端點 API 規格

## 端點

```
POST https://{digiRunner_DOMAIN}/oauth/token
```

## 請求 Header

```
Content-Type: application/x-www-form-urlencoded
Authorization: Basic {client_secret}
```

## client_secret 產生公式（PKCE + Public Client）

使用 PKCE 且於 digiRunner 勾選 Public Client (With PKCE) 時，無需 Client 密碼。

```
Base64Encode(ClientID + ":" + Base64Encode(""))
```

即等同於：

```
Base64Encode(ClientID + ":")
```

範例：
- Client ID: `tspclient`
- Base64Encode("tspclient:") = `dHNwY2xpZW50Og==`

## 請求 Body 參數

| 參數 | 類型 | 必要性 | 描述 |
|------|------|--------|------|
| grant_type | String | Required | 固定值 `authorization_code` |
| code | String | Required | 授權碼，唯一值，每次都會變動 |
| redirect_uri | String | Required | Client 於 digiRunner 註冊的 Redirect URL |
| code_verifier | String | Required | PKCE code_verifier |

## 成功回應

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

## 回應欄位

| 參數 | 類型 | 描述 |
|------|------|------|
| access_token | String | Access Token (JWT) |
| expires_in | Number | Access Token 過期時間（秒） |
| jti | String | Access Token ID |
| node | Number | digiRunner v3 識別資料 |
| refresh_token | String | Refresh Token (JWT)，用於換取新 Access Token |
| scope | String | User 授予的權限 |
| stime | Number | Token 核發時間（毫秒） |
| token_type | String | `Bearer` |
| idp_type | String | `JDBC` |
| id_token | String | ID Token (JWT)，scope 含 openid/email/profile 時回傳 |
