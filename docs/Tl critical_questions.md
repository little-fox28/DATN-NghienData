### I. Nghiệp vụ Rủi ro Tín dụng & Tư duy Kinh doanh (Domain Knowledge)
1. Định nghĩa "Vỡ nợ" (Default) trong dự án của bạn được xác định dựa trên tiêu chí nào (DPD 30, 60 hay 90)? Tại sao?
- Thường dùng DPD ≥ 90 ngày theo chuẩn Basel và IFRS 9 vì phản ánh rõ khả năng mất vốn.
2. Điểm tín dụng (Credit Score) bạn tạo ra có ý nghĩa gì đối với quyết định phê duyệt khoản vay của ngân hàng?
-Là thước đo rủi ro tín dụng, điểm càng cao khả năng vỡ nợ càng thấp.
3. Sự khác biệt giữa Probability of Default (PD), Loss Given Default (LGD), và Exposure at Default (EAD) là gì? Mô hình của bạn đang giải quyết yếu tố nào?
- PD: Xác suất vỡ nợ.
- LGD: Tỷ lệ tổn thất khi vỡ nợ.
- EAD: Dư nợ tại thời điểm vỡ nợ.
- Dự án này tập trung vào PD.
4. Tại sao tỷ lệ nợ trên thu nhập (DTI - Debt-to-Income) lại là một chỉ số sống còn trong việc đánh giá rủi ro?
- DTI cao cho thấy phần lớn thu nhập đã dùng để trả nợ, rủi ro mất khả năng thanh toán cao.
5. Nếu khách hàng có thu nhập cao nhưng điểm tín dụng (Credit History) ngắn, rủi ro tiềm ẩn ở đây là gì?
- Thiếu dữ liệu đánh giá hành vi trả nợ nên vẫn tiềm ẩn rủi ro.
6. Nhóm khách hàng "Thin-file" (chưa từng vay mượn) sẽ bị mô hình của bạn đánh giá như thế nào? Có công bằng không?
- Mô hình thường đánh giá thận trọng hơn do thiếu dữ liệu lịch sử.
7. Sự khác nhau giữa nợ thế chấp (Secured Loan) và nợ tín chấp (Unsecured Loan) ảnh hưởng thế nào đến cách xây dựng Scorecard?
- Secured Loan có tài sản đảm bảo nên rủi ro thấp hơn và scorecard thường cho điểm tốt hơn.
8. Khi tỷ lệ lạm phát kinh tế tăng cao, mô hình chấm điểm dựa trên dữ liệu quá khứ của bạn có còn chính xác không?
- Độ chính xác có thể giảm do Concept Drift, cần tái huấn luyện định kỳ.
9. Hệ thống của bạn xử lý thế nào với các khách hàng có nghề nghiệp tự do (Self-employed) với thu nhập không ổn định?
- Dùng thêm chỉ số dòng tiền, thu nhập trung bình nhiều tháng thay vì thu nhập một thời điểm.
10. Bạn làm cách nào để giải thích cho Giám đốc rủi ro hiểu tại sao một khách hàng bị mô hình từ chối phê duyệt?
- Dựa vào các yếu tố ảnh hưởng mạnh nhất như DTI cao, lịch sử nợ xấu, thu nhập thấp,...
11. "Information Value (IV)" và "Weight of Evidence (WOE)" có ý nghĩa gì trong nghiệp vụ tín dụng?
- WOE: Chuyển đổi biến để phản ánh khả năng phân biệt Good/Bad.
- IV: Đo sức mạnh dự báo của biến.
12. Tại sao Basel II/IFRS 9 lại khuyên dùng Logistic Regression cho Credit Scorecard thay vì các mô hình Black-box như Deep Learning?
- Dễ giải thích minh bạch đáp ứng yêu càu kiểm toán và quy định basel
13. Làm sao để phân biệt giữa khách hàng "không có khả năng trả nợ" và khách hàng "cố tình lừa đảo" (Fraud) thông qua dữ liệu?
- Default là mất khả năng trả nợ
- Fraud là cố tình gian lận thông tin.
14. Mục đích vay (Loan Intent) như "Y tế" hay "Giáo dục" khác gì so với "Tiêu dùng cá nhân" về mặt rủi ro?
- Khoản vay y tế hoặc giáo dục thường ổn định hơn vay tiêu dùng cá nhân.
15. Tỷ lệ cấp tín dụng trên giá trị tài sản đảm bảo (LTV - Loan-to-Value) có được phản ánh trong bộ dữ liệu của bạn không?
- Không. Bộ dữ liệu hiện tại không có thông tin tài sản đảm bảo nên không tính được LTV.
16. Bạn sẽ tư vấn gì cho Business User nếu tỷ lệ duyệt (Approval Rate) của hệ thống tự động quá thấp, dẫn đến mất doanh số? 
- Đề xuất xem lại Cut-off Score và đánh đổi giữa tăng doanh số và kiểm soát rủi ro.
17. Cut-off score (Điểm cắt) để phân loại Duyệt/Từ chối được bạn xác định dựa trên cơ sở tối ưu hóa lợi nhuận hay cực tiểu hóa rủi ro?
- Tối ưu giữa lợi nhuận kỳ vọng và mức rủi ro chấp nhận được.
18. Làm sao để mô hình không vi phạm các nguyên tắc đạo đức/phân biệt đối xử (độ tuổi, giới tính, vùng miền)?
- Hạn chế sử dụng các biến nhạy cảm như giới tính, vùng miền hoặc kiểm tra Fairness.
19. "Vùng xám" (Grey area - khách hàng nằm ngay sát ranh giới cut-off) sẽ được xử lý thủ công hay tự động?
- Chuyển sang thẩm định thủ công thay vì quyết định tự động.
20. Giả sử hệ thống chấm điểm sai và gây thiệt hại tài chính, ai (hoặc bộ phận nào) sẽ chịu trách nhiệm?
-Bộ phận Quản lý rủi ro, Data Science và Ban phê duyệt mô hình cùng chịu trách nhiệm theo quy trình quản trị mô hình.

