---
name: digirunner-oidc-flow-guide
description: 引導完成 digiRunner OIDC 完整登入流程設定。觸發時機：使用者提到「OIDC 登入」、「digiRunner 認證」、「OAuth 設定」、「建立 Client」、「JDBC IdP」、「完整認證流程」等關鍵字。此 Skill 會檢查系統是否已有 OIDC 程式碼，並按順序使用 MCP tools 與相關 sub-skills 完成設定。
---

# digiRunner OIDC Flow Guide

完整的 OIDC 登入流程導引，包含 digiRunner MCP tools 設定與程式碼實作。

## 流程決策樹

```
開始
  │
  └─ 系統是否已有 OIDC 程式碼？
       │
       ├─ 是 → 跳過程式碼實作，直接到「Phase 3: 前端環境變數設定」
       │
       └─ 否 → 執行「Phase 1: MCP 資料建立」
                 ↓
               執行「Phase 2: 程式碼實作」
                 ↓
               執行「Phase 3: 前端環境變數設定」
```

## Phase 1: MCP 資料建立

使用 digiRunner MCP tools 依序執行：

### Step 1: 反向代理設定

> ⚠️ `<website_name>` 與 `<frontend_url>` 需詢問使用者。

```
1. digiRunner-configureStaticWebReverseProxy   # 設定靜態網頁反向代理
   ├─ websiteName: "<website_name>"            ← ⚠️ 詢問使用者
   ├─ url: "<frontend_url>"                    ← ⚠️ 詢問使用者（格式見下方）
   └─ remark: "<remark>"
```

> **`url` 參數格式**（必須遵守）：
>
> ```
> http://{domain}/website/{path}/
> https://{domain}/website/{path}/
> ```
>
> - `{domain}`：前端服務的網域或 IP:Port（例如 `192.168.1.100:4200`）
> - `{path}`：前端服務的路徑（通常與 `websiteName` 相同）
> - Protocol 為 `http://` 或 `https://`，視前端服務而定
>
> 範例：`http://192.168.1.100:4200/website/tpi_bank/`

### Step 2: Client 設定

> ⚠️ `<client_id>` 需詢問使用者。此為 digiRunner 上註冊的用戶端 ID。

```
2. digiRunner-searchClient      # 查詢 clientId 是否存在
   └─ keyword: "<client_id>"           ← ⚠️ 詢問使用者

3. digiRunner-createClient      # 建立用戶端（若不存在）
   ├─ clientID: "<client_id>"          ← ⚠️ 詢問使用者
   ├─ clientName: "<client_name>"
   ├─ clientAlias: "<client_alias>"
   └─ clientBlock: "<password>"

4. digiRunner-updateClientTokenSettings  # 更新 Token 設定
   ├─ clientID: "<client_id>"
   ├─ authorizedGrantType: "refresh_token,client_credentials,password,public,authorization_code"
   ├─ accessTokenQuota: "0"
   ├─ refreshTokenQuota: "0"
   └─ webServerRedirectUri: "<redirect_uri>"   ← ⚠️ 格式見下方
   └─ webServerRedirectUri1: ""
   └─ webServerRedirectUri2: ""
   └─ webServerRedirectUri3: ""
   └─ webServerRedirectUri4: ""
   └─ webServerRedirectUri5: ""   
```

> **`webServerRedirectUri` 格式**（必須遵守）：
>
> ```
> https://{DIGIRUNNER_DOMAIN}/website/{websiteName}/callback
> ```
>
> - `{DIGIRUNNER_DOMAIN}`：digiRunner 伺服器網域
> - `{websiteName}`：Step 1 設定的靜態網頁反向代理名稱
> - 範例：`https://digirunner.example.com/website/tpi_bank/callback`
> - ❌ 錯誤：`https://example.com/callback`（不可使用非 digiRunner 的網域）
> - ❌ 錯誤：`https://digirunner.example.com/callback`（缺少 `/website/{websiteName}/` 路徑）
> - ✅ 正確：`https://digirunner.example.com/website/tpi_bank/callback`

### Step 3: Group 設定

```
5. digiRunner-searchGroup       # 查詢群組是否存在
   └─ keyword: "<group_name>"

6. digiRunner-createGroup       # 建立群組（若不存在）
   ├─ groupName: "<group_name>"
   └─ groupAlias: "<group_alias>"

7. digiRunner-associateClientGroup  # 關聯用戶端與群組
   ├─ clientID: "<client_id>"
   └─ groupID: "<group_id>"
```

