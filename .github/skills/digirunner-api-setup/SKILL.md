---
name: digirunner-api-setup
description: 使用 digiRunner MCP tools 建立並設定 API。觸發時機：使用者提到「建立 API」、「新增 API」、「API 設定」、「啟用 API」、「API 關聯群組」、「digiRunner API」等關鍵字。每次需要在 digiRunner 上註冊新 API 時使用此 Skill。
---

# digiRunner API Setup

使用 digiRunner MCP tools 快速建立、啟用並關聯 API。

## ⚠️ 重要架構原則

```
┌──────────┐     ┌─────────────┐     ┌──────────┐
│  前端    │ ──► │ digiRunner  │ ──► │  後端    │
│ Frontend │     │ API Gateway │     │ Backend  │
└──────────┘     └─────────────┘     └──────────┘
     │                  │
     │   ✗ 禁止直接呼叫  │
     └────────X─────────┘
```

**前端絕對不能直接呼叫後端 API！**

- ✗ 錯誤：`fetch('http://backend:8080/api/users')`
- ✓ 正確：`fetch('https://digirunner-domain/{apiId}')`

所有 API 請求必須經過 digiRunner API Gateway，由 digiRunner 轉發到後端。

**前端 Asset 路徑規則**（產生程式碼時必須遵守）：
- ✗ 錯誤：`/css`、`/js`、`/images`、`/config.js`
- ✗ 錯誤：`/{websiteName}/css`、`/{websiteName}/js`（缺少 `/website/` 前綴）
- ✓ 正確：`/website/{websiteName}/css`、`/website/{websiteName}/js`、`/website/{websiteName}/images`、`/website/{websiteName}/config.js`

> 前端透過反向代理部署於 `https://digirunner-domain/website/{websiteName}/`，所有靜態資源的絕對路徑必須包含 `/website/{websiteName}/` 前綴。

```javascript
// Vite 設定（vite.config.ts）— 必須設定 base 為 /website/{websiteName}/
export default defineConfig({
  base: '/website/{websiteName}/',  // ← 所有 Asset 路徑自動加上此前綴
});
```

> ⚠️ 產生的所有前端程式碼中，靜態資源的路徑**必須**包含 `/website/{websiteName}/` 前綴，否則透過 digiRunner 反向代理時將無法載入資源。

## 使用時機

- 需要在 digiRunner 註冊新的後端 API
- 已完成 OIDC 登入流程設定（若未完成，先使用 `digirunner-oidc-flow-guide`）

## API 建立流程

依序執行以下 MCP tools：

### Step 1: 建立 API

```
digiRunner-createApi
├─ apiId: "<api_id>"           # API 唯一識別碼（前端呼叫用）
├─ apiName: "<api_name>"       # API 名稱
├─ srcUrl: "<backend_url>"     # 後端目標 URL（digiRunner 轉發用）
├─ moduleName: "<module>"      # 模組名稱（前端呼叫用）
├─ methods: "GET,POST"         # 允許的 HTTP Methods
└─ noOAuth: "N"                # 是否需要 OAuth（Y/N）
```

### Step 2: 啟用 API

```
digiRunner-enableApi
├─ moduleName: "<module>"      # 與 Step 1 相同的模組名稱
└─ apiId: "<api_id>"           # 與 Step 1 相同的 API ID
```

### Step 3: 查詢用戶端群組資訊

> 💡 使用 `CLIENT_ID` 搭配 `digiRunner-searchClient` 查出 `clientName`，再使用 `digiRunner-queryClientGroups` 查詢該用戶端所屬的群組資訊，供下一步關聯 API 時使用。

```
digiRunner-searchClient
└─ keyword: "<client_id>"          # 用 CLIENT_ID 查詢用戶端

# 從查詢結果取得 clientName 後

digiRunner-queryClientGroups
├─ clientID: "<client_id>"         # CLIENT_ID
└─ clientName: "<client_name>"     # 從 searchClient 查詢結果取得
```

