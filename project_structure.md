```text
NghienData-DATN/
├── .gitignore              # Danh sách tệp/thư mục không đưa vào Git
├── GIT_WORKFLOW_GUIDE.md   # Hướng dẫn quy trình làm việc với Git
├── README.md               # Giới thiệu tổng quan về dự án
├── requirements.txt        # Danh sách thư viện Python cần cài đặt
├── project_structure.md    # Mô tả cấu trúc dự án hiện tại
├── data/                   # Khu vực lưu dữ liệu của dự án
│   ├── raw/                # Dữ liệu gốc đầu vào
│   └── output/             # Dữ liệu đầu ra sau xử lý
├── docs/                   # Tài liệu và nội dung tham khảo
│   ├── 01_reports/         # Báo cáo chính thức (Word, PDF)
│   ├── 02_qna/             # Câu hỏi phản biện, bộ hỏi đáp
│   ├── 03_engineering/     # Tài liệu Data Engineering, rules, log
│   ├── 04_feedback/        # Các file ghi nhận ý kiến cá nhân
│   └── 05_assets/          # Tài nguyên tĩnh (Hình ảnh, sơ đồ ERD)
├── notebook/               # Notebook thử nghiệm, EDA hoặc ghi chú nhanh
├── src/                    # Mã nguồn chính của hệ thống
│   ├── etl/                # Luồng trích xuất - biến đổi - nạp dữ liệu
│   │   ├── extract/        # Trích xuất dữ liệu và kiểm tra (monitor_data.py, DQ_rules.json)
│   │   ├── transform/      # Biến đổi và làm sạch dữ liệu
│   │   ├── load.py         # Nạp dữ liệu vào DB
│   │   └── pipeline.py     # Điều phối quy trình
│   ├── sql_model/          # Chứa các file schema SQL Server (Dim/Fact)
│   └── utils/              # Các hàm tiện ích (logger, setup_db)
└── tests/                  # Tệp kiểm thử và script xác nhận chức năng
```