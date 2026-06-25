IF OBJECT_ID('DimLocation', 'U') IS NULL
BEGIN
    CREATE TABLE DimLocation (
        LocationKey INT IDENTITY(1,1) PRIMARY KEY,
        Country VARCHAR(100),
        State VARCHAR(100),
        City VARCHAR(100),
        city_latitude DECIMAL(10,6),
        city_longitude DECIMAL(10,6)
    );
END;
GO