### II. Kỹ sư Dữ liệu & Kiểm soát Chất lượng (Data Engineering & Quality)
21. Bạn xử lý các bản ghi có tuổi đi làm (Employment Length) lớn hơn tuổi đời (Age) như thế nào?
- Xem là dữ liệu lỗi, loại bỏ hoặc hiệu chỉnh theo quy tắc nghiệp vụ.
22. Tại sao bạn quyết định xóa (Drop) thay vì điền khuyết (Impute) đối với các giá trị Null trong trường Thu nhập?
- Nếu tỷ lệ thiếu nhỏ và dữ liệu quan trọng thì loại bỏ giúp tránh tạo sai xót.
23. Nếu điền khuyết (Imputing) giá trị Null bằng Mean/Median, bạn có lo ngại làm méo mó phân phối gốc của biến không?
- Có, đặc biệt với dữ liệu lệch phải như thu nhập.
# 24. Pipeline xử lý dữ liệu của bạn mất bao lâu để chạy qua 37.000 dòng? Thuật toán O(n) hiện tại có scale lên 1 triệu dòng được không?
25. Làm sao để đảm bảo không xảy ra Data Leakage (Rò rỉ dữ liệu) giữa tập Train và Test trong quá trình Feature Engineering?
- Chia Train/Test trước rồi mới thực hiện Feature Engineering.
26. Thiết kế OOP (Rule Engine) cho Data Quality Validation mang lại lợi ích gì so với việc dùng nhiều lệnh if-else lồng nhau?
- Dễ bảo trì, mở rộng và tái sử dụng hơn if-else lồng nhau. 
27. Nếu dữ liệu mới (Real-time data) bị lỗi định dạng string trong cột Numeric, API của bạn có bị crash không?
- API cần validation và trả lỗi 400 thay vì crash.
# 28. "Concept Drift" (Sự thay đổi hành vi khách hàng) sẽ được hệ thống của bạn phát hiện thông qua những metric giám sát nào?
29. Quá trình One-Hot Encoding cho cột 'Thành phố' (City) có dẫn đến "Lời nguyền số chiều" (Curse of Dimensionality) không?
- Có nếu số thành phố quá lớn.
30. Bạn đã dùng kỹ thuật gì để xử lý hiện tượng Imbalanced Data (Mất cân bằng nhãn) cực đoan trong Credit Risk?
- SMOTE, Class Weight hoặc Threshold Tuning.
31. SMOTE (Synthetic Minority Over-sampling Technique) tạo ra dữ liệu giả, điều này có làm sai lệch logic tài chính thực tế không?
- Có thể nhưng giúp mô hình học tốt hơn nhóm thiểu số.
32. Bạn xử lý Outliers (ví dụ thu nhập 1 triệu USD/năm) bằng Capping (Winsorization) hay loại bỏ hoàn toàn? Vì sao?
- Ưu tiên Winsorization (Capping) thay vì xóa hoàn toàn.
33. Làm sao để xử lý các cột có tính Cardinality cao (quá nhiều giá trị duy nhất) mà không làm tăng kích thước ma trận quá mức?
- DÙng Target Encoding hoặc Frequency Encoding để xử lý các biến có Cardinality cao.
34. Nếu Core Banking thay đổi cấu trúc bảng, module Extract của bạn có cơ chế nào để tự động cảnh báo lỗi schema không?
- Kiểm tra schema validation và gửi cảnh báo tự động.
35. Dữ liệu vĩ độ, kinh độ (Latitude, Longitude) trong bộ data này được bạn tận dụng hay loại bỏ? Tại sao?
- Nếu không chứng minh được giá trị dự báo thì loại bỏ.

