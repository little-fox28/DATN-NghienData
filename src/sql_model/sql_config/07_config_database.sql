USE master;
GO

SET NOCOUNT ON;
GO

------------------------------------------------------------
-- 1. Check whether the database exists
------------------------------------------------------------
IF DB_ID(N'CreditRiskDB') IS NULL
BEGIN
    THROW 50001,
        N'Database CreditRiskDB was not found.',
        1;
END;
GO

------------------------------------------------------------
-- 2. Set the Recovery Model to SIMPLE if necessary
------------------------------------------------------------
IF EXISTS
(
    SELECT 1
    FROM sys.databases
    WHERE name = N'CreditRiskDB'
      AND recovery_model_desc <> N'SIMPLE'
)
BEGIN
    ALTER DATABASE [CreditRiskDB]
    SET RECOVERY SIMPLE;

    PRINT N'Recovery Model has been changed to SIMPLE.';
END
ELSE
BEGIN
    PRINT N'Recovery Model is already set to SIMPLE.';
END;
GO

------------------------------------------------------------
-- 3. Enable Read Committed Snapshot Isolation if necessary
------------------------------------------------------------
IF EXISTS
(
    SELECT 1
    FROM sys.databases
    WHERE name = N'CreditRiskDB'
      AND is_read_committed_snapshot_on = 0
)
BEGIN
    ALTER DATABASE [CreditRiskDB]
    SET READ_COMMITTED_SNAPSHOT ON
    WITH ROLLBACK IMMEDIATE;

    PRINT N'READ_COMMITTED_SNAPSHOT has been enabled.';
END
ELSE
BEGIN
    PRINT N'READ_COMMITTED_SNAPSHOT is already enabled.';
END;
GO

------------------------------------------------------------
-- 4. Check server-level configuration permissions
------------------------------------------------------------
IF ISNULL(IS_SRVROLEMEMBER(N'sysadmin'), 0) <> 1
BEGIN
    THROW 50002,
        N'The current SQL Server account must have the sysadmin role to run sp_configure.',
        1;
END;
GO

------------------------------------------------------------
-- 5. Enable advanced configuration options
------------------------------------------------------------
EXEC sys.sp_configure
    'show advanced options',
    1;

RECONFIGURE;
GO

------------------------------------------------------------
-- 6. Set Cost Threshold for Parallelism to 50
------------------------------------------------------------
DECLARE @CurrentCostThreshold INT;

SELECT
    @CurrentCostThreshold = CONVERT(INT, value_in_use)
FROM sys.configurations
WHERE name = N'cost threshold for parallelism';

IF @CurrentCostThreshold <> 50
BEGIN
    EXEC sys.sp_configure
        'cost threshold for parallelism',
        50;

    RECONFIGURE;

    PRINT N'Cost Threshold for Parallelism has been set to 50.';
END
ELSE
BEGIN
    PRINT N'Cost Threshold for Parallelism is already set to 50.';
END;
GO

------------------------------------------------------------
-- 7. Set Maximum Degree of Parallelism to 4
------------------------------------------------------------
DECLARE @CurrentMaxDop INT;

SELECT
    @CurrentMaxDop = CONVERT(INT, value_in_use)
FROM sys.configurations
WHERE name = N'max degree of parallelism';

IF @CurrentMaxDop <> 4
BEGIN
    EXEC sys.sp_configure
        'max degree of parallelism',
        4;

    RECONFIGURE;

    PRINT N'MAXDOP has been set to 4.';
END
ELSE
BEGIN
    PRINT N'MAXDOP is already set to 4.';
END;
GO

------------------------------------------------------------
-- 8. Disable advanced configuration options
------------------------------------------------------------
EXEC sys.sp_configure
    'show advanced options',
    0;

RECONFIGURE;
GO

------------------------------------------------------------
-- 9. Verify the database and server configurations
------------------------------------------------------------
SELECT
    name AS DatabaseName,
    recovery_model_desc AS RecoveryModel,
    is_read_committed_snapshot_on AS RCSIEnabled
FROM sys.databases
WHERE name = N'CreditRiskDB';

SELECT
    name AS ConfigurationName,
    value AS ConfiguredValue,
    value_in_use AS CurrentValue
FROM sys.configurations
WHERE name IN
(
    N'cost threshold for parallelism',
    N'max degree of parallelism'
);
GO