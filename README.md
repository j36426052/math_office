# 教室借用系統 (FastAPI + Vue3)

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
API 文件： http://127.0.0.1:8000/docs

## 從 0 開始快速安裝與執行 (Zero-to-Run)
以下指令假設你只有系統預設的 git / Node / Python (>=3.11)。若缺少請先安裝。

### macOS / Linux
```bash
# 1. 取得原始碼 (若已在專案根目錄可略過)
git clone <YOUR_FORK_OR_REPO_URL> classroom-booking
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

# 6. (可選) 設定 API 位置，未設置則預設 http://127.0.0.1:8000
echo "VITE_API_BASE=http://127.0.0.1:8000" > .env

# 7. 啟動前端開發伺服器
npm run dev

# 8. （可選）在另一個終端執行測試
cd ../backend
pytest -q
```

打開瀏覽器：
- 使用者前端：http://localhost:5173
- 後端 Swagger 文件：http://127.0.0.1:8000/docs

### Windows (PowerShell)
```powershell
git clone <YOUR_FORK_OR_REPO_URL> classroom-booking
cd classroom-booking

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r backend\requirements.txt
uvicorn backend.app.main:app --reload --port 8000

cd frontend
npm install
"VITE_API_BASE=http://127.0.0.1:8000" | Out-File -Encoding utf8 .env
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
VITE_API_BASE=http://127.0.0.1:8000
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

回傳：
```json
{
  "created_ids": [10,11,17,25],
  "skipped_conflicts": ["2025-10-06T09:00:00", "2025-11-03T09:00:00"]
}
```

> 注意：跳過代表該週時段已存在可衝突的借用（非 rejected）。

## 類別與時間規則
| 類別 | 英文值 | 允許起迄 (本地時間 UTC+8) |
|------|--------|-------------------------|
| 活動 | activity | 05:00 ≤ start < end ≤ 22:00 |
| 會議 | meeting  | 05:00 ≤ start < end ≤ 17:00 |

所有時間需為「HH:00」或「HH:30」。

## 開發/測試注意
- 時區處理目前採簡化（以 UTC+8 偏移計算小時條件），未引入 timezone-aware 物件。
- 若需正式環境，建議改用 timezone-aware (e.g. `datetime.now(ZoneInfo('Asia/Taipei'))`).
- 測試中會重建資料庫，實際部署請改用遷移工具 (Alembic)。


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

## 授權
MIT