### III. Khai phá Dữ liệu & Kỹ thuật Đặc trưng (EDA & Feature Engineering)
36. Biểu đồ nào là phù hợp nhất để so sánh phân phối thu nhập giữa nhóm Good và Bad customers?
- Boxplot hoặc Violin Plot. Chúng giúp so sánh phân phối thu nhập giữa hai nhóm Good và Bad một cách trực quan.
37. Đa cộng tuyến (Multicollinearity) giữa Biến Thu nhập và Biến Hạn mức vay ảnh hưởng thế nào đến Logistic Regression?
- Làm hệ số Logistic Regression không ổn định.
38. Hệ số VIF (Variance Inflation Factor) của các biến trong mô hình hiện đang ở mức bao nhiêu?
- Cần tính thực tế. Thông thường VIF < 5 là tố
39. Bạn đã nhóm (Binning) biến Tuổi (Age) thành các nhóm như thế nào để đảm bảo tính đơn điệu (Monotonic trend) của tỷ lệ nợ xấu?
- Chia thành các nhóm 18–25, 26–35, 36–45, 46–60 và >60, sau đó kiểm tra tỷ lệ nợ xấu của từng nhóm để đảm bảo xu hướng đơn điệu.
40. Việc sử dụng WOE (Weight of Evidence) transformation giúp ích gì cho thuật toán hồi quy tuyến tính?
- Tạo quan hệ tuyến tính hơn với log-odds.
41. Có biến nào có Information Value (IV) rất cao (>0.5) nhưng lại đáng ngờ (Suspiciously good) vì chứa thông tin tương lai không?
- Có thể chứa thông tin tương lai hoặc leakage.
42. Tại sao Tỷ lệ Tận dụng Tín dụng (Credit Utilization Ratio) liên tục chạm mức 99% lại là tín hiệu cảnh báo vỡ nợ nghiêm trọng?
- Cho thấy khách hàng gần dùng hết hạn mức tín dụng.
# 43. Bạn có tạo ra các biến tương tác (Interaction Features) như (Tuổi x Thu nhập) không? Lý do? 
44. Lịch sử trễ hạn (Past Delinquencies) có trọng số IV lớn thứ mấy trong bộ tính năng của bạn?
- Thường nằm trong nhóm quan trọng nhất.
45. Sự khác biệt về tỷ lệ nợ xấu giữa khách hàng thuê nhà (Rent) và sở hữu nhà (Own/Mortgage) có ý nghĩa thống kê không?
- Kiểm định Chi-square hoặc t-test để xác nhận.
46. Bạn sử dụng kiểm định thống kê (Statistical Test) nào để khẳng định hai biến số liên tục độc lập với nhau?
- Sử dụng kiểm định tương quan Pearson hoặc Spearman. Nếu hệ số tương quan gần 0 và p-value không có ý nghĩa thống kê thì có thể xem hai biến gần như độc lập.
# 47. Làm sao để biến đổi một biến Categorical có tính thứ bậc (Ordinal) như "Trình độ học vấn" cho mô hình học máy?
48. Bạn giải thích thế nào nếu thấy tập khách hàng có bằng Thạc sĩ (Master) lại có tỷ lệ vỡ nợ cao hơn người chỉ tốt nghiệp cấp 3? 
- Có thể do mẫu nhỏ hoặc nhóm nghề nghiệp đặc thù.
49. Tính thời vụ (Seasonality) có tồn tại trong dữ liệu xin vay mượn này không? Bạn kiểm tra bằng cách nào?
- Kiểm tra theo tháng/quý nếu có dữ liệu thời gian.
50. Các khoản vay cho mục đích Kinh doanh/Khởi nghiệp (Venture) có rủi ro thực tế cao hơn hay thấp hơn vay Y tế (Medical)?
- Thông thường Venture rủi ro cao hơn.
# 51. Biến 'Thời hạn khoản vay' (Loan Term) có mối tương quan thuận hay nghịch với 'Lãi suất khoản vay' (Interest Rate) trong EDA của bạn?
52. Khi biến đổi (Transform) biến skewed (lệch) như Thu nhập, bạn dùng Log Transformation hay Box-Cox? Khác biệt là gì?
- Log đơn giản hơn 
- Box-Cox linh hoạt hơn.
# 53. Bạn đánh giá sức mạnh phân loại của từng tính năng đơn lẻ (Univariate analysis) bằng phương pháp nào?
54. Biến nào bị bạn đánh giá là rác (Noise) và thẳng tay loại bỏ trong quá trình lọc Features?
- ID khách hàng thường bị loại bỏ.
55. Giới tính (Gender) có nên được đưa vào mô hình chấm điểm tín dụng không, xét cả về mặt thống kê và đạo đức?
- Về đạo đức thường không khuyến khích

