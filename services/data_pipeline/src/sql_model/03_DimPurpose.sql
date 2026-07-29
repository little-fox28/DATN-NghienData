IF OBJECT_ID('dbo.DimLoanPurpose', 'U') IS NOT NULL
    DROP TABLE dbo.DimLoanPurpose;

CREATE TABLE dbo.DimLoanPurpose (
    PurposeKey TINYINT IDENTITY(1,1) PRIMARY KEY,
    LoanIntent VARCHAR(50) NOT NULL
)
WITH(DATA_COMPRESSION = PAGE);
GO