### Step 4: JDBC IdP 設定

> ⚠️ `<jdbc_url>`、`<db_user>`、`<db_password>` 需詢問使用者。這些是連線至使用者資料庫的設定。

```
8. digiRunner-testJdbcConnection    # 測試 JDBC 連線
   ├─ connName: "<connection_name>"
   ├─ jdbcUrl: "<jdbc_url>"         ← ⚠️ 詢問使用者（JDBC 連線字串）
   ├─ userName: "<db_user>"         ← ⚠️ 詢問使用者（資料庫帳號）
   └─ mima: "<db_password>"         ← ⚠️ 詢問使用者（資料庫密碼）

9. digiRunner-createJdbcConnection  # 建立 JDBC 連線（測試成功後）
   ├─ connectionName: "<connection_name>"
   ├─ jdbcUrl: "<jdbc_url>"         ← 同上
   ├─ userName: "<db_user>"         ← 同上
   ├─ mima: "<db_password>"         ← 同上
   ├─ maxPoolSize: "10"
   ├─ connectionTimeout: "30000"
   ├─ idleTimeout: "600000"
   ├─ maxLifetime: "1800000"
   └─ dataSourceProperty: ""
```

#### Step 10: 建立 GTW JDBC IdP（終端使用者身分驗證資料來源）

> 這是設定 OIDC 的「終端使用者身分驗證」的資料來源。
> digiRunner 會依據這些設定值去查詢使用者資料表，並取得終端使用者的資訊（如帳號、密碼、姓名、Email 等）。

> ⚠️ **欄位名稱格式：`{{$<欄位名稱>%}}` 是字面值（Literal Value）**
>
> 以下標示「格式：`{{$<欄位名稱>%}}`」的欄位，`{{$...%}}` 是**必須原封不動傳給 MCP tool 的字面值**，不是文件 Placeholder。
>
> | | 傳入值 | 說明 |
> |---|---|---|
> | ✅ 正確 | `{{$password%}}` | 完整包含 `{{$` 前綴與 `%}}` 後綴 |
> | ❌ 錯誤 | `password` | 缺少 `{{$...%}}` 包裝，digiRunner 無法識別 |
>
> 此格式同樣適用於 `sqlParams`、`userMimaColName`、`idtSub`、`idtName`、`idtEmail`、`idtPicture` 等欄位。

