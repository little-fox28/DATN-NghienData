```text
DATN/
├── .env                            # Biến môi trường và cấu hình bảo mật
├── .gitignore                      # Danh sách tệp/thư mục không đưa vào Git
├── GIT_WORKFLOW_GUIDE.md           # Hướng dẫn quy trình làm việc với Git
├── QUICKSTART.md                   # Hướng dẫn khởi chạy nhanh dự án
├── README.md                       # Giới thiệu tổng quan về dự án
├── project_structure.md            # Mô tả cấu trúc dự án hiện tại
├── requirements.txt                # Danh sách thư viện Python cần cài đặt
├── backend/                        # Dịch vụ Backend API (FastAPI)
│   ├── config.py                   # Cấu hình server và kết nối CSDL
│   └── main.py                     # Entry point API thu thập và dự báo khoản vay
├── data/                           # Khu vực lưu trữ dữ liệu dự án
│   ├── raw/                        # Dữ liệu thô đầu vào
│   ├── processed/                  # Dữ liệu đã làm sạch cho ML
│   └── output/                     # Dữ liệu đầu ra sau ETL
├── docs/                           # Tài liệu nghiệp vụ và thiết kế hệ thống
│   ├── 01_reports/                 # Báo cáo chính thức (Word, PDF)
│   ├── 02_qna/                     # Bộ câu hỏi và tài liệu phản biện
│   ├── 03_notes/                   # Ghi chú kỹ thuật và nghiệp vụ
│   │   ├── business/               # Tài liệu nghiệp vụ, từ điển dữ liệu
│   │   └── engineering/            # Data Engineering rules, log sự cố
│   ├── 04_feedback/                # Ghi nhận ý kiến đóng góp
│   └── 05_assets/                  # Tài nguyên tĩnh (Hình ảnh, sơ đồ ERD)
├── models/                         # Lưu trữ artifacts mô hình ML và encoders
├── notebook/                       # Jupyter notebook phục vụ trực quan hóa và phân tích ML
│   ├── 01_credit_risk.ipynb        # Trực quan hóa & trả lời Bài toán 1 (Khả năng vỡ nợ)
│   ├── ...
├── reports/                        # Báo cáo đánh giá mô hình ML và biểu đồ
│   ├── training_metrics.json       # Chỉ số đánh giá mô hình
├── src/                            # Mã nguồn chính của hệ thống
│   ├── etl/                        # Luồng trích xuất - biến đổi - nạp dữ liệu (ELT)
│   │   ├── extract/                # Trích xuất dữ liệu và kiểm tra DQ
│   │   ├── transform/              # Biến đổi và làm sạch dữ liệu
│   │   ├── load.py                 # Nạp dữ liệu vào CSDL
│   │   └── pipeline.py             # Điều phối quy trình ELT
│   ├── machine_learning/           # Lõi tính toán Machine Learning (Credit Risk Engine)
│   │   ├── config.yaml             # Cấu hình siêu tham số và đường dẫn ML
│   │   ├── config.py               # Module đọc cấu hình ML
│   │   ├── preprocessing.py        # Tiền xử lý dữ liệu và chia tập train/test
│   │   ├── features.py             # Mã hóa đặc trưng (OrdinalEncoder)
│   │   ├── train.py                # Huấn luyện mô hình XGBoost
│   │   ├── evaluate.py             # Đánh giá mô hình (AUC, Gini, KS)
│   │   ├── predict.py              # Engine tính điểm tín dụng (Credit Score)
│   │   └── pipeline.py             # Kịch bản chạy End-to-End ML Pipeline
│   ├── sql_model/                  # Định nghĩa schema CSDL SQL Server (Dim/Fact)
│   └── utils/                      # Tiện ích dùng chung (Logger, DB Setup)
└── tests/                          # Script kiểm thử tự động
```