從查詢結果中找到對應的群組，取得 `groupID`、`groupName` 和 `groupAlias`。

### Step 4: 關聯 API 與群組

> 💡 `groupID`、`groupName`、`groupAlias` 從 Step 3 查詢結果取得；`moduleName` 從前端環境變數取得。

```
digiRunner-associateApiGroup
├─ groupID: "<group_id>"       # 群組 ID（從 Step 3 查詢結果取得）
├─ groupName: "<group_name>"   # 群組代碼（從 Step 3 查詢結果取得）
├─ groupAlias: "<group_alias>" # 群組名稱（從 Step 3 查詢結果取得）
├─ moduleName: "<module>"      # 模組名稱（從前端環境變數取得）
└─ apiId: "<api_id>"           # API ID
```

## 參數說明

| 參數 | 說明 | 範例 |
|-----|------|------|
| apiId | API 唯一識別碼（前端呼叫路徑） | `get-user-profile` |
| apiName | API 顯示名稱 | `使用者查詢 API` |
| srcUrl | 後端服務 URL（digiRunner 轉發目標） | `http://backend:8080/api/v1/users` |
| moduleName | 模組分類名稱（前端呼叫路徑） | `user-service` |
| methods | HTTP Methods（逗號分隔） | `GET,POST,PUT,DELETE` |
| noOAuth | 是否跳過 OAuth 驗證 | `N`（需要驗證） |

## 前端呼叫方式

API 建立完成後，**前端必須呼叫 digiRunner 端點**：

```
https://{DIGIRUNNER_DOMAIN}/{apiId}
```

> ⚠️ 前端 URL 只需 `/{apiId}`，不包含 `{moduleName}`。`moduleName` 僅用於 digiRunner 內部設定。
> ⚠️ `DIGIRUNNER_DOMAIN` 因環境而異，必須從前端環境變數讀取，不可寫死。
> 詳見 `digirunner-oidc-flow-guide` 的 Phase 3 說明。

使用 `digiRunner-oidc-api-call` skill 產生正確的呼叫程式碼，確保：
- 呼叫 digiRunner URL，而非後端 URL
- 帶入 `ID-Token` 和 `Authorization: Bearer {access_token}` Header

## 完整範例

建立一個使用者查詢 API：

```
# Step 1: 建立（srcUrl 是後端地址，前端不會直接用到）
digiRunner-createApi
  apiId: "get-user-profile"
  apiName: "取得使用者資料"
  srcUrl: "http://backend-server:8080/api/v1/users/profile"  ← 後端 URL
  moduleName: "user-service"
  methods: "GET"
  noOAuth: "N"

# Step 2: 啟用
digiRunner-enableApi
  moduleName: "user-service"
  apiId: "get-user-profile"

# Step 3: 查詢用戶端群組資訊
digiRunner-searchClient
  keyword: "my-bank-client"

# 從查詢結果取得 clientName 後
digiRunner-queryClientGroups
  clientID: "my-bank-client"
  clientName: "my-bank-client-name"    ← 從 searchClient 查詢結果取得

# Step 4: 關聯群組（groupID、groupName、groupAlias 從 Step 3 查詢結果取得）
digiRunner-associateApiGroup
  groupID: "grp-001"
  groupName: "default-group"
  groupAlias: "預設群組"
  moduleName: "user-service"
  apiId: "get-user-profile"
```

**前端呼叫**（使用 `digiRunner-oidc-api-call` skill 產生）：

```javascript
// ✓ 正確：呼叫 digiRunner（URL 只用 apiId，不含 moduleName）
const response = await fetch('https://digirunner.example.com/get-user-profile', {
  headers: {
    'ID-Token': idToken,
    'Authorization': `Bearer ${accessToken}`
  }
});

// ✗ 錯誤：直接呼叫後端
// const response = await fetch('http://backend-server:8080/api/v1/users/profile');
```
