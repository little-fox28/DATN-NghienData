-- ============================================================
-- 07_stg_predictions.sql
-- Bảng staging cho file predictions.csv từ ML Engine.
-- Phản ánh đúng cấu trúc predictions.csv (15 cột).
-- ============================================================

IF OBJECT_ID('stg_predictions', 'U') IS NOT NULL
    DROP TABLE stg_predictions;

CREATE TABLE stg_predictions (
    -- Định danh
    client_id                VARCHAR(20),
    is_test                  TINYINT,          -- 0 = train | 1 = test

    -- 10 Features (WoE input)
    loan_grade               VARCHAR(5),
    person_home_ownership    VARCHAR(20),
    cb_person_default_on_file VARCHAR(5),
    loan_intent              VARCHAR(30),
    loan_to_income_ratio     DECIMAL(12,9),
    debt_to_income_ratio     DECIMAL(12,9),
    person_income            DECIMAL(15,2),
    loan_int_rate            DECIMAL(9,4),
    person_emp_length        DECIMAL(9,2),
    loan_amnt                DECIMAL(15,2),

    -- Kết quả dự đoán
    pd_score                 DECIMAL(12,9),    -- Xác suất vỡ nợ
    predicted_class          TINYINT,          -- 0=no default, 1=default
    actual                   TINYINT           -- loan_status thực tế
);
GO
