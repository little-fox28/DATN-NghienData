import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_rules() -> list:
    rules_path = Path(__file__).parent / "DQ_rules.json"
    try:
        with open(rules_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load DQ rules from {rules_path}: {e}")
        return []


RULES = load_rules()


class CreditDataValidator:
    """
    Data Quality Gateway for Credit Risk dataset.
    Provides scanning/reporting for the Extract phase and segregation for the Transform phase.
    """

    def __init__(self) -> None:
        """
        Initializes the validator with a set of modular business rules.
        """
        self.rules = RULES

    def _prepare_validation_df(self, df):
        validated_df = df.copy()
        # Prevent ZeroDivisionError for R6
        validated_df["calc_loan_to_income"] = np.where(
            validated_df["person_income"] > 0,
            validated_df["loan_amnt"] / validated_df["person_income"],
            np.nan
        )
        return validated_df

    def _get_validation_results(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Internal method to apply rules vectorially and return the mask of passed records.
        """
        df_prepared = self._prepare_validation_df(df)
        results_df = pd.DataFrame(
            {rule["id"]: self._apply_rule(df_prepared, rule) for rule in self.rules}
        )
        passed_all = results_df.all(axis=1)
        return results_df, passed_all

    def _apply_rule(self, df: pd.DataFrame, rule: Dict[str, Any]) -> pd.Series:
        try:
            # Step 1: Apply fallback computation (fill_expr) if field is null
            # If computation also yields NaN, the check will fail → record marked critical
            if "fill_target" in rule and "fill_expr" in rule:
                df = df.copy()
                fill_target = rule["fill_target"]
                null_mask = df[fill_target].isna()
                if null_mask.any():
                    computed = eval(rule["fill_expr"], {"df": df, "np": np})
                    if hasattr(computed, "__len__"):
                        df.loc[null_mask, fill_target] = pd.Series(computed, index=df.index)[null_mask]
                    else:
                        df.loc[null_mask, fill_target] = computed
                    filled_count = null_mask.sum() - df[fill_target].isna().sum()
                    if filled_count > 0:
                        logger.info(
                            f"[{rule['id']}] Auto-filled {filled_count} missing '{fill_target}' "
                            f"value(s) via fallback computation."
                        )

            # Step 2: Run the check expression
            check_expr = rule["check"]
            if isinstance(check_expr, str):
                return eval(check_expr, {"df": df, "np": np}).fillna(False).astype(bool)
            return rule["check"](df).fillna(False).astype(bool)
        except Exception as e:
            logger.error(f"Error applying rule {rule['id']}: {e}")
            return pd.Series(False, index=df.index)

    def _calculate_violation_notes(
        self, df: pd.DataFrame, results_df: pd.DataFrame
    ) -> pd.Series:
        """
        Constructs a human-readable string of violations for each failed record.
        """
        violation_notes = pd.Series("", index=df.index)
        for rule in self.rules:
            failed_mask = ~results_df[rule["id"]]
            violation_notes.loc[failed_mask] += f"[{rule['id']}: {rule['desc']}] "
        return violation_notes

    def calculate_status(self, df: pd.DataFrame, results_df: pd.DataFrame) -> pd.Series:
        """
        Calculates status ('pass', 'warning', 'critical') for each record vectorially.
        """
        critical_rule_ids = [rule["id"] for rule in self.rules if rule.get("severity") == "critical"]
        warning_rule_ids = [rule["id"] for rule in self.rules if rule.get("severity") == "warning"]

        # A rule violation is denoted by False in results_df
        is_critical = ~results_df[critical_rule_ids].all(axis=1) if critical_rule_ids else pd.Series(False, index=df.index)
        is_warning = ~is_critical & (~results_df[warning_rule_ids].all(axis=1) if warning_rule_ids else pd.Series(False, index=df.index))

        status = pd.Series("pass", index=df.index)
        status[is_warning] = "warning"
        status[is_critical] = "critical"
        return status

    def report_issues(
        self, df: pd.DataFrame, report_path: str = "docs/03_notes/engineering/data_issues.txt"
    ) -> bool:
        """
        Feature 1: Scans data and generates a structured Data Quality Scan Report.
        Typically used during the Extract process.
        """
        report_file = Path(report_path)
        if report_file.exists():
            logger.info(f"Quality report already exists at {report_path}. Skipping scan to optimize performance.")
            return True

        logger.info(f"Scanning {len(df)} records for issues...")

        try:
            results_df, passed_all = self._get_validation_results(df)
            status_series = self.calculate_status(df, results_df)
            df_quarantine = df[~passed_all].copy()

            report_file.parent.mkdir(parents=True, exist_ok=True)

            with open(report_file, mode="w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write(
                    f"DATA QUALITY SCAN REPORT \n"
                )
                f.write("=" * 80 + "\n\n")

                total_records = len(df)
                quarantine_count = len(df_quarantine)
                
                # Count status values
                status_counts = status_series.value_counts()
                pass_count = status_counts.get("pass", 0)
                warning_count = status_counts.get("warning", 0)
                critical_count = status_counts.get("critical", 0)
                clean_count = pass_count + warning_count

                f.write("EXECUTIVE SUMMARY:\n")
                f.write("-" * 18 + "\n")
                f.write(f"Total Records Scanned: {total_records}\n")
                f.write(f"Issues Found:          {quarantine_count}\n")
                f.write(
                    f"Issue Rate:            {(quarantine_count / total_records * 100):.2f}%\n\n"
                )
                f.write("DATA QUALITY STATUS BREAKDOWN:\n")
                f.write(f"  - PASS:     {pass_count:6} records ({(pass_count / total_records * 100):.2f}%)\n")
                f.write(f"  - WARNING:  {warning_count:6} records ({(warning_count / total_records * 100):.2f}%)\n")
                f.write(f"  - CRITICAL: {critical_count:6} records ({(critical_count / total_records * 100):.2f}%)\n\n")

                f.write("RULE VIOLATION BREAKDOWN:\n")
                for rule in self.rules:
                    rule_id = rule["id"]
                    failed_count = int((~results_df[rule_id]).sum())
                    if failed_count > 0:
                        f.write(f"  - {rule_id}: {failed_count} records ({(failed_count / total_records * 100):.2f}%)\n")
                f.write("\n")

                f.write("OUTPUT DATASET SUMMARY:\n")
                f.write(f"  - Output Records (PASS + WARNING): {clean_count:6} records ({(clean_count / total_records * 100):.2f}%)\n")
                f.write(f"  - Destination File:               data/output/df_output.csv\n\n")

                f.write("DETAILED FINDINGS:\n")
                f.write("-" * 18 + "\n")

                if quarantine_count > 0:
                    violation_notes = self._calculate_violation_notes(
                        df_quarantine, results_df.loc[df_quarantine.index]
                    )
                    id_col = (
                        "client_ID" if "client_ID" in df_quarantine.columns else None
                    )
                    for row in df_quarantine.itertuples():
                        client_id = getattr(row, id_col) if id_col else "N/A"
                        f.write(
                            f"Row: {row.Index:6} | Client_ID: {client_id:10} | Violations: {violation_notes.loc[row.Index]}\n"
                        )
                else:
                    f.write("No issues detected.\n")

                f.write("\n" + "=" * 80 + "\n")
                f.write("END OF SCAN REPORT\n")
                f.write("=" * 80 + "\n")

            logger.info(f"Scanner report generated at {report_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to generate scanner report: {e}", exc_info=True)
            return False

    def segregate_and_save(
        self, df: pd.DataFrame, output_dir: str = "data/processed"
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Feature 2: Segregates valid and invalid records based on Data Quality Tiers
        and saves them to the processed directory.
        Typically used during the Transform process.
        """
        logger.info(
            f"Segregating {len(df)} records into tier-based datasets..."
        )

        try:
            results_df, _ = self._get_validation_results(df)
            
            # Calculate status column vectorially
            status_series = self.calculate_status(df, results_df)
            
            df_with_status = df.copy()
            df_with_status["status"] = status_series
            
            # Segregate based on status
            df_pass = df_with_status[df_with_status["status"] == "pass"].copy()
            df_warning = df_with_status[df_with_status["status"] == "warning"].copy()
            df_critical = df_with_status[df_with_status["status"] == "critical"].copy()
            
            # df_clean contains pass and warning records
            df_clean = df_with_status[df_with_status["status"].isin(["pass", "warning"])].copy()
            
            # Ensure output directory exists
            out_path = Path(output_dir)
            out_path.mkdir(parents=True, exist_ok=True)

            # Save files
            df_pass.to_csv(out_path / "df_pass.csv", index=False)
            df_warning.to_csv(out_path / "df_warning.csv", index=False)
            df_critical.to_csv(out_path / "df_critical.csv", index=False)
            
            # Save df_output.csv to data/output
            output_path = Path("data/output")
            output_path.mkdir(parents=True, exist_ok=True)
            df_clean.to_csv(output_path / "df_output.csv", index=False)

            logger.info("Data segregated and saved:")
            logger.info(f"  - In {out_path.resolve()}:")
            logger.info(f"    * df_pass.csv: {len(df_pass)} records")
            logger.info(f"    * df_warning.csv: {len(df_warning)} records")
            logger.info(f"    * df_critical.csv: {len(df_critical)} records")
            logger.info(f"  - In {output_path.resolve()}:")
            logger.info(f"    * df_output.csv (pass + warning): {len(df_clean)} records")

            return df_clean, df_critical
        except Exception as e:
            logger.error(f"Failed to segregate and save data: {e}", exc_info=True)
            raise
