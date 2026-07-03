IF OBJECT_ID('DimLocation', 'U') IS  NOT NULL
    DROP TABLE DimLocation;

CREATE TABLE DimLocation (
    LocationKey INT IDENTITY(1,1) PRIMARY KEY,
    Country VARCHAR(50),
    State VARCHAR(50),
    City VARCHAR(50),
    city_latitude DECIMAL(9,6),
    city_longitude DECIMAL(9,6)
    )
WITH 
(DATA_COMPRESSION = PAGE);
GO