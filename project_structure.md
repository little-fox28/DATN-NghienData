```text
DATN/
├── .env                            # Biến môi trường và cấu hình bảo mật
├── .gitignore                      # Danh sách tệp/thư mục không đưa vào Git
├── GIT_WORKFLOW_GUIDE.md           # Hướng dẫn quy trình làm việc với Git
├── QUICKSTART.md                   # Hướng dẫn khởi chạy nhanh dự án
├── README.md                       # Giới thiệu tổng quan về dự án
├── project_structure.md            # Mô tả cấu trúc dự án hiện tại
├── requirements.txt                # Danh sách thư viện Python dùng chung
├── services/                       # Các dịch vụ phân hệ domain riêng biệt
│   ├── data_pipeline/              # Domain 1: Data Engineering Service
│   │   ├── src/
│   │   │   ├── etl/                # Extract - Transform - Load pipeline
│   │   │   └── sql_model/          # Schema SQL Server (Dim/Fact)
│   │   ├── main.py                 # Entry point chạy ETL Pipeline
│   │   └── requirements.txt        # Dependencies riêng cho Data Engineering
│   ├── ml_engine/                  # Domain 2: Machine Learning Engine
│   │   ├── src/
│   │   │   └── machine_learning/   # Core ML (Preprocess, Feature, Train, Eval, Predict)
│   │   └── requirements.txt        # Dependencies riêng cho Machine Learning
│   ├── api_server/                 # Domain 3: Backend REST API Service
│   │   ├── app/
│   │   │   ├── config.py           # Cấu hình server FastAPI
│   │   │   └── main.py             # Entry point API cho Web/App
│   │   └── requirements.txt        # Dependencies riêng cho API Server
│   └── web_app/                    # Domain 4: Frontend Web Application
│       ├── src/                    # App React + TypeScript + Vite
│       └── package.json            # Packages cho Frontend
├── shared/                         # Tiện ích & Hợp đồng dùng chung giữa các services
│   └── utils/                      # Logger, SQL Connector, Setup DB
├── data/                           # Khu vực lưu trữ dữ liệu dự án (raw, processed, output)
├── docs/                           # Tài liệu nghiệp vụ và thiết kế hệ thống
├── models/                         # Lưu trữ artifacts mô hình ML và encoders
├── notebook/                       # Jupyter notebook phục vụ trực quan hóa và phân tích ML
├── reports/                        # Báo cáo đánh giá mô hình ML và metrics
└── tests/                          # Script kiểm thử tự động
```