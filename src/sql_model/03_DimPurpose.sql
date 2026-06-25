IF OBJECT_ID('DimLoanPurpose', 'U') IS NULL
BEGIN
    CREATE TABLE DimLoanPurpose (
        PurposeKey INT IDENTITY(1,1) PRIMARY KEY,
        LoanIntent VARCHAR(50)
    );
END;
GO