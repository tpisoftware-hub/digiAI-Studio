# OIDC 授權請求 API 規格

## 端點

```
GET https://{digiRunner_DOMAIN}/dgrv4/ssotoken/gtwidp/JDBC/authorization
```

## 參數規格

### 必要參數

| 參數 | 類型 | 必要性 | 描述 | 範例 |
|------|------|--------|------|------|
| response_type | String | Required | 固定值 | `code` |
| client_id | String | Required | 於 digiRunner 註冊的 Client ID | `tspclient` |
| scope | String | Required | OIDC 存取範圍，多個以 `%20` 分隔 | `openid%20profile%20email` |
| redirect_uri | String | Required | 於 digiRunner 註冊的 Redirect URL | `https://{DIGIRUNNER_DOMAIN}/website/{websiteName}/callback` |
| state | String | Required | 隨機碼，防止 CSRF，建議使用 UUID | `550e8400-e29b-41d4-a716-446655440000` |

### PKCE 參數（選用）

| 參數 | 類型 | 必要性 | 描述 | 範例 |
|------|------|--------|------|------|
| code_challenge | String | Optional | Base64URL(SHA256(code_verifier)) | `Jhlf18b9aDFC5hkgQy3_MO1MznyS7kqMi32wELbhdos` |
| code_challenge_method | String | Optional | 固定值 | `S256` |

## PKCE 計算流程

1. 產生 `code_verifier`：43~128 字元的隨機字串
2. 計算 SHA256 雜湊：`SHA256(code_verifier)`
3. Base64URL 編碼（無 padding）：`Base64URLEncode(hash)`

### 範例

```
code_verifier:  B7gB0cY1C58ecNJ2J-231Ep-NmXgghAzgZg9nXu-vDo
code_challenge: Jhlf18b9aDFC5hkgQy3_MO1MznyS7kqMi32wELbhdos
```

## 完整 URL 範例

```
https://{digiRunner_DOMAIN}/dgrv4/ssotoken/gtwidp/JDBC/authorization?response_type=code&client_id={client_id}&scope=openid%20profile%20email&redirect_uri=https://{DIGIRUNNER_DOMAIN}/website/{websiteName}/callback&state={state}&code_challenge={code_challenge}&code_challenge_method=S256
```
