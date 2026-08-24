"""
Enrich Service — Business logic cho việc đọc/ghi dữ liệu CSV enriched.
"""
import csv
import io
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from services.api_server.app.schemas.loan import EnrichPayload
from services.api_server.app.utils.hash_utils import (
    get_next_client_id,
    generate_application_id,
)

DATA_RAW_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "raw"

ENRICHED_COLUMNS = [
    "application_id", "client_ID", "person_age", "person_income", "person_home_ownership",
    "person_emp_length", "loan_intent", "loan_grade", "loan_amnt",
    "loan_int_rate", "loan_status", "loan_percent_income",
    "loan_to_income_ratio", "debt_to_income_ratio",
    "cb_person_default_on_file", "cb_person_cred_hist_length",
    "gender", "marital_status", "education_level", "employment_type",
    "ml_pd_score", "ml_credit_score", "ml_decision",
    "created_at", "record_date", "record_month",
]


def get_file_path(target_date: Optional[date] = None) -> Path:
    d = target_date or date.today()
    return DATA_RAW_DIR / f"enriched_loan_data_{d.strftime('%Y%m%d')}.csv"


def read_all_records() -> list[dict]:
    """Đọc toàn bộ file enriched_loan_data_*.csv trong data/raw/."""
    all_records: list[dict] = []
    if not DATA_RAW_DIR.exists():
        return all_records
    for f in sorted(DATA_RAW_DIR.glob("enriched_loan_data_*.csv"), reverse=True):
        try:
            with open(f, "r", encoding="utf-8") as csv_file:
                for row in csv.DictReader(csv_file):
                    r = dict(row)
                    r["display_client_ID"] = r.get("client_ID", "")
                    all_records.append(r)
        except Exception:
            continue
    return all_records


def save_record(payload: EnrichPayload) -> dict:
    """Lưu hồ sơ vào CSV với Client ID chuẩn CUST_... và Application ID."""
    now = datetime.now()
    file_path = get_file_path(now.date())
    file_exists = file_path.exists()

    app_data = payload.application.model_dump()
    existing_count = len(read_all_records())
    raw_client_id = app_data.get("client_ID") or get_next_client_id(offset=existing_count)
    application_id = generate_application_id(raw_client_id, channel="O")

    row = {
        "application_id":           application_id,
        "client_ID":                raw_client_id,
        "person_age":               app_data.get("person_age"),
        "person_income":            app_data.get("person_income"),
        "person_home_ownership":    app_data.get("person_home_ownership"),
        "person_emp_length":        app_data.get("person_emp_length"),
        "loan_intent":              app_data.get("loan_intent"),
        "loan_grade":               app_data.get("loan_grade"),
        "loan_amnt":                app_data.get("loan_amnt"),
        "loan_int_rate":            app_data.get("loan_int_rate"),
        "loan_status":              payload.loan_status,
        "loan_percent_income":      app_data.get("loan_percent_income"),
        "loan_to_income_ratio":     app_data.get("loan_to_income_ratio"),
        "debt_to_income_ratio":     app_data.get("debt_to_income_ratio"),
        "cb_person_default_on_file":   app_data.get("cb_person_default_on_file"),
        "cb_person_cred_hist_length":  app_data.get("cb_person_cred_hist_length"),
        "gender":                   app_data.get("gender"),
        "marital_status":           app_data.get("marital_status"),
        "education_level":          app_data.get("education_level"),
        "employment_type":          app_data.get("employment_type"),
        "ml_pd_score":              payload.ml_pd_score,
        "ml_credit_score":          payload.ml_credit_score,
        "ml_decision":              payload.ml_decision,
        "created_at":               now.isoformat(),
        "record_date":              now.strftime("%Y-%m-%d"),
        "record_month":             now.strftime("%Y-%m"),
    }

    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    with open(file_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ENRICHED_COLUMNS, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    return {
        "client_ID":       raw_client_id,
        "application_id":  application_id,
        "saved_to":        str(file_path.relative_to(DATA_RAW_DIR.parent.parent)),
        "created_at":      row["created_at"],
    }


def update_label(client_id: str, loan_status: int) -> bool:
    """
    Cập nhật loan_status cho một hồ sơ theo client_ID.

    Returns:
        True nếu tìm thấy và cập nhật thành công, False nếu không tìm thấy.
    """
    for f in DATA_RAW_DIR.glob("enriched_loan_data_*.csv"):
        rows: list[dict] = []
        found = False
        with open(f, "r", encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            fieldnames = reader.fieldnames or ENRICHED_COLUMNS
            for row in reader:
                if row.get("client_ID") == client_id:
                    row["loan_status"] = str(loan_status)
                    found = True
                rows.append(row)

        if found:
            with open(f, "w", encoding="utf-8", newline="") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            return True

    return False


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
