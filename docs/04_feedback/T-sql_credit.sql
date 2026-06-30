
-- Người vay nào có khả năng nợ quá hạn cao nhất
SELECT
    LoanGrade,
    COUNT(*) total_customer,
    SUM(CASE WHEN LoanStatus = 1 THEN 1 ELSE 0 END) DefaultCount,
    FORMAT(
        CAST(SUM(CASE WHEN fl.LoanStatus = 1 THEN 1 ELSE 0 END)
        AS FLOAT) / COUNT(*),'p'
    )AS default_rat
FROM FactLoan fl
JOIN DimLoanGrade dg
    ON fl.GradeKey = dg.GradeKey
GROUP BY dg.LoanGrade
ORDER BY dg.LoanGrade



-- các mục đích vay cụ thể 
SELECT
    dp.LoanIntent,
    COUNT(*) AS TotalLoan,
    SUM(CASE
            WHEN fl.LoanStatus = 1 THEN 1
            ELSE 0
        END) AS DefaultCount,
    FORMAT(
        CAST(SUM(CASE WHEN fl.LoanStatus = 1 THEN 1 ELSE 0 END)
        AS FLOAT) / COUNT(*),'p'
    )AS default_rate
FROM FactLoan fl
LEFT JOIN DimLoanPurpose dp
    ON fl.PurposeKey = dp.PurposeKey
GROUP BY dp.LoanIntent
ORDER BY default_rate DESC;

-- Tỷ lệ khoản vay trên thu nhập và tỷ lệ nợ trên thu nhập liên quan như thế nào đến việc hoàn trả?
/*quy tắc :
DTI càng cao → tỷ lệ vỡ nợ càng tăng.

LTI càng cao → tỷ lệ vỡ nợ càng tăng.
*/

--1.Chứng minh DTI ảnh hưởng đến hoàn trả
SELECT
    CASE
        WHEN DebtToIncomeRatio < 0.2 THEN 'DTI < 20%'
        WHEN DebtToIncomeRatio < 0.4 THEN '20% - 40%'
        WHEN DebtToIncomeRatio < 0.6 THEN '40% - 60%'
        ELSE '> 60%'
    END AS DTI_Group,

    COUNT(*) AS TotalLoan,

    SUM(CASE
            WHEN LoanStatus = 1 THEN 1
            ELSE 0
        END) AS DefaultCount,

      FORMAT(
        CAST(SUM(CASE WHEN LoanStatus = 1 THEN 1 ELSE 0 END)
        AS FLOAT) / COUNT(*),'p') 
		AS DefaultRate

FROM FactLoan

GROUP BY
    CASE
        WHEN DebtToIncomeRatio < 0.2 THEN 'DTI < 20%'
        WHEN DebtToIncomeRatio < 0.4 THEN '20% - 40%'
        WHEN DebtToIncomeRatio < 0.6 THEN '40% - 60%'
        ELSE '> 60%'
    END

ORDER BY DefaultRate;

-- 2. Chứng minh LTI ảnh hưởng đến hoàn trả
SELECT
    CASE
        WHEN LoanToIncomeRatio < 0.2 THEN 'LTI < 20%'
        WHEN LoanToIncomeRatio < 0.4 THEN '20% - 40%'
        WHEN LoanToIncomeRatio < 0.6 THEN '40% - 60%'
        ELSE '> 60%'
    END AS LTI_Group,

    COUNT(*) AS TotalLoan,

    SUM(CASE
            WHEN LoanStatus = 1 THEN 1
            ELSE 0
        END) AS DefaultCount,

     FORMAT(
        CAST(SUM(CASE WHEN LoanStatus = 1 THEN 1 ELSE 0 END)
        AS FLOAT) / COUNT(*),'p') AS DefaultRate

FROM FactLoan