```
10. digiRunner-createGtwJdbcIdp
   ├─ clientId: "<client_id>"
   ├─ status: "Y"
   ├─ connectionName: "<connection_name>"
   │
   │  ── SQL 查詢設定 ──
   ├─ sqlPtmt: "<sql_query>"                  ← ⚠️ 詢問使用者
   │     查詢使用者資料的 SQL Prepare Statement。
   │     範例："SELECT * FROM users WHERE username = ?"
   ├─ sqlParams: "[\"{{$username%}}\"]"        ← ⚠️⚠️⚠️ 固定值，禁止修改 ⚠️⚠️⚠️
   │     此值為 digiRunner 系統保留字，**絕對不可替換為其他字串**。
   │     digiRunner 會自動將登入時輸入的帳號帶入 `{{$username%}}` 參數。
   │     ❌ 錯誤："[\"{{$ACCOUNT%}}\"]"（不可替換為資料表實際欄位名稱）
   │     ❌ 錯誤："[\"{{$login_id%}}\"]"（不可替換為其他任何字串）
   │     ✅ 正確："[\"{{$username%}}\"]"（永遠使用此固定值，無論資料表欄位名稱為何）
   │
   │  ── 密碼驗證設定 ──
   ├─ userMimaAlg: "Plain"                    ← ⚠️ 詢問使用者
   │     使用者資料表的密碼欄位的加密演算法。
   │     選項："Plain"（明文）| "Bcrypt" | "SHA256" | "SHA512"
   │     預設 "Plain"，表示密碼欄位的資料是明文儲存。
   ├─ userMimaColName: "{{$password%}}"       ← ⚠️ 詢問使用者實際欄位名稱（必須保留 {{$...%}} 包裝）
   │     格式：{{$<欄位名稱>%}}
   │     使用者資料表中「密碼」欄位的名稱。
   │     範例：若密碼欄位為 "pwd"，則填 "{{$pwd%}}"
   │     ❌ 錯誤：填 "password"（缺少 {{$...%}}）
   │     ✅ 正確：填 "{{$password%}}"
   │
   │  ── ID Token Claims 對應 ──
   ├─ idtSub: "{{$seq%}}"                    ← ⚠️ 詢問使用者實際欄位名稱（必須保留 {{$...%}} 包裝）
   │     格式：{{$<欄位名稱>%}}
   │     終端使用者的唯一識別碼（對應 JWT 的 sub claim）。
   │     範例：若主鍵欄位為 "user_id"，則填 "{{$user_id%}}"
   ├─ idtName: "{{$name%}}"                  ← ⚠️ 詢問使用者實際欄位名稱（必須保留 {{$...%}} 包裝）
   │     格式：{{$<欄位名稱>%}}
   │     終端使用者的顯示名稱（對應 JWT 的 name claim）。
   │     範例：若名稱欄位為 "display_name"，則填 "{{$display_name%}}"
   ├─ idtEmail: "{{$email%}}"                ← ⚠️ 詢問使用者實際欄位名稱（必須保留 {{$...%}} 包裝）
   │     格式：{{$<欄位名稱>%}}
   │     終端使用者的電子郵件（對應 JWT 的 email claim）。
   │     範例：若 Email 欄位為 "mail"，則填 "{{$mail%}}"
   ├─ idtPicture: "{{$picture%}}"            ← ⚠️ 詢問使用者實際欄位名稱（必須保留 {{$...%}} 包裝）
   │     格式：{{$<欄位名稱>%}}
   │     終端使用者的頭像 URL（對應 JWT 的 picture claim）。
   │     範例：若頭像欄位為 "avatar_url"，則填 "{{$avatar_url%}}"
   │     若無頭像欄位，可留空字串 ""
   │
   │  ── 頁面與備註 ──
   ├─ pageTitle: "<PageTitle>"                ← ⚠️ 詢問使用者
   │     OIDC 登入頁面的標題文字。範例："會員登入"
   └─ remark: "<remark>"                      ← ⚠️ 詢問使用者
         備註欄位，可填寫說明文字。範例："銀行系統 OIDC 身分驗證"
```

## Phase 2: 程式碼實作

依序觸發以下 sub-skills：

| 順序 | Skill | 功能 |
|-----|-------|------|
| 1 | `digiRunner-oidc-auth-request` | 產生授權 URL、state、PKCE code_verifier/challenge |
| 2 | `digiRunner-oidc-auth-callback` | 實作 redirect_uri callback endpoint |
| 3 | `digiRunner-oidc-token-exchange` | 用授權碼換取 Access/Refresh/ID Token |
| 4 | `digiRunner-oidc-token-verify` | 驗證 ID Token 並取得使用者資訊 |
| 5 | `digiRunner-oidc-token-refresh` | Access Token 過期時，用 Refresh Token 換取新 Token |
| 6 | `digiRunner-oidc-token-revocation` | 登出時撤銷 Access Token 和 Refresh Token |

## Phase 3: 前端環境變數設定

> `DIGIRUNNER_DOMAIN` 與 `CLIENT_ID` 因部署環境不同而異（dev / staging / production），
> 必須放到前端的環境變數檔案，不可寫死在程式碼中。

### ⚠️ Protocol 規則（必須遵守）

digiRunner 的 Protocol **必須**為 `https://`，**禁止使用 `http://`**：

- ✗ 錯誤：`http://{DIGIRUNNER_DOMAIN}/...`
- ✓ 正確：`https://{DIGIRUNNER_DOMAIN}/...`

> 產生的所有程式碼中，呼叫 digiRunner 端點時 **一律使用 `https://`**。`DIGIRUNNER_DOMAIN` 環境變數僅包含網域名稱（不含 protocol），程式碼中拼接時必須使用 `https://`。

### ⚠️ SSL 自簽署憑證處理

digiRunner 預設使用自簽署憑證 (Self-signed Certificate)：

- **開發環境**：可跳過 SSL 憑證驗證（`DIGIRUNNER_SSL_VERIFY=false`）
- **生產環境**：**必須**使用有效的 SSL 憑證，確保安全性（`DIGIRUNNER_SSL_VERIFY=true`）

> 使用 `DIGIRUNNER_SSL_VERIFY` 環境變數控制是否驗證 SSL 憑證。**生產環境禁止跳過 SSL 驗證。**

