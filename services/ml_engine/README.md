# 🧠 ML Engine — Credit Risk & Multi-Task Machine Learning Service

Thành phần lõi tính toán và dự báo Machine Learning dành cho Phân hệ Quản trị Rủi ro Tín dụng & Ngân hàng Tiêu dùng (**Credit Risk & Retail Banking System**). 

Phân hệ này được thiết kế theo chuẩn **OOP (Object-Oriented Programming)** và mô hình **Config-Driven Architecture**, cho phép mở rộng và vận hành đồng thời nhiều bài toán trí tuệ nhân tạo (Credit Risk, Loan Intent, Interest Pricing, Regional Demand, Collection Strategy) mà không cần chỉnh sửa lại mã nguồn lõi.

---

## 📌 Tính năng Nổi bật (Core Features)

1. **Kiến trúc Hướng đối tượng (OOP Architecture):**
   - Phân tách rõ ràng các tầng trách nhiệm: `DataPreprocessor`, `FeatureEngineer`, `ModelTrainer`, `ModelEvaluator`, `ModelPredictor`.
   - Dễ dàng kiểm thử đơn vị (Unit Test), mở rộng và bảo trì độc lập.

2. **Cấu hình Đa Bài toán (Multi-Task Configuration Engine):**
   - Quản lý toàn bộ thông số siêu tham số (Hyperparameters), đường dẫn dữ liệu, danh sách đặc trưng và thang điểm Scorecard thông qua file cấu hình trung tâm `config.yaml`.
   - Hỗ trợ chạy các tác vụ ML khác nhau chỉ bằng cách truyền cờ `--task <task_name>`.

3. **Quy trình Mã hóa & Xử lý Đặc trưng Chuẩn Ngân hàng:**
   - **Xử lý Dữ liệu khuyết & Outliers:** Điền giá trị trống tự động theo Median và lọc ngoại lệ theo logic nghiệp vụ tài chính.
   - **Mã hóa biến Phân loại (Categorical Encoding):** Tích hợp `OrdinalEncoder` với cơ chế `handle_unknown='use_encoded_value'`, đảm bảo tính nhất quán tuyệt đối giữa tập Train và tập Inference thực tế.

4. **Đánh giá Mô hình Đa chiều (Financial ML Evaluation):**
   - Đo lường sức mạnh phân loại thông qua các chỉ số tiêu chuẩn ngành ngân hàng:
     - **AUC-ROC** (Area Under the ROC Curve)
     - **Gini Coefficient** ($Gini = 2 \times AUC - 1$)
     - **KS Statistic** (Kolmogorov–Smirnov Distance: $\max |TPR - FPR|$)
     - **Classification Report** (Precision, Recall, F1-Score)
   - Tự động đóng gói tọa độ ROC và Feature Importance ra JSON phục vụ trực quan hóa tương tác trên Jupyter Notebook hoặc Dashboard.

5. **Chuyển đổi Điểm Tín dụng (Standard Credit Scorecard):**
   - Tích hợp công thức quy đổi từ **Xác suất Vỡ nợ (PD - Probability of Default)** sang **Điểm Tín dụng (Credit Score 300 - 850)** theo tiêu chuẩn Scorecard:
     $$\text{Score} = \text{Target Score} - \text{Factor} \times \ln\left(\frac{\text{Odds}}{\text{Target Odds}}\right)$$
   - Phân hạng rủi ro (Risk Tiers: LOW, MEDIUM, HIGH, CRITICAL) và đưa ra phán quyết tự động (APPROVED, MANUAL_REVIEW, REJECTED).

---

## 🏗️ Cấu trúc Thư mục Service (`services/ml_engine/`)

```text
services/ml_engine/
├── src/
│   └── machine_learning/
│       ├── __init__.py          # Public API export các OOP Classes
│       ├── config.yaml          # File cấu hình trung tâm cho tất cả bài toán ML
│       ├── config.py            # Module nạp và chuyển đổi đường dẫn tuyệt đối
│       ├── preprocessing.py     # Lớp DataPreprocessor (Làm sạch & Train/Test split)
│       ├── features.py          # Lớp FeatureEngineer (Fit/Transform Categorical Encoders)
│       ├── train.py             # Lớp ModelTrainer (Huấn luyện XGBoost Classifier)
│       ├── evaluate.py          # Lớp ModelEvaluator (Tính AUC, Gini, KS & Export JSON)
│       ├── predict.py           # Lớp ModelPredictor (Inference & Scorecard Engine)
│       └── pipeline.py          # Lớp MLPipeline (Điều phối End-to-End Execution)
└── requirements.txt             # Danh sách dependencies dành riêng cho ML Engine
```

---

## ⚙️ Cấu hình Bài toán (`config.yaml`)

File `config.yaml` định nghĩa thông số cho từng bài toán ML. Ví dụ cho bài toán **Credit Risk (`credit_risk`)**:

```yaml
global:
  raw_data_path: "data/raw/Credit%20Risk%20Data.csv"

tasks:
  credit_risk:
    target_column: "loan_status"
    id_column: "id"
    test_size: 0.2
    random_state: 42
    fillna_median_cols:
      - "person_emp_length"
      - "loan_int_rate"
    categorical_cols:
      - "person_home_ownership"
      - "loan_intent"
      - "loan_grade"
      - "cb_person_default_on_file"
      - "gender"
      - "marital_status"
      - "education_level"
      - "employment_type"
    params:
      n_estimators: 200
      max_depth: 5
      learning_rate: 0.05
      random_state: 42
    model_artifact: "models/credit_risk_model.joblib"
    encoder_artifact: "models/woe_binner.pkl"
    metrics_output: "reports/training_metrics.json"
    figures_dir: "reports/figures"
    scorecard:
      target_score: 600
      target_odds: 50
      pdo: 20

tasks:
  ...
```

