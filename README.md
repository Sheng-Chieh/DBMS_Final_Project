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
- 訪客可直接瀏覽首頁介紹。
- 註冊時需選擇學生或校友角色；登入後系統會依角色導向對應功能。
- 登出會清空登入狀態，回到訪客頁面。

### Onboarding 與履歷
- 首次登入會進入 Onboarding，填寫系所、入學/畢業年度等基本資料。
- 履歷頁整合活動、課程、工作經驗，支援新增、編輯與刪除。
- 校友可補上目前公司與職稱；學生則保留學習資訊與活動紀錄。

### 公司查詢與推薦
- 公司列表支援關鍵字、產業與地區條件篩選。
- 公司詳情會顯示與你同系所、且在該公司任職或有相關經歷的校友名單。
- 公司推薦聊天以向量檢索為基礎，並透過 Gemini 產生推薦理由；未設定 API Key 仍會有基本回覆。

### Coffee Chat
學生端：
- 瀏覽校友公開的對談時段並提交申請。
- 申請完成後可追蹤狀態（審核中/已接受/已婉拒）。

校友端：
- 建立對談時段，設定線上或線下地點、對談時間與目標系所。
- 管理已發布的時段，支援編輯、上下架與刪除。
- 審核申請者，可接受或婉拒，狀態即時更新。

### Micro Project
- 學生可瀏覽微任務列表，依產業/公司/標籤篩選。
- 校友可發布微任務並綁定標籤，方便學生快速找到合適的專案。

## 假資料與資料表說明
- 所有 CSV 位於 `dataset/`，可用 create_database.py 一鍵匯入。
- 需先執行 `python manage.py migrate`以紀錄使用者的登入狀態。
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
