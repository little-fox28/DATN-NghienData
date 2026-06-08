# 🚀 Credit Risk ELT Pipeline - Quickstart Guide

Welcome to the **Credit Risk Data Engineering Project**. This repository contains a production-ready ELT (Extract, Load, Transform) pipeline designed to ingest, validate, and process credit risk datasets for downstream machine learning.

---

## 🛠 Prerequisites

Before you begin, ensure you have the following installed:
- **Python 3.10+**
- **Git**
- **Kaggle Account** (for data extraction)

---

## ⚙️ Setup Instructions

### 1. Clone the Repository
```bash
git clone <repository-url>
cd DATN
```

### 2. Create a Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Kaggle API
1. Go to your [Kaggle Account Settings](https://www.kaggle.com/settings).
2. Click **'Your API Token'** -> **Generate New Key**.
3. Create a `.env` file in the root directory and add your credentials:
   ```env
   KAGGLE_API_TOKEN=KGAT_...
   ```

---

## 🚀 Running the Pipeline

To execute the complete pipeline (Extract -> Monitor -> Transform):

```bash
# Set PYTHONPATH to root and run main
$env:PYTHONPATH = "."
python -m src.main
```

---

## 📂 Project Structure

- `src/elt/extract/`: Data ingestion logic and the **Data Quality Scanner**.
- `src/elt/transform/`: XLS to CSV conversion and data segregation.
- `data/raw/`: Original files downloaded from Kaggle.
- `data/processed/`: Cleaned and validated datasets (`df_clean.csv`).
- `docs/`: Automated quality reports (`data_issuses.txt`).
- `tests/`: Unit and integration tests.

---

## ✨ Key Features

### 🔍 1. Data Quality Scanner (Extract Phase)
The pipeline automatically scans raw data for business rule violations (Age, Income, Ratios, etc.) and generates a professional report in `docs/data_issuses.txt`.

### 🛡️ 2. Data Segregation (Transform Phase)
Valid records are saved to `data/processed/df_clean.csv`, while invalid records are quarantined in `df_quarantine.csv` with detailed violation notes for debugging.

### ⚡ 3. Smart Conversion
The pipeline intelligently detects if data is already in CSV format to bypass redundant conversion steps, saving time and resources.

### 🔌 4. Seamless Database Integration (Load Phase)
The pipeline automatically connects to **SQL Server** using `SQLAlchemy` and `pyodbc` to load the cleaned dataset (`df_clean.csv`) into the staging table (`stg_loan`). It utilizes **Windows Authentication** for secure, password-less connections and implements a chunking mechanism (`chunksize=1000`) to handle large datasets efficiently without memory bottlenecks.
---
## ⚙️ Setup & Database Connection Guide
To run this pipeline locally and connect it to your SQL Server database, follow these steps:

### Step 1: Install Dependencies
Ensure you have the required Python libraries and ODBC drivers installed:
```bash
pip install pandas sqlalchemy pyodbc python-dotenv
```
### Step 2: Configure Environment Variables
For security reasons (following best practices), database credentials are not hardcoded in the source code.
Create a file named .env in the root directory of the project and define your SQL Server configuration:
# .env file
DB_SERVER=YOUR_SERVER_NAME\SQLEXPRESS
DB_NAME=CreditRiskDB
# =====================================================================
# ⚠️ IMPORTANT SECURITY NOTE:
# This project is configured to use Windows Authentication by default 
# (Trusted_Connection=yes) to avoid hardcoding or exposing passwords.
# 
# DO NOT add DB_USER (e.g., 'sa') or DB_PASS variables here. 
# The pipeline will automatically authenticate using your Windows account.
# =====================================================================
### Step 3: Verify the Staging Data
Open SQL Server Management Studio (SSMS) or DBeaver, connect to your database, and verify the loaded data:

### Step 4: Build the Star Schema (Data Modeling)
Once the clean data is loaded into the staging table (`stg_loan`), the final step is to transform it into a production-ready Star Schema using the provided T-SQL scripts.

1. Open SQL Server Management Studio (SSMS) or DBeaver.
2. Navigate to the `sql_models/` (or `src/sql/`) directory in this repository.
3. Execute the SQL scripts in sequential order to generate the Dimension and Fact tables:
   - `01_DimCustomer.sql`
   - `02_DimLocation.sql`
   - `03_Dimpurpose.sql`
   - `04_DimLoanGrade.sql`
   - `05_Factloan.sql`

## 🤝 Contributing
- Follow the **OOP (Object-Oriented Programming)** style established in the `src/` directory.
- Ensure all business rules are updated in `CreditDataValidator` if requirements change.
- Always check the `docs/data_issuses.txt` after a run to monitor dataset health.

---
**Zui zẻ nha!** 📈
