```text
NghienData-DATN/
├── .gitignore              # Danh sách tệp/thư mục không đưa vào Git
├── GIT_WORKFLOW_GUIDE.md   # Hướng dẫn quy trình làm việc với Git
├── README.md               # Giới thiệu tổng quan về dự án
├── requirements.txt        # Danh sách thư viện Python cần cài đặt
├── project_structure.md    # Mô tả cấu trúc dự án hiện tại
├── data/                   # Khu vực lưu dữ liệu của dự án
│   └── raw/                # Dữ liệu gốc đầu vào, ví dụ file .xls
├── docs/                   # Tài liệu và nội dung tham khảo
│   ├── 01_reports/         # Báo cáo và tài liệu chính (file Word)
│   ├── 02_design_assets/   # Sơ đồ thiết kế hệ thống và ERD
│   ├── 03_team_feedback/   # Ý kiến đóng góp từ các thành viên trong nhóm
│   ├── 04_qna/             # Câu hỏi và tài liệu chuẩn bị phản biện
│   ├── 05_data_quality/    # Nhật ký lỗi và chất lượng dữ liệu đầu vào
│   └── 06_notes/           # Ghi chú kỹ thuật, DE rules
├── notebook/               # Notebook thử nghiệm, EDA hoặc ghi chú nhanh
│   └── .gitkeep
├── src/                    # Mã nguồn chính của hệ thống
│   ├── __init__.py
│   └── etl/                # Luồng trích xuất - biến đổi - nạp dữ liệu
│       ├── __init__.py
│       ├── extract.py      # Trích xuất dữ liệu từ nguồn
│       ├── transform.py     # Biến đổi và làm sạch dữ liệu
│       ├── load.py         # Nạp dữ liệu đã xử lý
│       └── pipeline.py     # Điều phối toàn bộ quy trình ELT
└── tests/                  # Tệp kiểm thử và script xác nhận chức năng
    └── .gitkeep
```