IF OBJECT_ID('DimLoanGrade', 'U') IS NULL
BEGIN
    CREATE TABLE DimLoanGrade (
        GradeKey INT IDENTITY(1,1) PRIMARY KEY,
        LoanGrade VARCHAR(10)
    );
END;
GO