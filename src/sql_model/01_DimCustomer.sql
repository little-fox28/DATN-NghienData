IF OBJECT_ID('dbo.FactLoan', 'U') IS NOT NULL
BEGIN
    DROP TABLE dbo.FactLoan;
END;
GO

-- Sau khi FactLoan đã chết, chúng ta có thể thoải mái xử lý DimCustomer
IF OBJECT_ID('dbo.DimCustomer', 'U') IS NOT NULL
BEGIN
    IF EXISTS (
        SELECT 1
        FROM sys.tables
        WHERE name = 'DimCustomer'
          AND temporal_type = 2
    )
    BEGIN
        ALTER TABLE dbo.DimCustomer
        SET (SYSTEM_VERSIONING = OFF);
    END;

    DROP TABLE dbo.DimCustomer;
END;
GO

IF OBJECT_ID('dbo.DimCustomerHistory', 'U') IS NOT NULL
BEGIN
    DROP TABLE dbo.DimCustomerHistory;
END;
GO

CREATE TABLE dbo.DimCustomer
(
    CustomerKey INT IDENTITY(1,1) PRIMARY KEY,
    client_id VARCHAR(20) NOT NULL UNIQUE,
    person_age TINYINT,
    person_income DECIMAL(15,2),
    person_home_ownership VARCHAR(20),
    gender VARCHAR(10),
    marital_status VARCHAR(15),
    education_level VARCHAR(20),
    employment_type VARCHAR(20),
    cb_person_default_on_file VARCHAR(5),
    cb_person_cred_hist_length TINYINT,

    -- System-versioned columns
    SysStartTime DATETIME2
        GENERATED ALWAYS AS ROW START
        HIDDEN NOT NULL,
    SysEndTime DATETIME2
        GENERATED ALWAYS AS ROW END
        HIDDEN NOT NULL,
    PERIOD FOR SYSTEM_TIME
    (
        SysStartTime,
        SysEndTime
    )
)
WITH
(
    SYSTEM_VERSIONING = ON
    (
        HISTORY_TABLE = dbo.DimCustomerHistory
    ),

    DATA_COMPRESSION = PAGE
);
GO