### 需設定的環境變數

| 變數名稱 | 說明 | 用途 | 範例 |
|----------|------|------|------|
| `DIGIRUNNER_DOMAIN` | digiRunner 伺服器網域（不含 `https://`） | OIDC 登入、API 呼叫 | `digirunner.example.com` |
| `CLIENT_ID` | 在 digiRunner 註冊的用戶端 ID | OIDC 登入 | `my-bank-client` |
| `MODULE_NAME` | 模組名稱（digiRunner API 註冊用） | `digirunner-api-setup` Step 1/2 建立與啟用 API | `bank` |
| `DIGIRUNNER_SSL_VERIFY` | 是否驗證 SSL 憑證 | 開發環境 `false`（跳過自簽署憑證驗證），生產環境 `true` | `false` |

### 依前端框架設定

根據專案使用的前端框架，在對應的 `.env` 檔案中加入環境變數（使用框架要求的前綴）：

**Vite (Vue / React)**
```env
# .env.local 或 .env.production
VITE_DIGIRUNNER_DOMAIN=digirunner.example.com
VITE_CLIENT_ID=my-bank-client
VITE_MODULE_NAME=bank
VITE_DIGIRUNNER_SSL_VERIFY=false   # 開發環境：false，生產環境：true
```

程式碼中讀取：`import.meta.env.VITE_DIGIRUNNER_DOMAIN`

**Next.js**
```env
# .env.local 或 .env.production
NEXT_PUBLIC_DIGIRUNNER_DOMAIN=digirunner.example.com
NEXT_PUBLIC_CLIENT_ID=my-bank-client
NEXT_PUBLIC_MODULE_NAME=bank
NEXT_PUBLIC_DIGIRUNNER_SSL_VERIFY=false   # 開發環境：false，生產環境：true
```

程式碼中讀取：`process.env.NEXT_PUBLIC_DIGIRUNNER_DOMAIN`

**Angular**
```typescript
// environment.ts（開發環境）
export const environment = {
  digiRunnerDomain: 'digirunner.example.com',
  clientId: 'my-bank-client',
  moduleName: 'bank',
  digiRunnerSslVerify: false,   // 開發環境：false
};

// environment.prod.ts（生產環境）
export const environment = {
  digiRunnerDomain: 'digirunner.example.com',
  clientId: 'my-bank-client',
  moduleName: 'bank',
  digiRunnerSslVerify: true,    // 生產環境：true
};
```

**純前端 / 其他框架**
```env
# .env
DIGIRUNNER_DOMAIN=digirunner.example.com
CLIENT_ID=my-bank-client
MODULE_NAME=bank
DIGIRUNNER_SSL_VERIFY=false   # 開發環境：false，生產環境：true
```

**Node.js 後端**
```env
# .env
DIGIRUNNER_DOMAIN=digirunner.example.com
CLIENT_ID=my-bank-client
MODULE_NAME=bank
DIGIRUNNER_SSL_VERIFY=false   # 開發環境：false，生產環境：true
# 當 DIGIRUNNER_SSL_VERIFY=false 時，程式碼中需設定：
# process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
```

### 注意事項

- 每個環境（開發、測試、正式）需各自的 `.env` 檔案
- `.env.local` 不應提交至 Git，可提供 `.env.example` 作為範本
- 前端程式碼中使用環境變數取代寫死的值
- **開發環境**設定 `DIGIRUNNER_SSL_VERIFY=false` 以跳過自簽署憑證驗證
- **生產環境**必須設定 `DIGIRUNNER_SSL_VERIFY=true` 並使用有效的 SSL 憑證

## Phase 4: 執行完成說明

### 變數設定摘要

完成上述所有 Phase 後，系統中應已設定以下關鍵資訊：

| 類別 | 變數 / 設定 | 說明 | 來源 |
|------|------------|------|------|
| 反向代理 | `websiteName` | 靜態網頁反向代理名稱 | Phase 1 Step 1 |
| 用戶端 | `CLIENT_ID` | digiRunner 用戶端 ID | Phase 1 Step 2 |
| 群組 | `groupID` / `groupName` | 群組識別資訊 | Phase 1 Step 3 |
| 資料庫 | `connectionName` | JDBC 連線名稱 | Phase 1 Step 4 |
| 前端環境 | `DIGIRUNNER_DOMAIN` | digiRunner 網域 | Phase 3 |
| 前端環境 | `MODULE_NAME` | API 模組名稱 | Phase 3 |
| 前端環境 | `DIGIRUNNER_SSL_VERIFY` | SSL 憑證驗證開關 | Phase 3 |

