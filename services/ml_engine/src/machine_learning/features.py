"""
Tầng 2: Trích xuất Đặc trưng (Feature Engineering).

Implement WoE (Weight of Evidence) Binner thủ công — không phụ thuộc thư viện ngoài,
hoàn toàn kiểm soát logic, phù hợp với chuẩn Credit Scorecard ngân hàng.

Phương pháp:
    WoE_i = ln( P(Non-Default in Bin_i) / P(Default in Bin_i) )
           = ln( (n_nonevent_i / N_nonevent) / (n_event_i / N_event) )

    IV_i   = (P(Non-Default in Bin_i) - P(Default in Bin_i)) × WoE_i

Xử lý đặc biệt:
    - NaN: Gom thành bin "Missing" riêng (không điền tùy tiện)
    - Biến phân loại: Mỗi category → 1 bin → tính WoE
    - Biến số: Chia bin tự động bằng pd.qcut (quantile), sau đó tính WoE
"""
import pickle
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class WoEBinner:
    """
    WoE Binner thủ công theo chuẩn Credit Scorecard.

    Lý do tự implement thay vì dùng thư viện:
    - Hoàn toàn kiểm soát logic → dễ debug, dễ giải thích với hội đồng
    - Không phụ thuộc phiên bản scikit-learn (tránh breaking changes)
    - Cho phép custom bin boundaries theo yêu cầu BA trong tương lai
    """

    def __init__(self, n_bins: int = 5):
        self.n_bins = n_bins
        self.woe_maps: dict[str, dict] = {}   # {feature: {bin_label: woe_value}}
        self.iv_table: dict[str, float] = {}  # {feature: total_iv}
        self.bin_edges: dict[str, list] = {}  # {numerical_feature: [edges]}
        self.fitted = False

    def fit(self, X: pd.DataFrame, y: pd.Series,
            numerical_cols: list[str], categorical_cols: list[str]) -> "WoEBinner":
        """Fit WoE bins trên tập training."""
        all_cols = [c for c in (numerical_cols + categorical_cols) if c in X.columns]
        N_event    = max(y.sum(), 1)
        N_nonevent = max((1 - y).sum(), 1)

        logger.info(f"Fitting WoE Binner: {N_event:.0f} defaults / {N_nonevent:.0f} non-defaults")
        logger.info(f"Features to bin: {all_cols}")

        for col in all_cols:
            if col in categorical_cols:
                self._fit_categorical(X[col], y, col, N_event, N_nonevent)
            else:
                self._fit_numerical(X[col], y, col, N_event, N_nonevent)

        self.fitted = True
        self._log_iv_table()
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Chuyển đổi sang không gian WoE."""
        if not self.fitted:
            raise ValueError("WoEBinner chưa được fit. Hãy gọi fit() trước.")

        X_out = X.copy()
        for col, woe_map in self.woe_maps.items():
            if col not in X_out.columns:
                X_out[col] = np.nan

            if col in self.bin_edges:
                # Biến số: bin theo edges đã lưu
                X_out[col] = self._transform_numerical(X_out[col], col, woe_map)
            else:
                # Biến phân loại: map trực tiếp
                X_out[col] = self._transform_categorical(X_out[col], woe_map)

        return X_out

    # ── FIT INTERNALS ────────────────────────────────────────────────────────

    def _fit_numerical(self, series: pd.Series, y: pd.Series,
                       col: str, N_event: float, N_nonevent: float):
        """Chia bin quantile cho biến số, xử lý NaN thành bin "Missing"."""
        # Tách NaN ra xử lý riêng
        mask_valid = series.notna()
        s_valid = series[mask_valid]
        y_valid = y[mask_valid]
        s_nan   = series[~mask_valid]
        y_nan   = y[~mask_valid]

        # Chia bin bằng quantile (bỏ duplicates nếu có)
        n_bins = min(self.n_bins, s_valid.nunique())
        try:
            binned, edges = pd.qcut(s_valid, q=n_bins, retbins=True, duplicates="drop")
        except Exception:
            # Fallback: dùng pd.cut với 3 bins nếu qcut thất bại
            try:
                binned, edges = pd.cut(s_valid, bins=3, retbins=True)
            except Exception:
                logger.warning(f"Không thể chia bin cho '{col}', gán WoE=0.")
                self.woe_maps[col] = {"__default__": 0.0}
                self.iv_table[col] = 0.0
                return

        self.bin_edges[col] = list(edges)

        woe_map = {}
        iv_total = 0.0

        for bin_label in binned.cat.categories:
            mask_bin = (binned == bin_label)
            n_ev     = max(y_valid[mask_bin].sum(), 0.5)
            n_nonev  = max((1 - y_valid[mask_bin]).sum(), 0.5)
            woe, iv_bin = self._calc_woe_iv(n_ev, n_nonev, N_event, N_nonevent)
            woe_map[str(bin_label)] = round(woe, 6)
            iv_total += iv_bin

        # Bin "Missing"
        if len(s_nan) > 0:
            n_ev_nan    = max(y_nan.sum(), 0.5)
            n_nonev_nan = max((1 - y_nan).sum(), 0.5)
            woe_nan, iv_nan = self._calc_woe_iv(n_ev_nan, n_nonev_nan, N_event, N_nonevent)
            woe_map["__missing__"] = round(woe_nan, 6)
            iv_total += iv_nan
            logger.info(f"  [{col}] Missing bin: {len(s_nan)} records, WoE={woe_nan:.4f}")

        self.woe_maps[col] = woe_map
        self.iv_table[col] = round(iv_total, 6)

    def _fit_categorical(self, series: pd.Series, y: pd.Series,
                         col: str, N_event: float, N_nonevent: float):
        """Tính WoE cho từng category của biến phân loại."""
        woe_map = {}
        iv_total = 0.0

        # Xử lý NaN
        mask_null = series.isna()
        if mask_null.sum() > 0:
            n_ev_nan    = max(y[mask_null].sum(), 0.5)
            n_nonev_nan = max((1 - y[mask_null]).sum(), 0.5)
            woe_nan, iv_nan = self._calc_woe_iv(n_ev_nan, n_nonev_nan, N_event, N_nonevent)
            woe_map["__missing__"] = round(woe_nan, 6)
            iv_total += iv_nan

        # Xử lý từng category
        for cat in series.dropna().unique():
            mask_cat = (series == cat)
            n_ev    = max(y[mask_cat].sum(), 0.5)
            n_nonev = max((1 - y[mask_cat]).sum(), 0.5)
            woe, iv_bin = self._calc_woe_iv(n_ev, n_nonev, N_event, N_nonevent)
            woe_map[str(cat)] = round(woe, 6)
            iv_total += iv_bin

        self.woe_maps[col] = woe_map
        self.iv_table[col] = round(iv_total, 6)

    @staticmethod
    def _calc_woe_iv(n_event: float, n_nonevent: float,
                     N_event: float, N_nonevent: float) -> tuple[float, float]:
        """Tính WoE và đóng góp IV của một bin."""
        p_event    = n_event    / N_event
        p_nonevent = n_nonevent / N_nonevent
        woe = np.log(p_nonevent / p_event)
        iv  = (p_nonevent - p_event) * woe
        return woe, iv

    # ── TRANSFORM INTERNALS ──────────────────────────────────────────────────

    def _transform_numerical(self, series: pd.Series, col: str, woe_map: dict) -> pd.Series:
        """Map giá trị số sang WoE."""
        edges = self.bin_edges[col]
        result = pd.Series(np.nan, index=series.index)

        mask_nan = series.isna()
        result[mask_nan] = woe_map.get("__missing__", 0.0)

        s_valid = series[~mask_nan]
        if len(s_valid) == 0:
            return result

        # Bin theo edges đã lưu
        binned = pd.cut(s_valid, bins=edges, include_lowest=True)
        for bin_label, woe_val in woe_map.items():
            if bin_label in ("__missing__", "__default__"):
                continue
            try:
                mask_bin = (binned.astype(str) == bin_label)
                result[s_valid.index[mask_bin]] = woe_val
            except Exception:
                pass

        # Điền WoE mặc định cho giá trị nằm ngoài bin (out-of-range)
        default_woe = woe_map.get("__default__", 0.0)
        result.fillna(default_woe, inplace=True)
        return result

    def _transform_categorical(self, series: pd.Series, woe_map: dict) -> pd.Series:
        """Map category sang WoE."""
        missing_woe = woe_map.get("__missing__", 0.0)
        default_woe = woe_map.get("__default__", 0.0)
        return series.map(
            lambda v: missing_woe if pd.isna(v) else woe_map.get(str(v), default_woe)
        )

    def _log_iv_table(self):
        """Log bảng IV để kiểm tra chất lượng biến sau khi fit."""
        iv_sorted = sorted(self.iv_table.items(), key=lambda x: x[1], reverse=True)
        logger.info("\n" + "=" * 45)
        logger.info("  INFORMATION VALUE (IV) TABLE")
        logger.info("  IV > 0.5: Cực mạnh | > 0.3: Mạnh | > 0.1: Trung bình | < 0.02: Yếu")
        logger.info("=" * 45)
        for feat, iv in iv_sorted:
            strength = ("Cực mạnh" if iv > 0.5 else
                        "Mạnh"     if iv > 0.3 else
                        "Trung bình" if iv > 0.1 else
                        "Yếu")
            logger.info(f"  {feat:<30} IV={iv:.4f}  ({strength})")
        logger.info("=" * 45)


# ═══════════════════════════════════════════════════════════════════════════════


class FeatureEngineer:
    """
    Class đảm nhiệm việc mã hóa biến bằng WoE Binning.

    Kiến trúc "Model-based Score Scaling":
        Dữ liệu → WoE Transform → XGBoost (PD) → FICO Score
                       ↓
             WoE Contribution (giải thích từng biến)

    Ưu điểm so với OrdinalEncoder:
    - Supervised encoding: mỗi bin phản ánh trực tiếp mức độ rủi ro Default
    - Tự động gom NaN vào nhóm "Missing" (không điền tùy tiện)
    - Cho phép tính đóng góp từng biến theo công thức BA (Explainability)
    - Không phụ thuộc thư viện ngoài → ổn định với mọi phiên bản sklearn
    """

    def __init__(self, config: dict):
        """Khởi tạo với cấu hình bài toán."""
        self.config = config
        self.cat_cols         = self.config.get("categorical_cols", [])
        self.num_cols         = self.config.get("numerical_cols", [])
        self.encoder_artifact = self.config.get("encoder_artifact_abs")
        self.encoder: Optional[WoEBinner] = None

    # ── PUBLIC API ──────────────────────────────────────────────────────────

    def build_encoder(self, X_train: pd.DataFrame, y_train: pd.Series) -> WoEBinner:
        """
        Fit WoE Binner trên tập Training.

        Args:
            X_train: DataFrame các biến đầu vào (10 biến đã chọn theo BA).
            y_train: Series nhãn nhị phân (1=Default, 0=Non-Default).
        """
        logger.info("Building WoE Binner (Credit Scorecard standard)...")
        self.encoder = WoEBinner(n_bins=5)
        self.encoder.fit(X_train, y_train,
                         numerical_cols=self.num_cols,
                         categorical_cols=self.cat_cols)
        return self.encoder

    def save_encoder(self) -> None:
        """Lưu WoE Binner ra artifact (.pkl)."""
        if self.encoder is None:
            raise ValueError("Encoder chưa được build. Hãy chạy build_encoder() trước.")

        path_obj = Path(self.encoder_artifact)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        with open(path_obj, "wb") as f:
            pickle.dump(self.encoder, f)
        logger.info(f"WoE Binner saved to: {self.encoder_artifact}")

    def load_encoder(self) -> WoEBinner:
        """Tải WoE Binner từ artifact (.pkl)."""
        path_obj = Path(self.encoder_artifact)
        if not path_obj.exists():
            raise FileNotFoundError(
                f"Encoder artifact không tìm thấy: {self.encoder_artifact}. "
                "Hãy chạy: python -m services.ml_engine.src.machine_learning.pipeline --task credit_risk"
            )
        with open(path_obj, "rb") as f:
            self.encoder = pickle.load(f)
        logger.info(f"WoE Binner loaded from: {self.encoder_artifact}")
        return self.encoder

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Chuyển đổi dữ liệu sang không gian WoE."""
        if self.encoder is None:
            raise ValueError("Encoder chưa được load. Hãy chạy load_encoder() trước.")

        X_proc = self._prepare_features(X)
        return self.encoder.transform(X_proc)

    def transform_with_contributions(self, X: pd.DataFrame,
                                     score_factor: float = 72.13) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Chuyển đổi WoE + tính đóng góp điểm của từng biến.

        Công thức BA (Mục 4): Points_i = Round(WoE_i × score_factor / 10)

        Returns:
            (X_woe, contributions_df)
        """
        X_woe = self.transform(X)
        all_feature_cols = [c for c in (self.num_cols + self.cat_cols) if c in X_woe.columns]
        contributions = X_woe[all_feature_cols].apply(
            lambda col: col.apply(lambda woe: round(float(woe) * score_factor / 10, 2))
        )
        contributions.columns = [f"{c}_pts" for c in contributions.columns]
        return X_woe, contributions

    # ── PRIVATE ─────────────────────────────────────────────────────────────

    def _prepare_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """Chuẩn bị DataFrame: đảm bảo đủ các cột cần thiết."""
        X_out = X.copy()
        for col in self.cat_cols:
            if col not in X_out.columns:
                X_out[col] = np.nan
                logger.warning(f"Cột phân loại '{col}' thiếu trong input, gán NaN (→ bin 'Missing').")
        for col in self.num_cols:
            if col not in X_out.columns:
                X_out[col] = np.nan
                logger.warning(f"Cột số '{col}' thiếu trong input, gán NaN (→ bin 'Missing').")
        return X_out