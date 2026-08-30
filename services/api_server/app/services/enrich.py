"""
Enrich Service — Business logic cho việc đọc/ghi/sửa/xóa dữ liệu CSV enriched & Manual Review Backlog.
"""
import csv
import io
import json
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict, Any

from services.api_server.app.schemas.loan import EnrichPayload
from services.api_server.app.utils.hash_utils import generate_client_id

# Đường dẫn tới thư mục data/raw
DATA_RAW_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "raw"

# Thứ tự cột chuẩn của file CSV enriched
ENRICHED_COLUMNS = [
    "application_id", "client_ID", "person_age", "person_income", "person_home_ownership",
    "person_emp_length", "loan_intent", "loan_grade", "loan_amnt",
    "loan_int_rate", "loan_status", "loan_percent_income",
    "loan_to_income_ratio", "debt_to_income_ratio",
    "cb_person_default_on_file", "cb_person_cred_hist_length",
    "gender", "marital_status", "education_level", "employment_type",
    "loan_term_months", "ml_pd_score", "ml_credit_score", "ml_decision",
    "ml_risk_tier", "top_positive_factors", "top_negative_factors",
    "recommended_interest_rate", "max_credit_limit", "monthly_payment_estimate", "total_interest_estimate",
    "created_at", "record_date", "record_month",
]

_CACHED_RAW_BACKLOG: List[Dict[str, Any]] = []
_DELETED_CLIENT_IDS: set = set()


def get_raw_data_path() -> Optional[Path]:
    for name in ["Credit Risk Data.csv", "Credit%20Risk%20Data.csv", "credit_risk_dataset.csv"]:
        p = DATA_RAW_DIR / name
        if p.exists():
            return p
    return None


def get_file_path(target_date: Optional[date] = None) -> Path:
    """Trả về đường dẫn file enriched CSV theo ngày (mỗi ngày 1 file)."""
    d = target_date or date.today()
    return DATA_RAW_DIR / f"enriched_loan_data_{d.strftime('%Y%m%d')}.csv"


def _clean_record(raw: dict) -> dict:
    """Chuẩn hóa kiểu dữ liệu cho một bản ghi enriched."""
    r = dict(raw)
    
    # 1. Parse FICO Credit Score
    try:
        score_val = float(r.get("ml_credit_score") or 0)
        # Nếu score_val < 1 (bị nhầm với PD do lệch cột cũ), hiệu chỉnh lại
        if 0 < score_val < 1 and float(r.get("loan_term_months") or 0) > 300:
            r["ml_credit_score"] = int(float(r.get("loan_term_months")))
        elif score_val >= 300:
            r["ml_credit_score"] = int(score_val)
        else:
            r["ml_credit_score"] = 670
    except Exception:
        r["ml_credit_score"] = 670

    # 2. Parse PD Score
    try:
        pd_val = float(r.get("ml_pd_score") or 0)
        if pd_val > 1.0: # Bị lưu dạng % hoặc bị lệch với loan_term
            if pd_val in [12, 24, 36, 48, 60]:
                r["loan_term_months"] = int(pd_val)
                r["ml_pd_score"] = 0.045
            else:
                r["ml_pd_score"] = round(pd_val / 100.0, 4)
        else:
            r["ml_pd_score"] = round(pd_val, 4)
    except Exception:
        r["ml_pd_score"] = 0.045

    # 3. Parse loan_term_months
    try:
        r["loan_term_months"] = int(float(r.get("loan_term_months") or 36))
    except Exception:
        r["loan_term_months"] = 36

    # 4. Parse ML Decision
    dec = str(r.get("ml_decision", "")).strip().upper()
    if dec not in ["APPROVED", "APPROVED_CONDITIONAL", "MANUAL_REVIEW", "REJECTED"]:
        fico = r["ml_credit_score"]
        if fico >= 740:
            dec = "APPROVED"
        elif fico >= 670:
            dec = "APPROVED_CONDITIONAL"
        elif fico >= 580:
            dec = "MANUAL_REVIEW"
        else:
            dec = "REJECTED"
    r["ml_decision"] = dec

    # 5. Parse Top Positive / Negative Factors
    for factor_key in ["top_positive_factors", "top_negative_factors"]:
        val = r.get(factor_key)
        if isinstance(val, str) and (val.startswith("[") or val.startswith("{")):
            try:
                r[factor_key] = json.loads(val)
            except Exception:
                pass

    return r