### 反向代理進入點

前端網頁透過 digiRunner 反向代理提供服務，進入點為：

```
https://{DIGIRUNNER_DOMAIN}/website/{websiteName}/
```

> ⚠️ **前端 Asset 路徑規則**（產生程式碼時必須遵守）：
> - ✗ 錯誤：`/css`、`/js`、`/images`、`/config.js`
> - ✗ 錯誤：`/{websiteName}/css`、`/{websiteName}/js`（缺少 `/website/` 前綴）
> - ✓ 正確：`/website/{websiteName}/css`、`/website/{websiteName}/js`、`/website/{websiteName}/images`、`/website/{websiteName}/config.js`
>
> 前端透過反向代理部署於 `/website/{websiteName}/` 路徑下，所有靜態資源的絕對路徑必須包含 `/website/{websiteName}/` 前綴。
>
> **Vite 設定**（vite.config.ts）必須設定 `base: '/website/{websiteName}/'`，使所有 Asset 路徑自動加上前綴。
>
> ⚠️ 產生的所有前端程式碼中，靜態資源路徑**必須**包含 `/website/{websiteName}/` 前綴，否則透過 digiRunner 反向代理時將無法載入資源。

### 移植到其他環境

將系統移植到不同環境（dev → staging → production）時，需調整以下設定：

1. **前端環境變數**：更新 `.env` 中的 `DIGIRUNNER_DOMAIN`（指向目標環境的 digiRunner）
2. **反向代理**：在目標環境的 digiRunner 上重新執行 `digiRunner-configureStaticWebReverseProxy`，設定前端 URL 指向目標環境的前端服務（格式：`http(s)://{domain}/website/{path}/`）
3. **JDBC 連線**：若資料庫不同，需在目標環境重新建立 JDBC 連線與 GTW JDBC IdP
4. **Client / Group**：通常可沿用，若目標環境的 digiRunner 為獨立實例則需重新建立

### 維護與更新

- **新增 API**：使用 `digirunner-api-setup` skill，搭配已設定的 `MODULE_NAME` 和群組資訊
- **更新前端**：更新前端部署來源後，反向代理會自動指向新版本
- **更新 Token 設定**：使用 `digiRunner-updateClientTokenSettings` 調整 OAuth Grant Type 或 Redirect URI
- **更新 JDBC IdP**：若使用者資料表結構變更，需重新設定 GTW JDBC IdP

### Token 生命週期管理

OIDC 流程完成後，應用程式需管理 Token 的完整生命週期：

| 場景 | 使用 Skill | 說明 |
|------|-----------|------|
| Access Token 過期 | `digiRunner-oidc-token-refresh` | 用 Refresh Token 換取新的 Access Token，使用者無需重新登入 |
| Refresh Token 過期 | — | 引導使用者重新執行 OIDC 登入流程 |
| 使用者登出 | `digiRunner-oidc-token-revocation` | 同時撤銷 Access Token 和 Refresh Token |
| 呼叫 API | `digiRunner-oidc-api-call` | 推薦使用 Axios 攔截器集中管理 headers，並自動處理 401 Token 刷新 |

## 檢查 OIDC 程式碼是否存在

搜尋專案中是否包含以下關鍵程式碼：

```bash
# 搜尋授權請求相關程式碼
grep -r "code_verifier\|code_challenge\|authorization_code" --include="*.java" --include="*.kt" --include="*.ts" --include="*.js"

# 搜尋 Token 交換相關程式碼
grep -r "token_endpoint\|grant_type.*authorization_code" --include="*.java" --include="*.kt" --include="*.ts" --include="*.js"
```

若搜尋結果為空，則需要實作 OIDC 程式碼。

## 注意事項

- OIDC 登入流程程式碼在系統中**只需實作一次**
- 確保 redirect_uri 格式為 `https://{DIGIRUNNER_DOMAIN}/website/{websiteName}/callback`，與 digiRunner Client 設定的 `webServerRedirectUri` 一致
- `sqlParams` 固定為 `["{{$username%}}"]`，此為 digiRunner 系統保留字，禁止替換
