CREATE OR ALTER PROCEDURE sp_load_star_schema
AS
BEGIN
    SET NOCOUNT ON;
    TRUNCATE TABLE FactLoan;
    -- BƯỚC 1: CẬP NHẬT DIM CUSTOMER 
    INSERT INTO DimCustomer (client_id, person_age, person_income, person_home_ownership, gender, marital_status, education_level, employment_type)
    SELECT client_id, MAX(person_age), MAX(person_income), MAX(person_home_ownership), MAX(gender), MAX(marital_status), MAX(education_level), MAX(employment_type)
    FROM stg_loan
    WHERE client_id IS NOT NULL 
      AND client_id NOT IN (SELECT client_id FROM DimCustomer)
    GROUP BY client_id;

    -- BƯỚC 2: CẬP NHẬT DIM LOCATION 
    INSERT INTO DimLocation (Country, State, City, city_latitude, city_longitude)
    SELECT DISTINCT country, state, city, MAX(city_latitude), MAX(city_longitude)
    FROM stg_loan s
    WHERE (country IS NOT NULL OR state IS NOT NULL OR city IS NOT NULL)
      AND NOT EXISTS (
          SELECT 1 FROM DimLocation d 
          WHERE ISNULL(d.Country,'') = ISNULL(s.country,'') 
            AND ISNULL(d.State,'') = ISNULL(s.state,'') 
            AND ISNULL(d.City,'') = ISNULL(s.city,'')
      )
    GROUP BY country, state, city;

    -- BƯỚC 3: CẬP NHẬT DIM LOAN PURPOSE
    INSERT INTO DimLoanPurpose (LoanIntent)
    SELECT DISTINCT loan_intent FROM stg_loan
    WHERE loan_intent IS NOT NULL 
      AND loan_intent NOT IN (SELECT LoanIntent FROM DimLoanPurpose);

    -- BƯỚC 4: CẬP NHẬT DIM LOAN GRADE
    INSERT INTO DimLoanGrade (LoanGrade)
    SELECT DISTINCT loan_grade FROM stg_loan
    WHERE loan_grade IS NOT NULL 
      AND loan_grade NOT IN (SELECT LoanGrade FROM DimLoanGrade);

    -- BƯỚC 5: NẠP DỮ LIỆU VÀO FACT LOAN
    INSERT INTO FactLoan (
        CustomerKey, LocationKey, PurposeKey, GradeKey,
        LoanAmount, InterestRate, LoanTerm, LoanPercentIncome,
        LoanToIncomeRatio, DebtToIncomeRatio, CreditUtilization,
        PersonEmpLength, PastDelinquencies, OtherDebt, OpenAccounts, LoanStatus, Status
    )
    SELECT 
        s.client_id,
        dl.LocationKey,
        dp.PurposeKey,
        dg.GradeKey,
        s.loan_amnt,
        s.loan_int_rate,
        s.loan_term_months,
        s.loan_percent_income,
        s.loan_to_income_ratio,
        s.debt_to_income_ratio,
        s.credit_utilization_ratio,
        s.person_emp_length,
        s.past_delinquencies,
        s.other_debt,
        s.open_accounts,
        s.loan_status,
        s.status
    FROM stg_loan s
    LEFT JOIN DimCustomer c ON s.client_id = c.client_id
    LEFT JOIN DimLocation dl ON ISNULL(s.country,'') = ISNULL(dl.Country,'') 
                            AND ISNULL(s.state,'') = ISNULL(dl.State,'') 
                            AND ISNULL(s.city,'') = ISNULL(dl.City,'')
    LEFT JOIN DimLoanPurpose dp ON s.loan_intent = dp.LoanIntent
    LEFT JOIN DimLoanGrade dg ON s.loan_grade = dg.LoanGrade;

END;