# DATA QUALITY RULE CATALOG (ĐẶC TẢ CHẤT LƯỢNG DỮ LIỆU)
**Project Name:** Credit Risk Scoring System & Risk Data Mart  
**Domain:** Retail Banking / Credit Risk  
**Document Version:** 1.1.0  
**Framework:** DAMA-DMBOK Data Quality Dimensions  

---

## 1. TỔNG QUAN CÁC CHIỀU CHẤT LƯỢNG DỮ LIỆU (DQ DIMENSIONS)
Tài liệu này áp dụng các chiều chất lượng dữ liệu tiêu chuẩn sau:
* **Validity (Tính hợp lệ):** Dữ liệu phải tuân thủ đúng định dạng, kiểu dữ liệu và dải giá trị (range) cho phép.
* **Consistency (Tính nhất quán):** Dữ liệu giữa các trường (fields) phải logic và không mâu thuẫn với nhau.
* **Completeness (Tính toàn vẹn):** Dữ liệu không được phép rỗng tại các trường trọng yếu (Critical Data Elements).

## 2. QUY ƯỚC MỨC ĐỘ NGHIÊM TRỌNG (SEVERITY LEVELS)
* **CRITICAL (Nghiêm trọng):** Vi phạm logic nghiệp vụ cốt lõi hoặc pháp luật. Hành động: **Reject / Quarantine** (Cách ly và loại bỏ khỏi Data Mart).
* **WARNING (Cảnh báo):** Dữ liệu có thể bất thường nhưng được khoan hồng nếu thiếu thông tin (Tolerates Missing). Hành động: **Flag & Pass** (Đánh dấu lỗi nhưng vẫn cho phép nạp vào Data Mart để điền khuyết sau).

---

## 3. CHI TIẾT CÁC QUY TẮC (DATA QUALITY RULES)

### DQ-R01: Ràng buộc độ tuổi hợp pháp (Age Bounds)
* **Rule ID:** `R1_AGE`
* **Dimension:** Validity
* **Severity:** CRITICAL
* **Business Rationale:** Theo luật định và chính sách tín dụng, khách hàng vay vốn phải nằm trong độ tuổi lao động trưởng thành và không vượt quá giới hạn rủi ro tuổi tác.
* **Technical Logic:** `person_age >= 18 AND person_age <= 85`
* **Action on Fail:** Reject record.

### DQ-R02: Logic thâm niên công tác (Experience Logic)
* **Rule ID:** `R2_EXPERIENCE`
* **Dimension:** Consistency
* **Severity:** WARNING
* **Business Rationale:** Số năm đi làm không thể lớn hơn tuổi đời trừ đi độ tuổi lao động tối thiểu (quy định là 16 tuổi).
* **Technical Logic:** `IF person_emp_length IS NOT NULL THEN person_emp_length <= (person_age - 16)`
* **Action on Fail:** Flag record (Pass if NULL).

### DQ-R03: Logic độ dài lịch sử tín dụng (Credit History Logic)
* **Rule ID:** `R3_CREDIT_HIST`
* **Dimension:** Consistency
* **Severity:** WARNING
* **Business Rationale:** Khách hàng chỉ có thể bắt đầu có lịch sử tín dụng CIC sau khi đủ 18 tuổi (tuổi trưởng thành hợp pháp).
* **Technical Logic:** `IF cb_person_cred_hist_length IS NOT NULL THEN cb_person_cred_hist_length <= (person_age - 18)`
* **Action on Fail:** Flag record (Pass if NULL).

### DQ-R04: Ràng buộc số liệu tài chính cơ bản (Financial Baseline)
* **Rule ID:** `R4_FINANCIALS`
* **Dimension:** Validity / Completeness
* **Severity:** CRITICAL
* **Business Rationale:** Các hồ sơ xin cấp tín dụng bắt buộc phải có thu nhập và số tiền đề nghị vay lớn hơn 0 để tính toán khả năng trả nợ.
* **Technical Logic:** `person_income > 0 AND loan_amnt > 0`
* **Action on Fail:** Reject record.

