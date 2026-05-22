# DBMS_Final_Project

以 Django + MySQL 為基底的校園職涯媒合平台，包含履歷管理、公司搜尋與推薦、Coffee Chat 對談、微任務專案等功能，並可用 CSV 假資料快速建立資料庫。

## 主要功能
- 角色分流：學生/校友註冊與登入
- Onboarding 與履歷管理：活動、課程、工作經驗
- 公司查詢與詳情：依關鍵字/產業/地區篩選
- 公司推薦聊天：RAG 向量檢索 + Gemini 回覆理由
- Coffee Chat：校友發布時段、學生申請、校友審核
- Micro Project：校友發布微任務、標籤分類與篩選

## 技術
- Python / Django
- MySQL
- LangChain + Chroma
- Hugging Face Embeddings

## 專案結構
- create_database.py：建立資料表與匯入 CSV 假資料
- dataset/：所有 CSV 假資料
- finalproject/：Django 專案根目錄 (含 manage.py)
- finalproject/templates/：前端模板
- finalproject/rag_data_lc/：公司 RAG 向量資料

## 前置需求
- Anaconda / Miniconda
- MySQL
- pip (conda 環境內)

## 安裝與啟動

### 1) 建立 Conda 環境 (建議)
```bash
conda create -n dbms_project python=3.11
conda activate dbms_project
```

### 2) 安裝相依套件
```bash
pip install -r requirements.txt
```

### 3) 建立資料庫
先在 MySQL 建立空的資料庫，例如 `final_project`。

### 4) 設定 .env
請在專案根目錄建立或調整 .env (與 create_database.py 同層)，內容可參考：

```env
GEMINI_API_KEY=your_gemini_api_key
HF_TOKEN=your_huggingface_token
RAG_EMBEDDING_MODEL=BAAI/bge-m3
RAG_DEVICE=cpu

DB_ENGINE=django.db.backends.mysql
DB_NAME=final_project
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=3306
```

說明：
- `RAG_EMBEDDING_MODEL`：公司向量索引使用的 Hugging Face 模型
- `RAG_DEVICE`：建議 Windows 用 `cpu`，有 GPU 可設為 `cuda`，Mac M系列晶片可設為 `mps`
- `HF_TOKEN`：只有在模型需要授權時才必須，或是加快下載速度
- `GEMINI_API_KEY`：公司推薦聊天會用到（沒設定會自動退化為固定訊息）

### 5) 建表與匯入假資料
執行互動式工具：
```bash
python create_database.py
```

建議流程：
1. 選 `1` 重建所有資料表 (會清空舊資料)
2. 選 `2` 進入匯入專區後，輸入 `A` 一鍵匯入全部 CSV

### 6) (可選) 重新建立公司 RAG 索引
當你更新 `companies` 資料或更換 `RAG_EMBEDDING_MODEL` 時，建議重新建索引：
```bash
python finalproject/company/rag_lc/build_index.py
```

### 7) 啟動 Django 伺服器
```bash
cd finalproject
python manage.py runserver
```

瀏覽：http://127.0.0.1:8000/

## 功能操作說明

### 首頁與登入
- `/`：訪客首頁
- `/register`：註冊 (選擇學生或校友)
- `/login`：登入
- `/logout`：登出

### Onboarding 與履歷
- `/onboarding`：首次登入的基本資料填寫
- `/resume`：個人履歷總覽
- `/add-activity`、`/add-work`、`/add-course`：新增履歷資料
- `/activity/update/<id>`、`/work/update/<id>`、`/course/update/<id>`：更新資料
- `/activity/delete/<id>`、`/work/delete/<id>`、`/course/delete/<id>`：刪除資料

### 公司查詢與推薦
- `/search`：公司列表與篩選
- `/company/<id>`：公司詳情 + 同系所校友列表
- `/company/chat`：公司推薦聊天頁面
- `/company/chat_lc`：聊天 API (SSE)

### Coffee Chat
學生端：
- `/coffeechat/apply`：查看已發布時段並送出申請
- `/coffeechat/my-applications`：查看自己的申請狀態

校友端：
- `/ca_homepage`：校友首頁
- `/manage-chats`：管理自己發布的時段 (新增/編輯/上下架/刪除)
- `/manage-applicants`：審核申請者 (接受/拒絕)

### Micro Project
- `/projects/`：微任務列表與篩選
- `/projects/create/`：校友發布微任務 (學生不可發布)

## 假資料與資料表說明
- 所有 CSV 位於 `dataset/`，可用 create_database.py 一鍵匯入。
- 本專案使用原生 SQL 操作。
- 若顯示資料表不存在，請先執行 create_database.py 建表。

## 常見問題

### 1) 無法連線資料庫
- 確認 .env 內的 `DB_*` 設定
- 確認 MySQL 已啟動且資料庫已建立

### 2) 公司推薦聊天沒有回覆理由
- 確認 `GEMINI_API_KEY` 已設定
- 若未設定，系統會使用固定 fallback 訊息

### 3) RAG 查不到公司
- 確認 `rag_data_lc/` 是否與資料同步
- 重新執行 `finalproject/company/rag_lc/build_index.py`

## 其他
- 如需部署或調整設定，請先修改 .env 與 `finalproject/settings.py`。
