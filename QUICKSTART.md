# 🚀 Credit Risk ELT Pipeline - Quickstart Guide / Hướng dẫn Khởi chạy nhanh

> Select your language / Chọn ngôn ngữ hiển thị để xem chi tiết:

<details open>
<summary><b>🇬🇧 English Version (Click to collapse)</b></summary>

## Welcome to the Credit Risk Data Engineering Project
This repository contains a production-ready ELT (Extract, Load, Transform) pipeline designed to ingest, validate, and process credit risk datasets for downstream analytics and machine learning.

---

### 🛠 Prerequisites
Ensure you have the following installed on your machine:
*   **Python 3.10+** (Python 3.11 recommended)
*   **Git**
*   **Kaggle Account & API Token** (for downloading the source dataset)
*   **SQL Server** (required only for the DB Load phase)

---

### ⚙️ Setup Instructions

#### 1. Clone the Repository
```bash
git clone <repository-url>
cd DATN
```

#### 2. Create and Activate a Virtual Environment
**Windows:**
```powershell
python -m venv .venv
.venv\Scripts\activate
```
**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Configure Environment Variables
Create a `.env` file in the root directory of the project and add your configurations:
```env
# Kaggle API Credentials
KAGGLE_API_TOKEN=YOUR_KAGGLE_API_TOKEN_HERE

# Database Credentials (SQL Server)
DB_SERVER=YOUR_SERVER_NAME
DB_NAME=CreditRiskDB
DB_USER=sa
DB_PASS=YOUR_PASSWORD_HERE
```
*Note: Go to [Kaggle Account Settings](https://www.kaggle.com/settings) and click **'Your API Token'** -> **Generate New Key** to obtain your Kaggle token.*

---

### 🚀 Running the Pipeline

To run the complete ELT pipeline (Downloads from Kaggle, runs validation rules, auto-heals missing data, and naps to SQL Server):
```bash
# Set PYTHONPATH and run main
$env:PYTHONPATH = "."
python -m src.main
```

To run the pipeline in **standalone mode** (Extract & Transform only, without database connection):
```bash
$env:PYTHONPATH = "."
python -m src.main --skip-db
```

---

### ✨ Key Features
1.  **Data Quality Scanner:** Automatically runs 21 business validation rules (defined in `DQ_rules.json`) and outputs a structured log to `docs/03_notes/engineering/data_issues.txt`.
2.  **Data Healing & Imputation:** Imputes missing numerical variables (median-by-age for employment length, and median-by-grade for interest rates) before validation checks.
3.  **Data Segregation:** Splits output into `df_pass.csv` (perfect data), `df_warning.csv` (healed data), and `df_critical.csv` (quarantined records).
4.  **Database Star Schema:** Automatically runs `sp_load_star_schema` stored procedure in SQL Server to model data into Fact and Dimension tables.

---

### 🤝 Contributing
*   Follow the Object-Oriented Programming (OOP) design patterns inside `src/`.
*   Keep business rules configuration-driven by updating `src/etl/extract/DQ_rules.json`.
*   Ensure unit tests pass before submitting code.

</details>

<details>
<summary><b>🇻🇳 Bản Tiếng Việt (Click để mở rộng)</b></summary>

## Chào mừng bạn đến với Dự án Xử lý Dữ liệu Rủi ro Tín dụng
Mã nguồn này chứa quy trình ELT (Trích xuất, Nạp, Biến đổi) chuẩn sản xuất được thiết kế để thu thập, xác thực chất lượng và chuẩn hóa các tập dữ liệu tín dụng bán lẻ phục vụ phân tích nghiệp vụ và học máy.

---

### 🛠 Điều kiện tiên quyết
Đảm bảo máy tính của bạn đã được cài đặt sẵn:
*   **Python 3.10+** (Khuyên dùng Python 3.11)
*   **Git**
*   **Tài khoản Kaggle & API Token** (để trích xuất dữ liệu tự động)
*   **SQL Server** (chỉ yêu cầu nếu bạn chạy pha nạp Database)

---

### ⚙️ Hướng dẫn cài đặt

#### 1. Sao chép kho lưu trữ
```bash
git clone <repository-url>
cd DATN
```

#### 2. Tạo và kích hoạt môi trường ảo (Virtual Environment)
**Windows:**
```powershell
python -m venv .venv
.venv\Scripts\activate
```
**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### 3. Cài đặt các thư viện cần thiết
```bash
pip install -r requirements.txt
```

#### 4. Cấu hình biến môi trường
Tạo tệp `.env` tại thư mục gốc của dự án và điền thông tin cấu hình:
```env
# Thông tin API Kaggle
KAGGLE_API_TOKEN=YOUR_KAGGLE_API_TOKEN_HERE

# Kết nối SQL Server
DB_SERVER=YOUR_SERVER_NAME
DB_NAME=CreditRiskDB
DB_USER=sa
DB_PASS=YOUR_PASSWORD_HERE
```
*Lưu ý: Truy cập [Kaggle Account Settings](https://www.kaggle.com/settings) nhấn chọn **'Your API Token'** -> **Generate New Key** để lấy mã Token.*

---

### 🚀 Khởi chạy Pipeline

Để thực hiện toàn bộ quy trình ELT khép kín (Tải dữ liệu, quét chất lượng, điền khuyết tự động và nạp vào SQL Server):
```bash
# Thiết lập PYTHONPATH và chạy module main
$env:PYTHONPATH = "."
python -m src.main
```

Để chạy pipeline ở **chế độ độc lập** (Chỉ chạy Extract & Transform, không ghi vào Database):
```bash
$env:PYTHONPATH = "."
python -m src.main --skip-db
```

---

### ✨ Các Tính năng Chính
1.  **Trình quét chất lượng dữ liệu (DQ Scanner):** Tự động áp dụng 21 luật nghiệp vụ định nghĩa trong file `DQ_rules.json` và xuất báo cáo chi tiết ra file `docs/03_notes/engineering/data_issues.txt`.
2.  **Sửa lỗi dữ liệu (Data Healing):** Tự động điền dữ liệu khuyết thiếu bằng thuật toán trung vị nhóm (trung vị số năm làm việc theo độ tuổi, trung vị lãi suất theo hạng tín dụng).
3.  **Phân tách dữ liệu:** Tách dữ liệu đầu ra thành các tệp: `df_pass.csv` (dữ liệu sạch hoàn hảo), `df_warning.csv` (dữ liệu đã điền khuyết), và `df_critical.csv` (các hồ sơ lỗi nặng bị cách ly).
4.  **Tự động hóa Kho dữ liệu (DWH):** Tự động kích hoạt Stored Procedure `sp_load_star_schema` trong SQL Server để phân bổ dữ liệu vào các bảng Fact và Dimension.

---

### 🤝 Quy tắc đóng góp phát triển
*   Tuân thủ mô hình thiết kế hướng đối tượng (OOP) đã dựng trong thư mục `src/`.
*   Cập nhật hoặc thêm mới luật kiểm tra dữ liệu thông qua tệp cấu hình `src/etl/extract/DQ_rules.json`.
*   Đảm bảo chạy kiểm thử thành công trước khi đẩy mã nguồn mới.

---
**Chúc bạn làm việc vui vẻ!** 📈
</details>