### DQ-R05: Ràng buộc tỷ lệ sử dụng hạn mức (Utilization Range)
* **Rule ID:** `R5_UTILIZATION`
* **Dimension:** Validity
* **Severity:** WARNING
* **Business Rationale:** Tỷ lệ tận dụng tín dụng (Credit Utilization) là một giá trị phần trạng, bắt buộc phải nằm trong khoảng từ 0% đến 100%.
* **Technical Logic:** `IF credit_utilization_ratio IS NOT NULL THEN credit_utilization_ratio >= 0 AND credit_utilization_ratio <= 1`
* **Action on Fail:** Flag record (Pass if NULL).

### DQ-R06: Nhất quán Tỷ lệ Khoản vay trên Thu nhập (LTI Sync)
* **Rule ID:** `R6_RATIO_SYNC`
* **Dimension:** Consistency
* **Severity:** WARNING
* **Business Rationale:** Tỷ lệ LTI hệ thống báo cáo phải khớp với phép chia toán học thực tế giữa khoản vay và thu nhập, cho phép sai số làm tròn 1%.
* **Technical Logic:** `IF loan_to_income_ratio IS NOT NULL THEN ABS((loan_amnt / person_income) - loan_to_income_ratio) <= 0.01`
* **Action on Fail:** Flag record (Pass if NULL).

### DQ-R07: Nhất quán Tỷ lệ DTI và Tỷ lệ khoản vay (DTI Logic)
* **Rule ID:** `R7_DTI_LOGIC`
* **Dimension:** Consistency
* **Severity:** WARNING
* **Business Rationale:** Tổng tỷ lệ nợ trên thu nhập (DTI) bắt buộc phải lớn hơn hoặc bằng tỷ lệ của riêng khoản vay hiện tại so với thu nhập.
* **Technical Logic:** `IF debt_to_income_ratio IS NOT NULL AND loan_percent_income IS NOT NULL THEN debt_to_income_ratio >= loan_percent_income`
* **Action on Fail:** Flag record (Pass if NULL).

### DQ-R08: Nhất quán Hành vi Trễ hạn (Default vs. Delinquency)
* **Rule ID:** `R8_DEFAULT_DELINQUENCY`
* **Dimension:** Consistency
* **Severity:** WARNING
* **Business Rationale:** Nếu khách hàng được ghi nhận đã từng vỡ nợ (Default = Y), thì số lần trễ hạn trong quá khứ không thể bằng 0.
* **Technical Logic:** `IF cb_person_default_on_file IS NOT NULL AND past_delinquencies IS NOT NULL THEN NOT (cb_person_default_on_file == 'Y' AND past_delinquencies == 0)`
* **Action on Fail:** Flag record (Pass if NULL).

### DQ-R09: Nhất quán Hạn mức và Số lượng thẻ/tài khoản (Utilization vs. Accounts)
* **Rule ID:** `R9_UTILIZATION_ACCOUNTS`
* **Dimension:** Consistency
* **Severity:** WARNING
* **Business Rationale:** Khách hàng không thể có tỷ lệ sử dụng tín dụng lớn hơn 0 nếu họ không có bất kỳ tài khoản/thẻ tín dụng nào đang mở.
* **Technical Logic:** `IF credit_utilization_ratio IS NOT NULL AND open_accounts IS NOT NULL THEN NOT (credit_utilization_ratio > 0 AND open_accounts == 0)`
* **Action on Fail:** Flag record (Pass if NULL).

### DQ-R10: Nhất quán Dư nợ ngoài (Total Debt Sync)
* **Rule ID:** `R10_TOTAL_DEBT_SYNC`
* **Dimension:** Consistency
* **Severity:** WARNING
* **Business Rationale:** Nếu khách hàng không có dư nợ nào khác ngoài khoản vay này (other_debt = 0), tổng DTI phải bằng chính tỷ lệ khoản vay trên thu nhập (cho phép sai lệch 1%).
* **Technical Logic:** `IF other_debt IS NOT NULL AND debt_to_income_ratio IS NOT NULL AND loan_percent_income IS NOT NULL THEN NOT (other_debt == 0 AND ABS(debt_to_income_ratio - loan_percent_income) > 0.01)`
* **Action on Fail:** Flag record (Pass if NULL).

