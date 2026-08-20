-- ============================================================
-- 08_FactMLPrediction.sql
-- Bảng Fact chứa kết quả dự đoán của mô hình ML (XGBoost + WoE).
-- Nối với DimCustomer qua CustomerKey.
-- Tableau JOIN: FactMLPrediction → DimCustomer → FactLoan
-- ============================================================

IF OBJECT_ID(N'dbo.FactMLPrediction', N'U') IS NOT NULL
BEGIN
    DROP TABLE dbo.FactMLPrediction;
END;
GO

CREATE TABLE dbo.FactMLPrediction
(
    PredictionKey    INT IDENTITY(1,1) NOT NULL,
    CustomerKey      INT NOT NULL,              -- FK → DimCustomer
    pd_score         DECIMAL(9,6) NOT NULL,     -- Xác suất vỡ nợ (PD score)
    predicted_class  TINYINT NOT NULL,          -- Dự báo: 0=no default, 1=default
    actual           TINYINT NULL,              -- Thực tế loan_status (NULL nếu không có)
    is_test          TINYINT NOT NULL,          -- 0 = tập train | 1 = tập test

    -- Primary Key
    CONSTRAINT PK_FactMLPrediction
        PRIMARY KEY NONCLUSTERED (PredictionKey),

    -- Foreign Key → DimCustomer
    CONSTRAINT FK_FactMLPrediction_Customer
        FOREIGN KEY (CustomerKey)
        REFERENCES dbo.DimCustomer(CustomerKey)
);
GO

-- Columnstore Index để tăng tốc OLAP aggregation trên Tableau
CREATE CLUSTERED COLUMNSTORE INDEX CCI_FactMLPrediction
ON dbo.FactMLPrediction;
GO