---

## 🚀 Hướng dẫn Sử dụng (Usage Guide)

### 1. Cài đặt môi trường
Đảm bảo bạn đã kích hoạt virtual environment và cài đặt các thư viện cần thiết:
```bash
pip install -r services/ml_engine/requirements.txt
```

### 2. Huấn luyện End-to-End Pipeline (Train & Evaluate)
Chạy pipeline từ thư mục gốc dự án (`DATN/`):

```bash
# Huấn luyện bài toán Dự báo Vỡ nợ (Credit Risk)
python -m services.ml_engine.src.machine_learning.pipeline --task credit_risk

# Sử dụng dữ liệu đã làm sạch trước đó (Bỏ qua bước Preprocessing)
python -m services.ml_engine.src.machine_learning.pipeline --task credit_risk --skip-preprocessing
```

#### Output Log dự kiến:
```text
2026-07-28 14:00:00 - __main__ - INFO - STARTING ML PIPELINE FOR TASK: CREDIT_RISK
2026-07-28 14:00:00 - __main__ - INFO - [STEP 1/4] Preprocessing data...
2026-07-28 14:00:01 - __main__ - INFO - [STEP 2/4] Encoding categorical features...
2026-07-28 14:00:02 - __main__ - INFO - [STEP 3/4] Training model for task: credit_risk...
2026-07-28 14:00:03 - __main__ - INFO - [STEP 4/4] Evaluating model...
2026-07-28 14:00:03 - services.ml_engine.src.machine_learning.evaluate - INFO -   AUC-ROC : 0.9488
2026-07-28 14:00:03 - services.ml_engine.src.machine_learning.evaluate - INFO -   Gini    : 0.8976
2026-07-28 14:00:03 - services.ml_engine.src.machine_learning.evaluate - INFO -   KS Stat : 0.7588
2026-07-28 14:00:03 - __main__ - INFO - PIPELINE COMPLETED SUCCESSFULLY!
```

---

### 3. Sử dụng Lớp Predictor trong Code (Python API)

Dưới đây là ví dụ gọi lớp `ModelPredictor` để tính điểm tín dụng cho 1 hồ sơ khách hàng đơn lẻ:

```python
from services.ml_engine.src.machine_learning.config import get_task_config
from services.ml_engine.src.machine_learning.predict import ModelPredictor

# 1. Nạp cấu hình bài toán
config = get_task_config("credit_risk")

# 2. Khởi tạo Predictor Engine
predictor = ModelPredictor(config)

# 3. Hồ sơ khách hàng xin vay mẫu
applicant_data = {
    "person_age": 28,
    "person_income": 65000,
    "person_home_ownership": "RENT",
    "person_emp_length": 4.0,
    "loan_intent": "PERSONAL",
    "loan_grade": "B",
    "loan_amnt": 10000,
    "loan_int_rate": 11.14,
    "loan_percent_income": 0.15,
    "cb_person_default_on_file": "N",
    "cb_person_cred_hist_length": 3,
    "gender": "MALE",
    "marital_status": "SINGLE",
    "education_level": "BACHELOR",
    "employment_type": "FULL_TIME",
    "loan_to_income_ratio": 0.15,
    "debt_to_income_ratio": 0.25,
    "credit_utilization_ratio": 0.35,
    "past_delinquencies": 0
}

# 4. Chấm điểm tín dụng
result = predictor.score_single(applicant_data)
print(result)
```

#### Output Kết quả:
```json
{
  "pd_score": 0.1245,
  "credit_score": 682,
  "risk_tier": "MEDIUM",
  "decision": "APPROVED"
}
```

---

## 📊 Kết quả Sản phẩm (Artifacts Output)

Sau khi pipeline chạy thành công, các sản phẩm sau sẽ được tự động sinh ra tại thư mục chung của dự án:
- **`models/credit_risk_model.joblib`**: Mô hình XGBoost đã huấn luyện.
- **`models/woe_binner.pkl`**: Bộ mã hóa `OrdinalEncoder` đã fit với dữ liệu train.
- **`data/processed/df_clean.csv`**: Tập dữ liệu đã được làm sạch và loại bỏ outlier.
- **`reports/training_metrics.json`**: Chỉ số đo lường (AUC, Gini, KS, Report) và tọa độ vẽ biểu đồ ROC/Feature Importance.

---

## 🛡️ Tiêu chuẩn Đánh giá Rủi ro (Risk Decision Thresholds)

| PD Score Range | Risk Tier | Phán quyết (Decision) | Ý nghĩa Nghiệp vụ |
| :--- | :---: | :---: | :--- |
| **0.00% - 9.99%** | `LOW` | **APPROVED** | Rủi ro rất thấp. Phê duyệt tự động. |
| **10.00% - 24.99%** | `MEDIUM` | **APPROVED** | Rủi ro trung bình. Phê duyệt với hạn mức tiêu chuẩn. |
| **25.00% - 39.99%** | `HIGH` | **MANUAL_REVIEW** | Rủi ro cao. Chuyển Cán bộ Thẩm định thủ công. |
| **>= 40.00%** | `CRITICAL` | **REJECTED** | Rủi ro cực cao. Từ chối cấp tín dụng tự động. |
