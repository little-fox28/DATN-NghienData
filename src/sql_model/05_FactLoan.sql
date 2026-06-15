IF OBJECT_ID('FactLoan', 'U') IS NOT NULL DROP TABLE FactLoan;

CREATE TABLE FactLoan (
    FactLoanKey INT IDENTITY(1,1) PRIMARY KEY,
    CustomerKey VARCHAR(50) FOREIGN KEY REFERENCES DimCustomer(client_id),
    LocationKey INT FOREIGN KEY REFERENCES DimLocation(LocationKey),
    PurposeKey INT FOREIGN KEY REFERENCES DimLoanPurpose(PurposeKey),
    GradeKey INT FOREIGN KEY REFERENCES DimLoanGrade(GradeKey),
    
    LoanAmount FLOAT,
    InterestRate FLOAT,
    LoanTerm INT,
    LoanPercentIncome FLOAT,
    LoanToIncomeRatio FLOAT,
    DebtToIncomeRatio FLOAT,
    CreditUtilization FLOAT,
    PersonEmpLength INT,
    PastDelinquencies INT,
    OtherDebt FLOAT,
    OpenAccounts INT,
    LoanStatus INT,
    Status VARCHAR(50)
);
GO