# 教室借用系統 (FastAPI + Vue3)

![CI](https://github.com/j36426052/math_office/actions/workflows/ci.yml/badge.svg)

此專案提供簡單的教室借用功能：
- 前端：Vite + Vue3 (無登入，提供申請表單 / 一週總覽 / 後台管理頁)
- 後端：FastAPI + SQLite + SQLAlchemy
- 功能：
  - 列出教室與「未來 7 天」一週排程 `/rooms/weekly`
  - 查看單一教室與其借用時段
  - 建立借用申請（含姓名 / 身份 / 用途 / 起訖時間 / 類別）
  - 類別 (category) 與允許時間：
    - 活動 activity：05:00–22:00 (含整點/半點)
    - 會議 meeting：05:00–17:00 (含整點/半點)
  - 時間需為「整點或半點」，且結束時間 > 開始時間
  - 避免同教室時間重疊（未被拒絕的申請才列入衝突）
  - 後台管理（核可 / 退回 / 刪除 / 整學期週期性建立）
  - 整學期借用：指定星期、開始/結束日期區間、時間段，系統逐週建立，衝突自動跳過並回報

## 目錄結構
```
backend/
  app/
    main.py        # FastAPI 進入點
    models.py      # SQLAlchemy Models
    schemas.py     # Pydantic Schemas
    crud.py        # 資料存取/邏輯
    database.py    # DB Session & Base
  tests/
    test_bookings.py
frontend/
  src/
    main.js
    App.vue
    api.js
    pages/
      RoomsPage.vue
      RoomDetailPage.vue
      AdminPage.vue
```

## 後端啟動
(第一次) 安裝套件：
```
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
```
啟動伺服器：
```
uvicorn backend.app.main:app --reload --port 8000
```
API 文件（開發預設）: http://localhost:8000/docs  （部署時可關閉 docs 並設定自訂網域）

## 從 0 開始快速安裝與執行 (Zero-to-Run)
以下指令假設你只有系統預設的 git / Node / Python (>=3.11)。若缺少請先安裝。

### macOS / Linux
```bash
# 1. 取得原始碼 (若已在專案根目錄可略過)
git clone https://github.com/j36426052/math_office.git classroom-booking
cd classroom-booking

# 2. 建立並啟用 Python 虛擬環境
python -m venv .venv
source .venv/bin/activate

# 3. 安裝後端依賴
pip install -r backend/requirements.txt

# 4. 啟動後端 (前景執行)
uvicorn backend.app.main:app --reload --port 8000 &
# 若想在同一終端保持前景輸出，可改用：
# uvicorn backend.app.main:app --reload --port 8000

# 5. 安裝前端依賴
cd frontend
npm install

# 6. (可選) 設定 API 位置
# 默認：開發 (Vite 5173) 前端會自動使用 http://localhost:8000
# 若前後端同網域 & 反向代理，可不設定 VITE_API_BASE 讓前端採用相對路徑
echo "VITE_API_BASE=https://your-api.example.com" > .env

# 7. 啟動前端開發伺服器
npm run dev

# 8. （可選）在另一個終端執行測試
cd ../backend
pytest -q
```

打開瀏覽器：
- 使用者前端：http://localhost:5173
- 後端 Swagger 文件：開發階段 http://localhost:8000/docs （若未關閉）

### Windows (PowerShell)
```powershell
git clone https://github.com/j36426052/math_office.git classroom-booking
cd classroom-booking

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r backend\requirements.txt
uvicorn backend.app.main:app --reload --port 8000

cd frontend
npm install
"VITE_API_BASE=https://your-api.example.com" | Out-File -Encoding utf8 .env
npm run dev

# 新開一個 PowerShell 視窗可執行：
cd classroom-booking\backend
pytest -q
```

### 常見問題 (FAQ)
1. 看到 ModuleNotFoundError: backend：請確認在專案根目錄執行或 tests 已有 `backend` 上層 root 在 `sys.path`（本專案的 `tests/conftest.py` 已處理）。
2. 看到 資料庫檔案 `app.db` 尚未出現：第一次啟動 FastAPI 時會自動建立。
3. 更換 Port：後端可加 `--port 9000`；前端可用 `npm run dev -- --port 5174`。
4. 重新安裝乾淨環境：刪除 `.venv`、`node_modules`、`app.db` 後重跑上面流程。
5. 前端呼叫不到後端（CORS）：確認後端啟動、瀏覽器 devtools Network tab 狀態碼不是 404/500；`VITE_API_BASE` 是否一致。
6. 兩個 .env 差別？`frontend/.env` 只在本地 `npm run dev` 被 Vite 讀取，根目錄 `.env`（或 docker compose environment）提供後端與建置環境，正式 Docker 映像內前端已固定使用 `/api`。
7. 前端環境檔整合：已改用 `frontend/.env.example`，需要本地客製時執行 `cp frontend/.env.example frontend/.env`；請勿提交實際 `.env`。
8. Windows 提示缺少 tzdata / zoneinfo？安裝：`pip install tzdata`（本專案 requirements 已包含），或使用 WSL。若已有安裝仍錯，刪除 `.venv` 後重建；Docker 映像已安裝系統 `tzdata`，可改用容器避免本機時區套件問題。


## 前端啟動
進入 `frontend` 安裝依賴：
```
cd frontend
npm install
npm run dev
```
預設網址：http://localhost:5173

`.env` 可設定：
```
# 可選：指定後端 API 完整 URL（留空採相對路徑或預設 localhost:8000 開發）
VITE_API_BASE=https://your-api.example.com

# 後端 CORS 允許來源（逗號分隔），例：
# BACKEND_CORS_ORIGINS=http://localhost:5173,https://booking.example.edu
BACKEND_CORS_ORIGINS=
```

## API 簡述
| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | /rooms | 取得所有教室 |
| GET | /rooms/weekly | 取得所有教室未來 7 天內的已排定借用 (簡化週視圖) |
| GET | /rooms/{id} | 取得單一教室與 bookings |
| POST | /bookings | 建立借用申請 |
| GET | /bookings | 列出所有申請 (可加參數 room_id/status) |
| PATCH | /admin/bookings/{id} | 更新狀態 approved/rejected/pending |
| DELETE | /admin/bookings/{id} | 刪除申請 |
| POST | /admin/semester_bookings | 整學期（每週）批次建立申請 |

`POST /bookings` Body 範例：
```json
{
  "room_id": 1,
  "user_name": "張三",
  "user_identity": "S1234567",
  "purpose": "討論",
  "category": "activity",
  "start_time": "2025-09-17T10:00:00Z",
  "end_time": "2025-09-17T12:00:00Z"
}
```
`POST /admin/semester_bookings` Body 範例：
```json
{
  "room_id": 1,
  "category": "activity",
  "user_name": "助教A",
  "user_identity": "TA001",
  "purpose": "課程",
  "weekday": 2,            // 0=週一 ... 6=週日
  "start_date": "2025-09-01",
  "end_date": "2025-12-15",
  "start_time_hm": "09:00",
  "end_time_hm": "11:00"
}
```
```

> 注意：跳過代表該週時段已存在可衝突的借用（非 rejected）。

## 類別與時間規則
| 會議 | meeting  | 05:00 ≤ start < end ≤ 17:00 |

## 開發/測試注意
- 時區處理目前採簡化（以 UTC+8 偏移計算小時條件），未引入 timezone-aware 物件。
- 若需正式環境，建議改用 timezone-aware (e.g. `datetime.now(ZoneInfo('Asia/Taipei'))`).

若時間衝突會回傳 409：
```json
{ "detail": "時間衝突，請選擇其他時段" }
```

## 測試
```
pytest -q
```

## 後續擴充建議
- 加入身份驗證 (JWT / OAuth / SSO)
- 增加借用審核紀錄/理由欄位
- 加入教室設備/容量資訊
- 日曆視圖顯示 (FullCalendar)
- 分頁與查詢條件強化
- 真正的時區/夏令時間處理
- 借用申請 email 通知 & 審核 log

## Docker / Compose 部署 (解決不同 Port 造成的 CORS 問題)
此專案已提供 `deploy/docker-compose.yml` 以及前端 `nginx` 反向代理設定，讓瀏覽器只對同一來源 (port 80) 發送請求，透過 `/api/` 轉送到後端容器，達到「無需設定 CORS」的效果。

### 目標
- 使用者瀏覽器 → `http://your-host/` 取得前端 SPA
- API 呼叫 → 前端程式碼呼叫相對路徑 `/api/...` → `nginx` 代理 → `backend:8000`
- 因為對瀏覽器而言只有同源 (origin) `http://your-host`，不會再觸發跨來源預檢 (CORS preflight)

### 重要變更
- 前端建置時 `VITE_API_BASE` 已固定為 `/api`（參見 `deploy/Dockerfile.frontend`）。
- `deploy/nginx.conf` 啟用：
  ```nginx
  location /api/ { proxy_pass http://backend:8000/; }
  ```
- `docker-compose.yml` 中 frontend 不再需要 `VITE_API_BASE` 環境變數。
- 若不想對外暴露後端，可移除 backend 的 `ports` 映射 (仍可被 nginx 內部訪問)。

### 快速使用
```bash
docker compose -f deploy/docker-compose.yml up -d --build
open http://localhost/   # 或伺服器 IP
```

### 健康檢查
後端新增 `/healthz`：
```bash
curl http://localhost:8000/healthz
# {"status":"ok","time":"2025-01-01T00:00:00.000000"}
```
可在日後加入 docker healthcheck / 監控工具。

### 若仍需跨網域 (多網域/多 Port)
保留原本環境變數：
```
BACKEND_CORS_ALLOW_ALL=true  # 或 BACKEND_CORS_ORIGINS, BACKEND_CORS_ORIGINS_REGEX
```
但建議優先透過同源反向代理簡化瀏覽器行為。

### 管理端 Basic Auth / 登入流程
若根目錄 `.env`（或其他環境來源）未提供 `ADMIN_USER` / `ADMIN_PASS`，後端視為「未啟用驗證」：所有 admin 端點公開。正式環境務必設定以免遭濫用。

#### 設定方式（統一使用根目錄 `.env`）
1. 建立或修改專案根 `.env`：
  ```env
  ADMIN_USER=admin
  ADMIN_PASS=強密碼123
  DATABASE_URL=sqlite:////data/app.db
  TZ=Asia/Taipei
  ```
2. Docker 部署（compose 已設定 `env_file`）：
  ```bash
  docker compose -f deploy/docker-compose.yml up -d --build
  ```
  本機直接跑 uvicorn 則確保啟動前已存在 `.env` 或自行 `export` 變數。
3. 修改密碼後：
  ```bash
  docker compose -f deploy/docker-compose.yml restart backend
  ```
4. 暫時關閉保護：註解/刪除兩個變數後重啟（不建議正式環境）。

#### 前端登入行為
1. 進入 `/admin` 若收到 401 會顯示自製登入表單（不使用瀏覽器原生彈窗）。
2. 輸入帳密後會呼叫 `/admin/ping` 驗證成功即：
  - 將 Base64(`user:pass`) 保存於 `localStorage`（純示範，正式建議改 Token）。
  - 設定全域 `authState.isAdmin = true`，導覽列顯示「管理」。
3. 點擊「登出」移除保存的憑證並刷新狀態。
4. 若憑證過期 / 變更，後端再回 401，頁面會重新顯示登入表單。

#### 安全建議
- 僅在 HTTPS 環境傳輸 Basic Auth。
- 若要更安全：改為後端發行一次性 token 或 JWT；或把密碼只留在記憶體（`sessionStorage`）而非 `localStorage`。
- 可加入：IP allowlist、登入失敗延遲、審計 log。
- 若未來導入多使用者，建議直接改為基於資料庫的帳戶 + 雜湊密碼儲存。

### SQLite 持久化
`docker-compose.yml` 已加入 volume：
```
volumes:
  booking_data:
```
以及後端服務掛載 `/data` 並使用 `DATABASE_URL=sqlite:////data/app.db`，容器重建不會遺失資料。

### CI
GitHub Actions (`.github/workflows/ci.yml`) 會在 PR / main push：
1. 執行後端測試
2. 建置前端
3. 驗證 Docker build

可擴充：推送鏡像至 GHCR / Docker Hub、加入前端單元測試。

## 授權
MIT