### DQ-R11: Giới hạn Tọa độ Địa lý (Geographical Bounds)
* **Rule ID:** `R11_GEO_BOUNDS`
* **Dimension:** Validity
* **Severity:** WARNING
* **Business Rationale:** Tọa độ GPS hợp lệ theo chuẩn quốc tế: Vĩ độ (Latitude) từ -90 đến 90, Kinh độ (Longitude) từ -180 đến 180.
* **Technical Logic:** `IF city_latitude IS NOT NULL AND city_longitude IS NOT NULL THEN city_latitude BETWEEN -90 AND 90 AND city_longitude BETWEEN -180 AND 180`
* **Action on Fail:** Flag record (Pass if NULL).

### DQ-R12: Kiểm tra khuyết thiếu tỷ lệ nợ trên thu nhập (DTI Null Check)
* **Rule ID:** `R12_DTI_NULL`
* **Dimension:** Completeness
* **Severity:** CRITICAL
* **Business Rationale:** Tỷ lệ nợ trên thu nhập (DTI) là chỉ số bắt buộc để phân tích rủi ro tín dụng. Nếu bị khuyết thiếu, hệ thống sẽ cố gắng tính toán lại từ các trường `other_debt` và `person_income`. Nếu không thể tính toán được, bản ghi sẽ bị đánh dấu nghiêm trọng.
* **Technical Logic:** `debt_to_income_ratio IS NOT NULL` (Sau khi tính toán dự phòng: `(other_debt + loan_amnt) / person_income`)
* **Action on Fail:** Reject record.

### DQ-R13: Ràng buộc dải giá trị tỷ lệ nợ trên thu nhập (DTI Range Check)
* **Rule ID:** `R13_DTI_RANGE`
* **Dimension:** Validity
* **Severity:** CRITICAL
* **Business Rationale:** Tỷ lệ nợ trên thu nhập không thể âm.
* **Technical Logic:** `IF debt_to_income_ratio IS NOT NULL THEN debt_to_income_ratio >= 0`
* **Action on Fail:** Reject record.

### DQ-R14: Cảnh báo tỷ lệ nợ trên thu nhập bất thường (DTI Abnormal Check)
* **Rule ID:** `R14_DTI_MAX`
* **Dimension:** Validity
* **Severity:** WARNING
* **Business Rationale:** Tỷ lệ nợ trên thu nhập vượt quá 1.2 (120% thu nhập năm) là bất thường, có thể do lỗi nhập liệu đơn vị hoặc rủi ro tài chính cực đoan cần xem xét.
* **Technical Logic:** `IF debt_to_income_ratio IS NOT NULL THEN debt_to_income_ratio <= 1.2`
* **Action on Fail:** Flag record.

### DQ-R15: Kiểm tra khuyết thiếu thông tin vỡ nợ (Default File Null Check)
* **Rule ID:** `R15_DEFAULT_NULL`
* **Dimension:** Completeness
* **Severity:** CRITICAL
* **Business Rationale:** Thông tin có lịch sử vỡ nợ hay không là thuộc tính bắt buộc để phân nhóm khách hàng. Nếu bị khuyết thiếu, hệ thống sẽ tự động gán giá trị là 'N' (Không vỡ nợ) nếu số lần nợ quá hạn (`past_delinquencies`) bằng 0. Nếu không thể suy luận, bản ghi bị loại bỏ.
* **Technical Logic:** `cb_person_default_on_file IS NOT NULL` (Sau khi tính toán dự phòng: `'N'` nếu `past_delinquencies == 0`)
* **Action on Fail:** Reject record.

