IF OBJECT_ID('FactLoan', 'U') IS NOT NULL 
    DROP TABLE FactLoan;

CREATE TABLE FactLoan
(
    FactLoanKey INT IDENTITY(1,1) NOT NULL,
    CustomerKey INT NOT NULL,
    LocationKey INT,
    PurposeKey TINYINT,
    GradeKey TINYINT,
    LoanAmount DECIMAL(15,2),
    InterestRate DECIMAL(9,6),
    LoanTerm TINYINT,
    LoanPercentIncome DECIMAL(9,6),
    LoanToIncomeRatio DECIMAL(9,6),
    DebtToIncomeRatio DECIMAL(9,6),
    CreditUtilization DECIMAL(9,6),
    PastDelinquencies TINYINT,
    OtherDebt DECIMAL(15,2),
    OpenAccounts TINYINT,
    LoanStatus TINYINT,
    Status VARCHAR(50),

    -- Primary Key must be NONCLUSTERED when Clustered Columnstore Index is used
    CONSTRAINT PK_FactLoan
        PRIMARY KEY NONCLUSTERED (FactLoanKey),

    -- Foreign Keys
    CONSTRAINT FK_FactLoan_Customer
        FOREIGN KEY (CustomerKey)
        REFERENCES DimCustomer(CustomerKey),

    CONSTRAINT FK_FactLoan_Location
        FOREIGN KEY (LocationKey)
        REFERENCES DimLocation(LocationKey),

    CONSTRAINT FK_FactLoan_Purpose
        FOREIGN KEY (PurposeKey)
        REFERENCES DimLoanPurpose(PurposeKey),

    CONSTRAINT FK_FactLoan_Grade
        FOREIGN KEY (GradeKey)
        REFERENCES DimLoanGrade(GradeKey)
);
-- Create Clustered Columnstore Index for maximum OLAP aggregation speed
CREATE CLUSTERED COLUMNSTORE INDEX CCI_FactLoan ON FactLoan;
GO