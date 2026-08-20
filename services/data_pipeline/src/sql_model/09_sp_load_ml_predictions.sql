-- ============================================================
-- 09_sp_load_ml_predictions.sql
-- Stored Procedure nạp dữ liệu từ stg_predictions → FactMLPrediction.
--
-- Luồng thực thi:
--   1. Truncate FactMLPrediction
--   2. JOIN stg_predictions với DimCustomer qua client_id → lấy CustomerKey
--   3. INSERT vào FactMLPrediction
--
-- Gọi sau khi đã bulk insert predictions.csv vào stg_predictions.
-- ============================================================

CREATE OR ALTER PROCEDURE sp_load_ml_predictions
AS
BEGIN
    SET NOCOUNT ON;

    -- BƯỚC 1: Xoá dữ liệu cũ trong FactMLPrediction
    TRUNCATE TABLE dbo.FactMLPrediction;

    -- BƯỚC 2: Nạp dữ liệu từ staging vào Fact
    INSERT INTO dbo.FactMLPrediction (
        CustomerKey,
        is_test,
        pd_score,
        predicted_class,
        actual
    )
    SELECT
        c.CustomerKey,
        s.is_test,
        s.pd_score,
        s.predicted_class,
        s.actual
    FROM stg_predictions s
    INNER JOIN dbo.DimCustomer c
        ON s.client_id = c.client_id
    WHERE s.client_id IS NOT NULL
      AND s.pd_score  IS NOT NULL;

    -- BƯỚC 3: Log kết quả
    DECLARE @inserted INT = @@ROWCOUNT;
    PRINT CONCAT('sp_load_ml_predictions: Đã nạp ', @inserted, ' bản ghi vào FactMLPrediction.');
END;
GO
