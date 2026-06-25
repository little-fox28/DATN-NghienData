IF OBJECT_ID('DimCustomer', 'U') IS NULL
BEGIN
    CREATE TABLE DimCustomer (
        client_id VARCHAR(50) PRIMARY KEY,
        person_age INT,
        person_income FLOAT,
        person_home_ownership VARCHAR(50),
        gender VARCHAR(20),
        marital_status VARCHAR(50),
        education_level VARCHAR(50),
        employment_type VARCHAR(50)
    );
END;
GO