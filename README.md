# DATN - Phân tích rủi ro tài chính

## Cài đặt môi trường

> Yêu cầu: **Python 3.10+** đã được cài sẵn trên máy

---

### Bước 1: tạo môi trường ảo 

**Windows:**
```cmd
py -3.11 -m venv .venv
```

**Linux / macOS:**
```bash
python3.11 -m venv .venv
```

---

### Bước 2: kích hoạt môi trường ảo

**Windows (Command Prompt):**
```cmd
.venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

> Nếu PowerShell báo lỗi, chạy lệnh này trước rồi kích hoạt lại:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

**Linux / macOS:**
```bash
source .venv/bin/activate
```

Kích hoạt thành công sẽ thấy `(.venv)` ở đầu folder dự án.

---

### Bước 3: cài đặt thư viện
**Cài đặt toàn bộ thư viện của dự án**
```bash
pip install -r requirements.txt
```
**Hoặc có thể cài đặt thủ công các gói làm việc:**
```bash
pip install python-dotenv kaggle pandas
```

---

### Bước 4: tắt môi trường ảo (sau khi hoàn tất công việc)

```bash
deactivate
```

---

### Cấu trúc dự án

```Text
ghienData-DATN/
├── .gitignore              # Danh sách tệp/thư mục không đưa vào Git
├── GIT_WORKFLOW_GUIDE.md   # Hướng dẫn quy trình làm việc với Git
├── README.md               # Giới thiệu tổng quan về dự án
├── requirements.txt        # Danh sách thư viện Python cần cài đặt
├── project_structure.md    # Mô tả cấu trúc dự án hiện tại
├── data/                   # Khu vực lưu dữ liệu của dự án
│   └── raw/                # Dữ liệu gốc đầu vào, ví dụ file .xls
├── docs/                   # Tài liệu và nội dung tham khảo
│   └── Ykien/              # Các file ghi nhận ý kiến
├── notebook/               # Notebook thử nghiệm, EDA hoặc ghi chú nhanh
│   └── .gitkeep
├── src/                    # Mã nguồn chính của hệ thống
│   ├── __init__.py
│   └── elt/                # Luồng trích xuất - biến đổi - nạp dữ liệu
│       ├── __init__.py
│       ├── extract.py      # Trích xuất dữ liệu từ nguồn
│       ├── transform.py     # Biến đổi và làm sạch dữ liệu
│       ├── load.py         # Nạp dữ liệu đã xử lý
│       └── pipeline.py     # Điều phối toàn bộ quy trình ELT
└── tests/                  # Tệp kiểm thử và script xác nhận chức năng
    └── .gitkeep
```
---

### Lưu ý 

- Thư mục `.venv` không được push lên git (đã có trong `.gitignore`).
- Mỗi thành viên tự tạo `.venv` trên máy tính của mình theo hướng dẫn trên .

### Hướng dẫn sử dụng pipeline được chỉ dẫn ở mục QUICKSTART.md