### IV. Thuật toán, Đánh giá & Scorecard (Modeling & Validation)
56. Nếu Logistic Regression không bắt được các mối quan hệ phi tuyến tính (Non-linear), tại sao không thay bằng Random Forest hay XGBoost? 
- Khó giải thích và khó đáp ứng yêu cầu kiểm toán.
# 57. Cây quyết định (Decision Tree) dễ giải thích, nhưng nhược điểm lớn nhất của nó trong Credit Scoring là gì?
58. Trong bối cảnh Credit Risk, Type I Error (False Positive) hay Type II Error (False Negative) gây ra thiệt hại tài chính nặng nề hơn?
- Type II (duyệt nhầm khách hàng xấu).
# 59. F1-Score có phải là chỉ số tốt để đánh giá mô hình rủi ro tín dụng mất cân bằng (Imbalanced) không?
60. Chỉ số Gini (Gini Coefficient) trong mô hình của bạn đạt bao nhiêu? Mức bao nhiêu là có thể mang ra production?
- Thông thường >40% là tốt.
61. Tại sao đường cong ROC (ROC Curve) có thể đánh lừa người phân tích khi tập dữ liệu quá mất cân bằng?
- Dữ liệu mất cân bằng vẫn có ROC đẹp.
# 62. PR Curve (Precision-Recall Curve) có cung cấp thông tin gì khác biệt so với ROC Curve trong bài toán của bạn không?
63. Chỉ số Kolmogorov-Smirnov (KS) Statistic dùng để đo lường điều gì trong mô hình Credit Scorecard?
- Khả năng tách Good và Bad
64. Calibration (Hiệu chỉnh xác suất) là gì và tại sao PD (Probability of Default) cần phải được calibrate trước khi tính điểm?
- Hiệu chỉnh xác suất dự đoán gần thực tế hơn.
# 65. Phương pháp Scaling để chuyển từ Xác suất Vỡ nợ (PD) sang Điểm Tín Dụng (ví dụ Base Score = 600, PDO = 20) hoạt động như thế nào?
# 66. Thuật toán của bạn có bị Overfitting (Học vẹt) không? Bằng chứng là độ chênh lệch Gini giữa tập Train và Test là bao nhiêu?
# 67. Kỹ thuật K-Fold Cross Validation được áp dụng như thế nào trong lúc huấn luyện? Bạn chọn K bằng mấy?
68. Nếu hệ số (Coefficient) của một biến cực kỳ quan trọng lại mang dấu âm (trái với logic kinh tế), bạn sẽ xử lý như thế nào?
- Kiểm tra lại dữ liệu, cách xử lý biến và hiện tượng đa cộng tuyến. Nếu hệ số vẫn mang dấu trái với logic kinh tế thì cân nhắc loại bỏ biến khỏi mô hình.
69. Việc điều chỉnh siêu tham số (Hyperparameter Tuning) như L1/L2 Regularization (Lasso/Ridge) tác động gì đến độ thưa (Sparsity) của Scorecard?
- L1 tạo sparsity và chọn biến, còn L2 chủ yếu giảm overfitting bằng cách thu nhỏ hệ số..
70. OOT (Out-of-Time) Validation khác gì so với OOS (Out-of-Sample) Validation? Bạn có sử dụng OOT không?
- OOT kiểm tra theo thời gian
- OOS kiểm tra theo mẫu.
71. Làm cách nào để bạn xây dựng "Reject Inference" (Suy luận loại bỏ) để thêm những khách hàng từng bị từ chối vào tập dữ liệu huấn luyện?
- Ước lượng hành vi khách hàng từng bị từ chối.
72. Tại sao việc mô hình luôn dự đoán nhãn '0' (Không vỡ nợ) lại đạt Accuracy 95% nhưng mô hình đó lại hoàn toàn vô dụng?
- Do mô hình chỉ đoán toàn bộ là Good.
73. Ma trận nhầm lẫn (Confusion Matrix) của mô hình tại điểm cut-off hiện tại cho thấy tỷ lệ phê duyệt nhầm khách hàng xấu là bao nhiêu?
- Đọc từ False Negative trong Confusion Matrix.
74. Bạn sử dụng ngưỡng tối ưu (Optimal Threshold) nào trên ROC curve để cân bằng giữa Recall và Precision? Dùng Youden's J statistic chăng?
- Có, dùng Youden's J Statistic hoặc chọn ngưỡng theo mục tiêu kinh doanh (tối ưu lợi nhuận/rủi ro).
75. Nếu có một thuật toán mới mạnh mẽ hơn nhưng là "Black-box" (không thể giải thích hệ số), bạn có quyết định thay thế Scorecard truyền thống không?
- Chỉ khi chứng minh được hiệu quả và khả năng giải thích.