GROUP BY
    CASE
        WHEN LoanToIncomeRatio < 0.2 THEN 'LTI < 20%'
        WHEN LoanToIncomeRatio < 0.4 THEN '20% - 40%'
        WHEN LoanToIncomeRatio < 0.6 THEN '40% - 60%'
        ELSE '> 60%'
    END

ORDER BY DefaultRate;
-- 3. Chứng minh DTI quan trọng hơn LTI
SELECT
    LoanStatus,

    ROUND(AVG(DebtToIncomeRatio),2) AS Avg_DTI,

    ROUND(AVG(LoanToIncomeRatio),2) AS Avg_LTI

FROM FactLoan
GROUP BY LoanStatus;

-- 4.1 Sở hữu nhà có tạo khác biệt không?
SELECT
    dc.person_home_ownership,

    COUNT(*) AS TotalLoan,

    SUM(CASE
            WHEN fl.LoanStatus = 1 THEN 1
            ELSE 0
        END) AS DefaultCount,

   FORMAT(
        CAST(SUM(CASE WHEN LoanStatus = 1 THEN 1 ELSE 0 END)
        AS FLOAT) / COUNT(*),'p') AS DefaultRate

FROM FactLoan fl
JOIN DimCustomer dc
    ON fl.CustomerKey = dc.client_id

GROUP BY dc.person_home_ownership

ORDER BY DefaultRate DESC;

-- 4.2 Loại hình việc làm có tạo khác biệt không?
SELECT
    dc.employment_type,

    COUNT(*) AS TotalLoan,

    SUM(CASE
            WHEN fl.LoanStatus = 1 THEN 1
            ELSE 0
        END) AS DefaultCount,

   FORMAT(
        CAST(SUM(CASE WHEN LoanStatus = 1 THEN 1 ELSE 0 END)
        AS FLOAT) / COUNT(*),'p') AS DefaultRate

FROM FactLoan fl
JOIN DimCustomer dc
    ON fl.CustomerKey = dc.client_id

GROUP BY dc.employment_type

ORDER BY DefaultRate DESC;

-- 4.3 Thâm niên làm việc có ảnh hưởng không?

SELECT
    CASE
        WHEN dc.person_emp_length < 2 THEN '< 2 years'
        WHEN dc.person_emp_length < 5 THEN '2-5 years'
        WHEN dc.person_emp_length < 10 THEN '5-10 years'
        ELSE '> 10 years'
    END AS EmpGroup,

    COUNT(*) AS TotalLoan,

    SUM(CASE WHEN LoanStatus = 1 THEN 1 ELSE 0 END) AS DefaultCount,

       FORMAT(
        CAST(SUM(CASE WHEN LoanStatus = 1 THEN 1 ELSE 0 END)
        AS FLOAT) / COUNT(*),'p') AS DefaultRate

FROM FactLoan fl
JOIN DimCustomer dc ON fl.CustomerKey = dc.CustomerKey

GROUP BY
    CASE
        WHEN dc.person_emp_length < 2 THEN '< 2 years'
        WHEN dc.person_emp_length < 5 THEN '2-5 years'
        WHEN dc.person_emp_length < 10 THEN '5-10 years'
        ELSE '> 10 years'
    END

ORDER BY DefaultRate DESC;



---------------------------------------------------------------------------

-- 5.1 Chứng minh người có nợ xấu trong quá khứ rủi ro hơn

SELECT
    dc.cb_person_default_on_file,

    COUNT(*) AS TotalLoan,

    SUM(CASE
            WHEN fl.LoanStatus = 1 THEN 1
            ELSE 0
        END) AS DefaultCount,

    FORMAT(
        CAST(
            SUM(CASE
                    WHEN fl.LoanStatus = 1 THEN 1
                    ELSE 0
                END)
            AS FLOAT
        ) / COUNT(*),
        'P'
    ) AS DefaultRate

FROM FactLoan fl
JOIN DimCustomer dc
    ON fl.CustomerKey = dc.CustomerKey

GROUP BY dc.cb_person_default_on_file;