### DQ-R16: Định dạng giá trị vỡ nợ (Default File Value Check)
* **Rule ID:** `R16_DEFAULT_VALUE`
* **Dimension:** Validity
* **Severity:** CRITICAL
* **Business Rationale:** Trường thông tin vỡ nợ chỉ được phép chứa các giá trị chuẩn hóa là 'Y' (Có) hoặc 'N' (Không).
* **Technical Logic:** `IF cb_person_default_on_file IS NOT NULL THEN cb_person_default_on_file IN ('Y', 'N')`
* **Action on Fail:** Reject record.

### DQ-R17: Kiểm tra khuyết thiếu xếp hạng khoản vay (Loan Grade Null Check)
* **Rule ID:** `R17_GRADE_NULL`
* **Dimension:** Completeness
* **Severity:** CRITICAL
* **Business Rationale:** Xếp hạng khoản vay là trường thông tin cốt lõi để phân loại và đánh giá mức độ rủi ro của khoản vay, bắt buộc phải có thông tin và không thể tự tính toán suy luận từ các trường khác.
* **Technical Logic:** `loan_grade IS NOT NULL`
* **Action on Fail:** Reject record.

### DQ-R18: Định dạng xếp hạng khoản vay (Loan Grade Value Check)
* **Rule ID:** `R18_GRADE_VALUE`
* **Dimension:** Validity
* **Severity:** CRITICAL
* **Business Rationale:** Xếp hạng khoản vay phải nằm trong danh mục phân loại chuẩn của ngân hàng từ A đến G.
* **Technical Logic:** `IF loan_grade IS NOT NULL THEN loan_grade IN ('A', 'B', 'C', 'D', 'E', 'F', 'G')`
* **Action on Fail:** Reject record.

### DQ-R19: Nhất quán giữa Xếp hạng khoản vay và Tỷ lệ sử dụng hạn mức (Loan Grade vs. Utilization)
* **Rule ID:** `R19_GRADE_UTILIZATION`
* **Dimension:** Consistency
* **Severity:** WARNING
* **Business Rationale:** Khách hàng được xếp hạng khoản vay mức A (rủi ro thấp nhất) thường có hành vi tài chính tốt và không nên có tỷ lệ sử dụng hạn mức tín dụng quá cao (>= 80%). Nếu vi phạm, cần gắn cờ cảnh báo để kiểm tra lại xếp hạng.
* **Technical Logic:** `IF loan_grade IS NOT NULL AND credit_utilization_ratio IS NOT NULL THEN NOT (loan_grade == 'A' AND credit_utilization_ratio >= 0.8)`
* **Action on Fail:** Flag record.

### DQ-R20: Kiểm tra khuyết thiếu số lần nợ quá hạn (Past Delinquencies Null Check)
* **Rule ID:** `R20_DELINQ_NULL`
* **Dimension:** Completeness
* **Severity:** CRITICAL
* **Business Rationale:** Số lần nợ quá hạn trong quá khứ là chỉ số quan trọng để đánh giá uy tín tín dụng của khách hàng. Nếu bị khuyết thiếu, hệ thống tự động gán giá trị bằng 0 nếu khách hàng không có lịch sử vỡ nợ (`cb_person_default_on_file == 'N'`).
* **Technical Logic:** `past_delinquencies IS NOT NULL` (Sau khi tính toán dự phòng: `0` nếu `cb_person_default_on_file == 'N'`)
* **Action on Fail:** Reject record.

### DQ-R21: Ràng buộc số lần nợ quá hạn hợp lệ (Past Delinquencies Range Check)
* **Rule ID:** `R21_DELINQ_RANGE`
* **Dimension:** Validity
* **Severity:** CRITICAL
* **Business Rationale:** Số lần nợ quá hạn phải là một số nguyên không âm.
* **Technical Logic:** `IF past_delinquencies IS NOT NULL THEN past_delinquencies >= 0`
* **Action on Fail:** Reject record.