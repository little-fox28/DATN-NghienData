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
│   │   ├── models/                 # Lưu trữ artifacts mô hình ML và encoders (.pkl, .joblib)
│   │   ├── models_readable/        # Chứa bản dịch (JSON/TXT) của mô hình để dễ đọc
│   │   ├── reports/                # Báo cáo kết quả ML (thông số kỹ thuật, biểu đồ)
│   │   ├── src/
│   │   │   └── machine_learning/   # Core ML (Preprocess, Feature, Train, Eval, Predict)
│   │   │       ├── config.yaml     # File config siêu tham số cho nhiều task (credit_risk, v.v)
│   │   │       ├── config.py       # Tự động parse đường dẫn và config yaml
│   │   │       ├── pipeline.py     # End-to-end pipeline huấn luyện mô hình ML
│   │   │       └── predict.py      # Tầng Inference (Dự đoán)
│   │   └── requirements.txt        # Dependencies riêng cho Machine Learning
│   ├── api_server/                 # Domain 3: Backend REST API Service (FastAPI)
│   │   ├── app/
│   │   │   ├── config.py           # Cấu hình server FastAPI
│   │   │   └── main.py             # Entry point API cho Web/App
│   │   └── requirements.txt        # Dependencies riêng cho API Server
│   └── web_app/                    # Domain 4: Frontend Web Application (React + Vite)
│       ├── src/                    # Mã nguồn chính
│       │   ├── api/                # Cấu hình HTTP Clients gọi về Backend API
│       │   ├── assets/             # Hình ảnh, biểu tượng, file tĩnh
│       │   ├── components/         # React Components tái sử dụng (Gauge, UI)
│       │   ├── contexts/           # React Contexts (Quản lý Theme, Cấu hình)
│       │   ├── i18n/               # Cấu hình đa ngôn ngữ (locales: en.json, vi.json)
│       │   ├── layouts/            # Component Bố cục (Sidebar, Header)
│       │   ├── pages/              # Màn hình chính (Dashboard, Loan Application)
│       │   └── types/              # Type/Interface TypeScript
│       └── package.json            # Packages cho Frontend
├── shared/                         # Tiện ích & Hợp đồng dùng chung giữa các services
│   └── utils/                      # Logger, SQL Connector, Setup DB
├── data/                           # Khu vực lưu trữ dữ liệu dự án
│   ├── raw/                        # Dữ liệu gốc nguyên bản
│   └── processed/                  # Dữ liệu đã qua làm sạch, biến đổi
├── docs/                           # Tài liệu nghiệp vụ và thiết kế hệ thống
├── notebook/                       # Jupyter notebook phục vụ phân tích EDA
└── tests/                          # Script kiểm thử tự động hệ thống
```