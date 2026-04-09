# OIDC 授權回應錯誤碼規格

## 成功回應

callback URL: `https://{DIGIRUNNER_DOMAIN}/website/{websiteName}/callback?code={code}&state={state}`

| 參數 | 類型 | 描述 |
|------|------|------|
| code | String | 用於獲取訪問令牌的授權代碼，10 分鐘有效，只能使用一次 |
| state | String | 應與授權請求時的 state 值相同，必須驗證一致性 |

## 錯誤回應

callback URL: `https://{DIGIRUNNER_DOMAIN}/website/{websiteName}/callback?rtn_code={rtn_code}&msg={msg}`

| 參數 | 類型 | 描述 |
|------|------|------|
| rtn_code | String | 錯誤碼 |
| msg | String | Base64URL 編碼的錯誤訊息，TSP 須使用 Base64URL Decode 取得原文 |

## 錯誤碼對照表

| 錯誤碼 | 描述 | User 動作 |
|--------|------|-----------|
| error | 不允許應用程式要求授權碼 | User 帳號或密碼錯誤或其他錯誤 |
| cancel | 資源擁有者拒絕同意 | User 在同意畫面按下取消 |

## Base64URL Decode 範例

錯誤訊息範例（編碼前）：`VXNlciBjYW5jZWxsZWQgdGhlIHJlcXVlc3Q=`

```python
import base64
encoded_msg = "VXNlciBjYW5jZWxsZWQgdGhlIHJlcXVlc3Q"
decoded = base64.urlsafe_b64decode(encoded_msg + "==").decode("utf-8")
```