### V. Kiến trúc Hệ thống, Triển khai & MLOps (System & Deployment)
# 76. Luồng kiến trúc Microservices của bạn kết nối Web App, Backend API và Model Registry như thế nào?
# 77. FastAPI/Flask xử lý thế nào nếu có 1.000 request chấm điểm tín dụng được gửi đến cùng lúc (Concurrency)?
78. Quá trình Serialize và Deserialize (như dùng thư viện pickle hoặc joblib) mô hình Machine Learning tiềm ẩn rủi ro bảo mật nào?
- Có thể thực thi mã độc khi deserialize nếu file mô hình đến từ nguồn không tin cậy
79. Nếu API trả về kết quả lỗi do thiếu một trường dữ liệu (Missing JSON Key), cơ chế Handle Exception của bạn sẽ thông báo gì cho Front-end?
- Trả lỗi 400 và mô tả trường bị thiếu.
80. Làm sao để quản lý các phiên bản (Versioning) của mô hình (VD: v1.0, v1.1) khi bạn cập nhật lại Scorecard?
- Sử dụng Model Registry để quản lý các phiên bản Scorecard (v1.0, v1.1, v2.0). Mỗi bản cập nhật được lưu thành một version riêng nhằm đảm bảo khả năng theo dõi và kiểm soát mô hình.
81. Cơ chế CI/CD (Continuous Integration / Continuous Deployment) nào được sử dụng để tự động test code và deploy API?
- GitHub Actions hoặc GitLab CI/CD. Chúng giúp tự động test code và deploy API.
# 82. Web App (như Streamlit) của bạn quản lý State (trạng thái ứng dụng) như thế nào khi khách hàng làm mới (refresh) trang?
83. Dữ liệu của khách hàng (PII - Personally Identifiable Information) truyền qua API có được mã hóa (Encryption) để đảm bảo bảo mật không?
- Có, dùng HTTPS/TLS để đảm bảo an toàn và bảo mật khi truyền qua API.
# 84. Thời gian phản hồi (Latency) của API từ lúc nhận request đến lúc trả về kết quả Credit Score là bao nhiêu mili-giây?
85. Làm sao để hệ thống lưu lại log của tất cả các quyết định phê duyệt/từ định chối từ API để Audit (Kiểm toán) sau này?
- Lưu Request, Response, Timestamp, Credit Score, quyết định phê duyệt, từ chối và Version Model để đảm bảo khả năng kiểm toán và truy vết.
### VI. Trực quan hóa Dữ liệu & Dashboard (BI & Visualization)
86. Tại sao bạn lại chọn biểu đồ này thay vì biểu đồ khác để thể hiện Phân bổ Rủi ro (Risk Distribution) trên Dashboard?
- Vì biểu đồ trực quan, dễ đọc và hỗ trợ so sánh phân bổ rủi ro giữa các nhóm một cách hiệu quả.
87. Drill-down (Khám phá sâu) trên Dashboard cho phép Giám đốc chi nhánh theo dõi từ cấp độ Khu vực xuống cấp độ Cá nhân vay như thế nào?
- Dashboard hỗ trợ Drill-down theo cấu trúc Region → Branch → Customer → Loan, cho phép Giám đốc chi nhánh đi từ góc nhìn tổng quan khu vực xuống chi tiết từng khách hàng và khoản vay cụ thể.
88. "Actionable Insights" (Insight có thể hành động) rõ ràng nhất mà Dashboard này mang lại cho bộ phận Thu hồi nợ (Collection Team) là gì?
- Danh sách khách hàng có xác suất vỡ nợ cao nhất.
89. Nếu Tableau/Power BI tải Dashboard quá chậm (chậm hơn 10s), bạn sẽ tối ưu hóa Aggregation ở tầng Database hay tầng BI?
Ưu tiên tối ưu Aggregation ở tầng Database trước, vì giảm lượng dữ liệu phải truyền và xử lý trên Tableau. Sau đó mới tối ưu ở tầng BI nếu cần.
90. Dashboard có tính năng What-If Analysis (Mô phỏng thay đổi tham số) để xem xét kịch bản lạm phát tăng không?
- Không. Dashboard hiện chỉ phân tích dữ liệu thực tế và chưa tích hợp tính năng What-If Analysis cho kịch bản lạm phát tăng do bộ dữ liệu không có biến lạm phát. Tuy nhiên, tính năng này có thể được phát triển trong các phiên bản sau.
91. Làm sao để đảm bảo dữ liệu trên Dashboard luôn được làm mới (Refresh) tự động hàng ngày mà không cần chạy file thủ công?
- Sử dụng Scheduled Refresh để tự động làm mới dữ liệu hằng ngày.
92. Các chỉ báo màu sắc (Đỏ/Vàng/Xanh) trên Dashboard có tuân thủ nguyên tắc mù màu (Color-blind friendly) hay không?
- Chưa hoàn toàn, hiện chủ yếu dùng Đỏ/Vàng/Xanh và có thể cải thiện thêm để thân thiện hơn với người mù màu.
# 93. Thiết kế giao diện (UI/UX) của Dashboard có làm nổi bật được "Top 5% khách hàng rủi ro cao nhất" ngay từ cái nhìn đầu tiên không?
94. Nếu Business User nói rằng "Dashboard quá phức tạp, tôi chỉ muốn xem 3 con số quan trọng nhất", bạn sẽ chọn 3 con số nào?
- Tổng số khách hàng, tỷ lệ nợ xấu và số khách hàng rủi ro cao. Đây là 3 KPI quan trọng nhất để đánh giá tình trạng danh mục tín dụng.
95. Mức độ chi tiết (Granularity) của báo cáo đang ở mức Khách hàng (CIF) hay mức Khoản vay (Loan ID)? Nếu 1 CIF có nhiều khoản vay thì tính toán thế nào?
- Mức CIF. Nếu một CIF có nhiều khoản vay thì dữ liệu được tổng hợp theo khách hàng, thường lấy tổng dư nợ hoặc mức rủi ro cao nhấ

### VII. Quản lý Dự án & Phát triển Tương lai (Project Management)
# 96. Quản lý thời gian và phân chia công việc trong nhóm diễn ra như thế nào đối với dự án này?
# 97. Khó khăn lớn nhất về mặt Kỹ thuật (Technical Debt) mà nhóm đã phải thỏa hiệp để kịp tiến độ # bảo vệ đồ án là gì?
# 98. Trọng số đóng góp của từng khía cạnh: Dữ liệu sạch, Thuật toán hay Giao diện đóng vai trò quyết định đến sự thành công của dự án này?
# 99. Nếu được cấp ngân sách và thêm 3 tháng, tính năng số 1 bạn muốn nâng cấp cho hệ thống này là gì?
# 100. Làm thế nào để dự án này chứng minh được giá trị sinh lời (ROI) rõ ràng nếu muốn bán giải pháp cho một tổ chức tài chính vi mô (Microfinance)?