import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, List, Dict, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)

class CreditDataValidator:
    """
    Data Quality Gateway for Credit Risk dataset.
    Provides scanning/reporting for the Extract phase and segregation for the Transform phase.
    """

    def __init__(self) -> None:
        """
        Initializes the validator with a set of modular business rules.
        """
        self.rules = [
            {"id": "R1_AGE", "desc": "Age must be between 18 and 85", "check": lambda df: df['person_age'].between(18, 85)},
            {"id": "R2_EXPERIENCE", "desc": "Employment length cannot exceed (Age - 18)", "check": lambda df: df['person_emp_length'] <= (df['person_age'] - 18)},
            {"id": "R3_CREDIT_HIST", "desc": "Credit history length cannot exceed (Age - 18)", "check": lambda df: df['cb_person_cred_hist_length'] <= (df['person_age'] - 18)},
            {"id": "R4_FINANCIALS", "desc": "Income and Loan amount must be > 0", "check": lambda df: (df['person_income'] > 0) & (df['loan_amnt'] > 0)},
            {"id": "R5_UTILIZATION", "desc": "Credit utilization ratio must be between 0 and 1", "check": lambda df: df['credit_utilization_ratio'].between(0, 1)},
            {"id": "R6_RATIO_SYNC", "desc": "Calculated loan-to-income ratio mismatch (> 0.01 error)", "check": lambda df: ((df['loan_amnt'] / df['person_income'] - df['loan_to_income_ratio']).abs() <= 0.01)},
            {"id": "R7_DTI_LOGIC", "desc": "Debt-to-income ratio must be >= loan percent income", "check": lambda df: df['debt_to_income_ratio'] >= df['loan_percent_income']}
        ]

    def _get_validation_results(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Internal method to apply rules vectorially and return the mask of passed records.
        """
        results_df = pd.DataFrame({
            rule["id"]: self._apply_rule(df, rule) for rule in self.rules
        })
        passed_all = results_df.all(axis=1)
        return results_df, passed_all

    def _apply_rule(self, df: pd.DataFrame, rule: Dict[str, Any]) -> pd.Series:
        try:
            return rule["check"](df).fillna(False).astype(bool)
        except Exception as e:
            logger.error(f"Error applying rule {rule['id']}: {e}")
            return pd.Series(False, index=df.index)

    def _calculate_violation_notes(self, df: pd.DataFrame, results_df: pd.DataFrame) -> pd.Series:
        """
        Constructs a human-readable string of violations for each failed record.
        """
        violation_notes = pd.Series("", index=df.index)
        for rule in self.rules:
            failed_mask = ~results_df[rule["id"]]
            violation_notes.loc[failed_mask] += f"[{rule['id']}: {rule['desc']}] "
        return violation_notes

    def report_issues(self, df: pd.DataFrame, report_path: str = "docs/data_issuses.txt") -> bool:
        """
        Feature 1: Scans data and generates a structured Data Quality Scan Report.
        Typically used during the Extract process.
        """
        logger.info(f"Scanning {len(df)} records for issues...")
        
        try:
            results_df, passed_all = self._get_validation_results(df)
            df_quarantine = df[~passed_all].copy()
            
            report_file = Path(report_path)
            report_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(report_file, mode='w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write(f"DATA QUALITY SCAN REPORT - {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*80 + "\n\n")
                
                total_records = len(df)
                quarantine_count = len(df_quarantine)
                
                f.write("EXECUTIVE SUMMARY:\n")
                f.write("-" * 18 + "\n")
                f.write(f"Total Records Scanned: {total_records}\n")
                f.write(f"Issues Found:          {quarantine_count}\n")
                f.write(f"Issue Rate:            {(quarantine_count / total_records * 100):.2f}%\n\n")
                
                f.write("DETAILED FINDINGS:\n")
                f.write("-" * 18 + "\n")
                
                if quarantine_count > 0:
                    violation_notes = self._calculate_violation_notes(df_quarantine, results_df.loc[df_quarantine.index])
                    id_col = 'client_ID' if 'client_ID' in df_quarantine.columns else None
                    for row in df_quarantine.itertuples():
                        client_id = getattr(row, id_col) if id_col else 'N/A'
                        f.write(f"Row: {row.Index:6} | Client_ID: {client_id:10} | Violations: {violation_notes.loc[row.Index]}\n")
                else:
                    f.write("No issues detected.\n")
                
                f.write("\n" + "="*80 + "\n")
                f.write("END OF SCAN REPORT\n")
                f.write("="*80 + "\n")
            
            logger.info(f"Scanner report generated at {report_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to generate scanner report: {e}", exc_info=True)
            return False

    def segregate_and_save(self, df: pd.DataFrame, output_dir: str = "data/processed") -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Feature 2: Segregates valid and invalid records and saves them to the processed directory.
        Typically used during the Transform process.
        """
        logger.info(f"Segregating {len(df)} records into clean and quarantine datasets...")
        
        try:
            results_df, passed_all = self._get_validation_results(df)
            df_clean = df[passed_all].copy()
            df_quarantine = df[~passed_all].copy()
            
            # Attach violation notes to quarantine data for context
            if not df_quarantine.empty:
                df_quarantine['violation_notes'] = self._calculate_violation_notes(df_quarantine, results_df.loc[df_quarantine.index])
            
            # Ensure output directory exists
            out_path = Path(output_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            
            # Save files
            clean_file = out_path / "df_clean.csv"
            quarantine_file = out_path / "df_quarantine.csv"
            
            df_clean.to_csv(clean_file, index=False)
            df_quarantine.to_csv(quarantine_file, index=False)
            
            logger.info(f"Data segregated. Clean: {len(df_clean)} records, Quarantine: {len(df_quarantine)} records.")
            logger.info(f"Files saved to {out_path.resolve()}")
            
            return df_clean, df_quarantine
        except Exception as e:
            logger.error(f"Failed to segregate and save data: {e}", exc_info=True)
            raise