SELECT
    dc.cb_person_default_on_file,

    ROUND(AVG(fl.InterestRate),2) AS AvgInterestRate

FROM FactLoan fl
JOIN DimCustomer dc
    ON fl.CustomerKey = dc.CustomerKey

GROUP BY dc.cb_person_default_on_file;


SELECT
    dc.cb_person_default_on_file,

    CASE
        WHEN dc.cb_person_cred_hist_length < 3 THEN '<3 years'
        WHEN dc.cb_person_cred_hist_length < 7 THEN '3-7 years'
        WHEN dc.cb_person_cred_hist_length < 10 THEN '7-10 years'
        ELSE '10+ years'
    END AS CreditHistory,

    COUNT(*) AS TotalLoan,

    FORMAT(
        CAST(
            SUM(CASE WHEN fl.LoanStatus = 1 THEN 1 ELSE 0 END)
            AS FLOAT
        ) / COUNT(*),
        'P'
    ) AS DefaultRate

FROM FactLoan fl
JOIN DimCustomer dc
    ON fl.CustomerKey = dc.CustomerKey

GROUP BY
    dc.cb_person_default_on_file,
    CASE
        WHEN dc.cb_person_cred_hist_length < 3 THEN '<3 years'
        WHEN dc.cb_person_cred_hist_length < 7 THEN '3-7 years'
        WHEN dc.cb_person_cred_hist_length < 10 THEN '7-10 years'
        ELSE '10+ years'
    END

HAVING COUNT(*) >= 30
ORDER BY
    dc.cb_person_default_on_file,
    CreditHistory;


-----------------------------------------------------------------------------

-- Có sự khác biệt giữa Mỹ, Anh và Canada không?


SELECT
    dl.Country,

    COUNT(*) AS TotalLoan,

    SUM(CASE
            WHEN fl.LoanStatus = 1 THEN 1
            ELSE 0
        END) AS DefaultCount,

    FORMAT(
        CAST(
            SUM(CASE
                    WHEN fl.LoanStatus = 1 THEN 1
                    ELSE 0
                END)
            AS FLOAT
        ) / COUNT(*),
        'P'
    ) AS DefaultRate

FROM FactLoan fl
JOIN DimLocation dl
    ON fl.LocationKey = dl.LocationKey

GROUP BY dl.Country
ORDER BY
    CAST(
        SUM(CASE WHEN fl.LoanStatus = 1 THEN 1 ELSE 0 END)
        AS FLOAT
    ) / COUNT(*) DESC;





-- Grade nào an toàn và Grade nào rủi ro?

SELECT
    dg.LoanGrade,

    COUNT(*) AS TotalLoan,

    SUM(CASE
            WHEN fl.LoanStatus = 1 THEN 1
            ELSE 0
        END) AS DefaultCount,

    FORMAT(
        CAST(
            SUM(CASE
                    WHEN fl.LoanStatus = 1 THEN 1
                    ELSE 0
                END)
            AS FLOAT
        ) / COUNT(*),
        'P'
    ) AS DefaultRate

FROM FactLoan fl
JOIN DimLoanGrade dg
    ON fl.GradeKey = dg.GradeKey

GROUP BY dg.LoanGrade
ORDER BY dg.LoanGrade;


----------------------------------------------------------------------------------
-- chứng minh loanintent

SELECT
    dp.LoanIntent,
    COUNT(*) AS TotalLoan,
    SUM(CASE WHEN fl.LoanStatus = 1 THEN 1 ELSE 0 END) AS DefaultCount,
    FORMAT(
        CAST(SUM(CASE WHEN fl.LoanStatus = 1 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*),
        'P'
    ) AS DefaultRate
FROM FactLoan fl
JOIN DimLoanPurpose dp
    ON fl.PurposeKey = dp.PurposeKey
GROUP BY dp.LoanIntent
ORDER BY DefaultRate DESC;