def read_all_records() -> list[dict]:
    """Đọc toàn bộ file enriched_loan_data_*.csv trong data/raw/, mới nhất trước."""
    all_records: list[dict] = []
    if not DATA_RAW_DIR.exists():
        return all_records
    for f in sorted(DATA_RAW_DIR.glob("enriched_loan_data_*.csv"), reverse=True):
        try:
            with open(f, "r", encoding="utf-8") as csv_file:
                for row in csv.DictReader(csv_file):
                    client_id = row.get("client_ID")
                    if client_id and client_id not in _DELETED_CLIENT_IDS:
                        all_records.append(_clean_record(row))
        except Exception:
            continue
    return all_records


def get_processed_client_ids() -> set[str]:
    """Lấy tập hợp các client_ID và application_id đã được ghi nhận trong Live Enriched CSV hoặc bị xóa."""
    processed = set(_DELETED_CLIENT_IDS)
    for r in read_all_records():
        cid = r.get("client_ID")
        aid = r.get("application_id")
        if cid:
            processed.add(str(cid).strip())
        if aid:
            processed.add(str(aid).strip())
    return processed


def read_manual_review_backlog(limit: Optional[int] = None) -> list[dict]:
    """Đọc danh sách hồ sơ cần thẩm định thủ công (Grade C & D) chưa được xử lý."""
    global _CACHED_RAW_BACKLOG
    if not _CACHED_RAW_BACKLOG:
        raw_path = get_raw_data_path()
        if not raw_path:
            return []

        backlog: List[Dict[str, Any]] = []
        try:
            with open(raw_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    grade = str(row.get("loan_grade", "")).strip().upper()
                    if grade in ["C", "D"]:
                        client_id = str(row.get("client_ID") or row.get("id") or f"CUST-CD-{len(backlog)+1:05d}")
                        int_rate = float(row.get("loan_int_rate") or 14.5)
                        loan_term = int(float(row.get("loan_term_months") or 36))
                        income = float(row.get("person_income") or 55000)
                        loan_amnt = float(row.get("loan_amnt") or 12000)
                        dti = float(row.get("debt_to_income_ratio") or 0.35)
                        
                        # Tính toán ước tính điểm FICO & PD cho nhóm thẩm định thủ công
                        pd_est = 0.068 if grade == "C" else 0.092
                        fico_est = 642 if grade == "C" else 608

                        backlog.append({
                            "application_id": f"APP-MR-{client_id.replace('CUST-', '')}",
                            "client_ID": client_id,
                            "person_age": row.get("person_age", 30),
                            "person_income": income,
                            "person_home_ownership": row.get("person_home_ownership", "RENT"),
                            "person_emp_length": row.get("person_emp_length", 3),
                            "loan_intent": row.get("loan_intent", "PERSONAL"),
                            "loan_grade": grade,
                            "loan_amnt": loan_amnt,
                            "loan_int_rate": int_rate,
                            "loan_status": str(row.get("loan_status", "-1")),
                            "loan_percent_income": row.get("loan_percent_income", 0.22),
                            "loan_to_income_ratio": row.get("loan_to_income_ratio", 0.22),
                            "debt_to_income_ratio": dti,
                            "cb_person_default_on_file": row.get("cb_person_default_on_file", "N"),
                            "cb_person_cred_hist_length": row.get("cb_person_cred_hist_length", 4),
                            "gender": row.get("gender", "MALE"),
                            "marital_status": row.get("marital_status", "SINGLE"),
                            "education_level": row.get("education_level", "BACHELOR"),
                            "employment_type": row.get("employment_type", "FULL_TIME"),
                            "loan_term_months": loan_term,
                            "ml_pd_score": pd_est,
                            "ml_credit_score": fico_est,
                            "ml_decision": "MANUAL_REVIEW",
                            "ml_risk_tier": "MEDIUM_HIGH" if grade == "C" else "HIGH",
                            "top_positive_factors": [
                                {"feature": "person_income", "points": 2.50},
                                {"feature": "cb_person_default_on_file", "points": 1.80},
                            ],
                            "top_negative_factors": [
                                {"feature": "debt_to_income_ratio", "points": -2.20},
                                {"feature": "person_home_ownership", "points": -1.40},
                            ],
                            "recommended_interest_rate": int_rate,
                            "max_credit_limit": loan_amnt * 1.2,
                            "monthly_payment_estimate": round(loan_amnt / loan_term * 1.15, 2),
                            "total_interest_estimate": round(loan_amnt * (int_rate / 100) * (loan_term / 12), 2),
                            "created_at": datetime.now().isoformat(),
                            "record_date": str(date.today()),
                            "record_month": date.today().strftime("%Y-%m"),
                            "source": "backlog",
                        })
            _CACHED_RAW_BACKLOG = backlog
        except Exception as e:
            print(f"Error loading backlog: {e}")
            return []

    processed = get_processed_client_ids()
    active_backlog = [
        r for r in _CACHED_RAW_BACKLOG
        if str(r.get("client_ID", "")).strip() not in processed
        and str(r.get("application_id", "")).strip() not in processed
    ]
    if limit is not None:
        return active_backlog[:limit]
    return active_backlog


def get_record_by_id(client_id: str) -> Optional[dict]:
    """Tìm hồ sơ theo client_ID từ cả enriched CSV và backlog."""
    # 1. Tìm trong enriched
    for r in read_all_records():
        if r.get("client_ID") == client_id or r.get("application_id") == client_id:
            return r

    # 2. Tìm trong backlog
    for r in read_manual_review_backlog(10000):
        if r.get("client_ID") == client_id or r.get("application_id") == client_id:
            return r

    return None


def save_record(payload: EnrichPayload) -> dict:
    """
    Tạo mới (Create) một hồ sơ vào CSV theo ngày.
    """
    now = datetime.now()
    file_path = get_file_path(now.date())
    
    # Kiểm tra header nếu file đã tồn tại
    write_header = not file_path.exists()
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            if first_line != ",".join(ENRICHED_COLUMNS):
                # Header cũ không khớp, đổi tên backup và tạo mới chuẩn
                backup_p = file_path.with_name(f"{file_path.stem}_old_{int(now.timestamp())}.csv")
                file_path.rename(backup_p)
                write_header = True

    app_data = payload.application.model_dump()
    client_id = generate_client_id(app_data)
    app_id = f"APP-{now.strftime('%y%m%d')}-{client_id[-4:]}"

    row = {
        "application_id":              app_id,
        "client_ID":                   client_id,
        "person_age":                  app_data.get("person_age"),
        "person_income":               app_data.get("person_income"),
        "person_home_ownership":       app_data.get("person_home_ownership"),
        "person_emp_length":           app_data.get("person_emp_length"),
        "loan_intent":                 app_data.get("loan_intent"),
        "loan_grade":                  app_data.get("loan_grade"),
        "loan_amnt":                   app_data.get("loan_amnt"),
        "loan_int_rate":               app_data.get("loan_int_rate"),
        "loan_status":                 payload.loan_status,
        "loan_percent_income":         app_data.get("loan_percent_income"),
        "loan_to_income_ratio":        app_data.get("loan_to_income_ratio"),
        "debt_to_income_ratio":        app_data.get("debt_to_income_ratio"),
        "cb_person_default_on_file":   app_data.get("cb_person_default_on_file"),
        "cb_person_cred_hist_length":  app_data.get("cb_person_cred_hist_length"),
        "gender":                      app_data.get("gender"),
        "marital_status":              app_data.get("marital_status"),
        "education_level":             app_data.get("education_level"),
        "employment_type":             app_data.get("employment_type"),
        "loan_term_months":            app_data.get("loan_term_months", 36),
        "ml_pd_score":                 payload.ml_pd_score,
        "ml_credit_score":             payload.ml_credit_score,
        "ml_decision":                 payload.ml_decision,
        "ml_risk_tier":                payload.ml_risk_tier or "MEDIUM_LOW",
        "top_positive_factors":        json.dumps(payload.top_positive_factors or []),
        "top_negative_factors":        json.dumps(payload.top_negative_factors or []),
        "recommended_interest_rate":   payload.recommended_interest_rate,
        "max_credit_limit":            payload.max_credit_limit,
        "monthly_payment_estimate":    payload.monthly_payment_estimate,
        "total_interest_estimate":     payload.total_interest_estimate,
        "created_at":                  now.isoformat(),
        "record_date":                 now.strftime("%Y-%m-%d"),
        "record_month":                now.strftime("%Y-%m"),
    }

    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    with open(file_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ENRICHED_COLUMNS, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerow(row)

    return {
        "client_ID":      client_id,
        "application_id": app_id,
        "saved_to":       str(file_path.relative_to(DATA_RAW_DIR.parent.parent)),
        "created_at":     row["created_at"],
    }


def update_label(client_id: str, loan_status: int) -> bool:
    """
    Cập nhật nhanh loan_status cho một hồ sơ theo client_ID.
    """
    return update_record_details(client_id, {
        "loan_status": str(loan_status),
        "ml_decision": "APPROVED" if loan_status == 0 else "REJECTED",
    }) is not None


def update_record_details(client_id: str, updates: dict) -> Optional[dict]:
    """
    Cập nhật (Update) chi tiết hồ sơ khoản vay (khoản vay, kỳ hạn, lãi suất, phân hạng, nhãn).
    """
    # 1. Tìm trong enriched CSV
    for f in DATA_RAW_DIR.glob("enriched_loan_data_*.csv"):
        rows: list[dict] = []
        updated_row = None
        with open(f, "r", encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            fieldnames = reader.fieldnames or ENRICHED_COLUMNS
            for row in reader:
                if row.get("client_ID") == client_id or row.get("application_id") == client_id:
                    row.update({k: str(v) for k, v in updates.items() if v is not None})
                    updated_row = _clean_record(row)
                rows.append(row)

        if updated_row:
            with open(f, "w", encoding="utf-8", newline="") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(rows)
            return updated_row

    # 2. Nếu là hồ sơ từ backlog, tạo bản ghi mới trong enriched CSV với các cập nhật
    backlog = read_manual_review_backlog(10000)
    for b in backlog:
        if b.get("client_ID") == client_id or b.get("application_id") == client_id:
            b_copy = dict(b)
            b_copy.update({k: str(v) for k, v in updates.items() if v is not None})
            now = datetime.now()
            file_path = get_file_path(now.date())
            file_exists = file_path.exists()
            with open(file_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=ENRICHED_COLUMNS, extrasaction="ignore")
                if not file_exists:
                    writer.writeheader()
                writer.writerow(b_copy)
            return _clean_record(b_copy)

    return None


def delete_record(client_id: str) -> bool:
    """
    Xóa (Delete) một hồ sơ khoản vay khỏi hệ thống.
    """
    _DELETED_CLIENT_IDS.add(client_id)
    found = False

    # Xóa khỏi file enriched CSV nếu có
    for f in DATA_RAW_DIR.glob("enriched_loan_data_*.csv"):
        rows: list[dict] = []
        file_found = False
        with open(f, "r", encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            fieldnames = reader.fieldnames or ENRICHED_COLUMNS
            for row in reader:
                if row.get("client_ID") == client_id or row.get("application_id") == client_id:
                    file_found = True
                    found = True
                    continue
                rows.append(row)

        if file_found:
            with open(f, "w", encoding="utf-8", newline="") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(rows)

    return True


def build_stats(all_records: list[dict]) -> dict:
    """Tính toán thống kê tổng quan từ danh sách hồ sơ."""
    total = len(all_records)
    n_default = sum(1 for r in all_records if str(r.get("loan_status", "")) == "1")
    n_good = total - n_default
    default_rate = round(n_default / total * 100, 2) if total > 0 else 0.0
    n_files = len(list(DATA_RAW_DIR.glob("enriched_loan_data_*.csv"))) if DATA_RAW_DIR.exists() else 0

    return {
        "total_records":    total,
        "n_good_loan":      n_good,
        "n_default":        n_default,
        "default_rate_pct": default_rate,
        "total_files":      n_files,
        "retrain_threshold": 100,
        "ready_for_retrain": total >= 100,
    }


def export_csv(all_records: list[dict]) -> io.StringIO:
    """Serialize danh sách hồ sơ thành StringIO CSV."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=ENRICHED_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(all_records)
    output.seek(0)
    return output
