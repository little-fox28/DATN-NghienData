IF OBJECT_ID('dbo.DimLoanGrade', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.DimLoanGrade (
        GradeKey TINYINT IDENTITY(1,1) PRIMARY KEY,
        LoanGrade VARCHAR(10)
    );
END;
GO