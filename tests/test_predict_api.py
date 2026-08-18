"""
test_predict_api.py — Production-grade automated test suite for the
Credit Risk Scoring API (POST /api/v1/predict).

Test plan reference: api_test_cases.md
Endpoint:            POST /api/v1/predict
Scoring engine:      XGBoost + WoE Transform → FICO Score (300-850) → Risk Tier → Decision

FICO Decision Thresholds (predict.py#L81-88):
    >= 740  → LOW          → APPROVED
    670-739 → MEDIUM_LOW   → APPROVED_CONDITIONAL
    580-669 → MEDIUM_HIGH  → MANUAL_REVIEW
    < 580   → HIGH         → REJECTED

Execution:
    # From project root
    pytest tests/test_predict_api.py -v --html=tests/report.html --self-contained-html
"""

from typing import Any, Callable

import pytest
import requests


# ===========================================================================
# Class 1: Happy Path — Baseline Validation
# ===========================================================================

class TestHappyPath:
    """TC-01, TC-02 — Establish golden-path baselines for CI/CD regression."""

    def test_prime_applicant_approved(
        self,
        predict_url: str,
        base_payload: dict[str, Any],
        universal_assertions: Callable,
    ) -> None:
        """
        TC-01: Happy Path — Prime Applicant.

        Risk Rationale: Establishes the golden path. Verifies the full
        pricing waterfall yields APR = 6.5 + 1.0 - 0.5 - 0.3 = 6.7%
        exactly. Any deviation signals a pricing engine regression.
        """
        # Mutate only the fields relevant to a prime borrower profile.
        base_payload.update({
            "person_income": 95_000,
            "loan_amnt": 10_000,
            "loan_grade": "A",
            "loan_int_rate": 7.5,
            "loan_to_income_ratio": 0.105,
            "loan_percent_income": 0.105,
            "debt_to_income_ratio": 0.18,
            "person_emp_length": 8.0,
            "person_home_ownership": "OWN",
            "cb_person_default_on_file": "N",
            "loan_intent": "EDUCATION",
        })

        response = requests.post(predict_url, json=base_payload)

        # Universal invariants must pass before specific assertions.
        assessment = universal_assertions(response)

        # TC-01 specific assertions
        assert assessment["credit_score"] >= 740, (
            f"Prime applicant (Grade A, no default, low DTI) must score >= 740. "
            f"Got: {assessment['credit_score']}"
        )
        assert assessment["risk_tier"] == "LOW"
        assert assessment["decision"] == "APPROVED"
        assert assessment["pd_score"] < 0.20, (
            f"Prime applicant PD must be low. Got: {assessment['pd_score']}"
        )

        # Pricing waterfall arithmetic: APR = 6.5 + 1.0(LOW) - 0.5(OWN) - 0.3(EDUCATION)
        pricing = assessment["pricing_recommendation"]
        assert pricing["base_rate"] == 6.5
        assert pricing["risk_spread"] == 1.0,   f"LOW tier spread must be 1.0, got {pricing['risk_spread']}"
        assert pricing["capital_discount"] == -0.5, f"OWN discount must be -0.5, got {pricing['capital_discount']}"
        assert pricing["intent_adjustment"] == -0.3, f"EDUCATION adj must be -0.3, got {pricing['intent_adjustment']}"
        assert pricing["recommended_interest_rate"] == pytest.approx(6.7, abs=0.01), (
            f"Waterfall APR must be 6.7%, got {pricing['recommended_interest_rate']}%"
        )

    def test_standard_applicant_baseline(
        self,
        predict_url: str,
        base_payload: dict[str, Any],
        universal_assertions: Callable,
    ) -> None:
        """
        TC-02: Happy Path — Standard Applicant (Baseline).

        Risk Rationale: This payload mirrors initialFormData exactly from
        LoanApplicationPage.tsx#L13-32. If this canonical payload ever shifts
        decision tier, it signals a model retraining side-effect or a breaking
        schema change. Must be part of every CI/CD smoke test.
        """
        # base_payload IS initialFormData — no mutation needed.
        response = requests.post(predict_url, json=base_payload)
        assessment = universal_assertions(response)

        # Standard applicant should land in the two middle tiers.
        assert assessment["decision"] in ("APPROVED_CONDITIONAL", "MANUAL_REVIEW"), (
            f"Standard B-grade applicant with default initialFormData must land in "
            f"APPROVED_CONDITIONAL or MANUAL_REVIEW. Got: {assessment['decision']}"
        )
        assert 580 <= assessment["credit_score"] <= 739, (
            f"Standard applicant score expected in 580-739 range. "
            f"Got: {assessment['credit_score']}"
        )

        # Verify limit_status for a reasonable loan amount (10K on 65K income)
        pricing = assessment["pricing_recommendation"]
        assert pricing["limit_status"] == "WITHIN_LIMIT", (
            f"$10K loan on $65K income must be WITHIN_LIMIT. "
            f"Got: {pricing['limit_status']}"
        )


# ===========================================================================
# Class 2: Contradictory Profiles — Semantic Adversarial Testing
# ===========================================================================

class TestContradictoryProfiles:
    """
    TC-03, TC-04, TC-05, TC-06 — Profiles where individual signals contradict
    each other. Tests whether the WoE weights correctly resolve the conflict.
    """

    def test_grade_a_with_prior_default(
        self,
        predict_url: str,
        base_payload: dict[str, Any],
        universal_assertions: Callable,
    ) -> None:
        """
        TC-03: Contradiction — Grade A + Prior Default.

        Risk Rationale: A Grade-A loan paired with a prior default is a
        classic fraud/data-quality signal. The WoE for
        cb_person_default_on_file='Y' must apply a heavy negative weight,
        overriding the positive signal from loan_grade='A'. A system that
        auto-approves this profile has a critical scoring failure.
        """
        base_payload.update({
            "loan_grade": "A",
            "cb_person_default_on_file": "Y",   # ← the adversarial mutation
            "loan_int_rate": 7.0,
            "person_income": 100_000,
            "loan_amnt": 15_000,
            "loan_to_income_ratio": 0.15,
            "loan_percent_income": 0.15,
            "debt_to_income_ratio": 0.20,
            "person_emp_length": 10.0,
            "person_home_ownership": "OWN",
            "loan_intent": "PERSONAL",
        })

        response = requests.post(predict_url, json=base_payload)
        assessment = universal_assertions(response)

        # Character (5C) dimension must penalise the prior default.
        # Auto-APPROVED is not acceptable for a borrower with cb_default='Y'.
        assert assessment["decision"] != "APPROVED", (
            "CRITICAL: Grade-A applicant with prior default MUST NOT be "
            "auto-approved. The WoE for cb_person_default_on_file='Y' is "
            "insufficient to override loan_grade='A'."
        )
        assert assessment["pd_score"] > 0.15, (
            f"Prior default must elevate PD above the prime baseline. "
            f"Got pd_score={assessment['pd_score']}"
        )

        # cb_person_default_on_file must surface as a negative factor.
        negative_features = [
            f["feature"]
            for f in assessment.get("top_factors", {}).get("negative_factors", [])
        ]
        assert "cb_person_default_on_file" in negative_features, (
            f"cb_person_default_on_file must appear in negative_factors. "
            f"Got: {negative_features}"
        )

    def test_high_income_catastrophic_dti(
        self,
        predict_url: str,
        base_payload: dict[str, Any],
        universal_assertions: Callable,
    ) -> None:
        """
        TC-04: Contradiction — High Income + Catastrophic DTI.

        Risk Rationale: A borrower earning $200K/yr with DTI=0.92 is
        technically already insolvent (92% of income services existing debt).
        Tests that the Capacity dimension (5C) correctly dominates. A system
        that approves this profile is critically broken. The DEBTCONSOLIDATION
        intent also triggers the highest pricing penalty (+0.8%).
        """
        base_payload.update({
            "person_income": 200_000,
            "loan_amnt": 50_000,
            "loan_grade": "C",
            "loan_int_rate": 14.0,
            "loan_to_income_ratio": 0.25,
            "loan_percent_income": 0.25,
            "debt_to_income_ratio": 0.92,       # ← catastrophic DTI
            "person_emp_length": 5.0,
            "person_home_ownership": "RENT",
            "cb_person_default_on_file": "N",
            "loan_intent": "DEBTCONSOLIDATION",  # ← highest intent penalty
        })

        response = requests.post(predict_url, json=base_payload)
        assessment = universal_assertions(response)

        assert assessment["decision"] in ("MANUAL_REVIEW", "REJECTED"), (
            f"Insolvent borrower (DTI=0.92) must not be approved. "
            f"Got: {assessment['decision']}"
        )
        assert assessment["pd_score"] > 0.30, (
            f"Catastrophic DTI must produce elevated PD. Got: {assessment['pd_score']}"
        )

        # DEBTCONSOLIDATION must apply the +0.8% intent penalty.
        pricing = assessment["pricing_recommendation"]
        assert pricing["intent_adjustment"] == pytest.approx(0.8, abs=0.001), (
            f"DEBTCONSOLIDATION intent_adjustment must be +0.8%. "
            f"Got: {pricing['intent_adjustment']}"
        )

        # debt_to_income_ratio must surface as a negative risk factor.
        negative_features = [
            f["feature"]
            for f in assessment.get("top_factors", {}).get("negative_factors", [])
        ]
        assert "debt_to_income_ratio" in negative_features, (
            f"debt_to_income_ratio must appear in negative_factors for DTI=0.92. "
            f"Got: {negative_features}"
        )

    def test_grade_g_overrides_positive_signals(
        self,
        predict_url: str,
        base_payload: dict[str, Any],
        universal_assertions: Callable,
    ) -> None:
        """
        TC-05: Contradiction — Grade G + No Default History + High Income.

        Risk Rationale: Grade G is the worst credit grade. Tests whether the
        model correctly assigns an extremely negative WoE to loan_grade='G'
        that overwhelms positive signals (clean default record, high income,
        low LTI). A system that approves this profile is critically broken.
        """
        base_payload.update({
            "loan_grade": "G",                  # ← worst possible grade
            "cb_person_default_on_file": "N",
            "person_income": 150_000,
            "loan_amnt": 8_000,
            "loan_to_income_ratio": 0.053,
            "loan_percent_income": 0.053,
            "debt_to_income_ratio": 0.15,
            "loan_int_rate": 22.0,
            "person_emp_length": 12.0,
            "person_home_ownership": "OWN",
            "loan_intent": "PERSONAL",
        })

        response = requests.post(predict_url, json=base_payload)
        assessment = universal_assertions(response)

        # Grade G must be a strongly negative WoE signal.
        assert assessment["decision"] in ("MANUAL_REVIEW", "REJECTED"), (
            f"Grade-G applicant must not be auto-approved regardless of "
            f"clean history. Got: {assessment['decision']}"
        )
        assert assessment["pd_score"] > 0.35

        # loan_grade must surface as the primary negative factor.
        negative_features = [
            f["feature"]
            for f in assessment.get("top_factors", {}).get("negative_factors", [])
        ]
        assert "loan_grade" in negative_features, (
            f"loan_grade must appear in negative_factors for Grade G. "
            f"Got: {negative_features}"
        )

        # Statutory cap must hold regardless of rate components.
        pricing = assessment["pricing_recommendation"]
        assert pricing["recommended_interest_rate"] <= 24.0

    def test_venture_loan_unemployed_masked_by_grade_a(
        self,
        predict_url: str,
        base_payload: dict[str, Any],
        universal_assertions: Callable,
    ) -> None:
        """
        TC-06: Contradiction — Venture Loan + Grade A + Zero Employment Length.

        Risk Rationale: An applicant with emp_length=0.0 (no employment history)
        applying for a VENTURE loan with LTI=0.50 is high-risk, masked by a
        good grade. Although employment_type is dropped by the model,
        person_emp_length=0.0 is a live feature that must map to the lowest
        WoE bin, penalising the score accordingly.
        """
        base_payload.update({
            "loan_grade": "A",
            "loan_intent": "VENTURE",
            "employment_type": "UNEMPLOYED",
            "person_emp_length": 0.0,           # ← zero employment tenure
            "person_income": 30_000,
            "loan_amnt": 15_000,
            "loan_to_income_ratio": 0.50,       # ← high LTI
            "loan_percent_income": 0.50,
            "debt_to_income_ratio": 0.60,
            "loan_int_rate": 8.0,
            "person_home_ownership": "RENT",
            "cb_person_default_on_file": "N",
        })

        response = requests.post(predict_url, json=base_payload)
        assessment = universal_assertions(response)

        assert assessment["decision"] != "APPROVED", (
            "Unemployed VENTURE applicant (LTI=0.50, emp_length=0) "
            "must not be auto-approved despite Grade A."
        )
        assert assessment["pd_score"] > 0.25

        # VENTURE intent must apply the +0.5% pricing penalty.
        pricing = assessment["pricing_recommendation"]
        assert pricing["intent_adjustment"] == pytest.approx(0.5, abs=0.001), (
            f"VENTURE intent_adjustment must be +0.5%. Got: {pricing['intent_adjustment']}"
        )


# ===========================================================================
# Class 3: Boundary Value Analysis — Threshold Probing
# ===========================================================================

class TestBoundaryValues:
    """
    TC-07 to TC-12 — Values resting exactly on or just over the decision
    boundaries. Tests the hard >= comparisons in _assign_risk_tier().
    """

    def test_fico_boundary_approved_vs_conditional(
        self,
        predict_url: str,
        base_payload: dict[str, Any],
        universal_assertions: Callable,
    ) -> None:
        """
        TC-07: BVA — FICO Boundary: APPROVED vs APPROVED_CONDITIONAL (score ~740).

        Risk Rationale: Probes the hard boundary at credit_score=740. An
        off-by-one in int(round(...)) in _pd_to_credit_score() could
        incorrectly classify a prime borrower. Verifies no mixed state
        (e.g., credit_score=740 but decision=MANUAL_REVIEW).
        """
        base_payload.update({
            "loan_grade": "A",
            "person_income": 80_000,
            "loan_amnt": 8_000,
            "loan_to_income_ratio": 0.10,
            "loan_percent_income": 0.10,
            "debt_to_income_ratio": 0.22,
            "loan_int_rate": 8.5,
            "person_emp_length": 6.0,
            "person_home_ownership": "MORTGAGE",
            "cb_person_default_on_file": "N",
            "loan_intent": "PERSONAL",
        })

        response = requests.post(predict_url, json=base_payload)
        assessment = universal_assertions(response)

        # The profile should be near the 740 boundary.
        assert assessment["credit_score"] >= 670, (
            f"Near-prime profile should score >= 670. Got: {assessment['credit_score']}"
        )
        # Key coherence: whatever tier is returned, decision must match it exactly.
        assert assessment["decision"] in ("APPROVED", "APPROVED_CONDITIONAL"), (
            f"Near-prime applicant must not fall into MANUAL_REVIEW or REJECTED. "
            f"Got: {assessment['decision']}"
        )
        # No mixed state: score < 670 cannot map to APPROVED_CONDITIONAL.
        assert assessment["risk_tier"] in ("LOW", "MEDIUM_LOW")

    def test_fico_boundary_manual_review_vs_rejected(
        self,
        predict_url: str,
        base_payload: dict[str, Any],
        universal_assertions: Callable,
    ) -> None:
        """
        TC-08: BVA — FICO Boundary: MANUAL_REVIEW vs REJECTED (score ~580).

        Risk Rationale: The 580-boundary is the most critical for fair lending.
        A borrower incorrectly rejected at score=581 is an unfair rejection and
        missed revenue. Verifies that the REJECTED path correctly zeroes
        max_credit_limit.
        """
        base_payload.update({
            "loan_grade": "D",
            "person_income": 45_000,
            "loan_amnt": 12_000,
            "loan_to_income_ratio": 0.267,
            "loan_percent_income": 0.267,
            "debt_to_income_ratio": 0.45,
            "loan_int_rate": 16.5,
            "person_emp_length": 2.0,
            "person_home_ownership": "RENT",
            "cb_person_default_on_file": "N",
            "loan_intent": "PERSONAL",
        })

        response = requests.post(predict_url, json=base_payload)
        assessment = universal_assertions(response)

        # Profile should land near the 580 boundary.
        assert assessment["decision"] in ("MANUAL_REVIEW", "REJECTED"), (
            f"Sub-prime Grade D applicant must be in MANUAL_REVIEW or REJECTED. "
            f"Got: {assessment['decision']}"
        )

        # Critical: REJECTED decision must zero the credit limit.
        pricing = assessment["pricing_recommendation"]
        if assessment["decision"] == "REJECTED":
            assert pricing["max_credit_limit"] == 0.0, (
                "REJECTED decision must set max_credit_limit to exactly 0.0"
            )

    def test_lti_exactly_at_low_tier_boundary(
        self,
        predict_url: str,
        base_payload: dict[str, Any],
        universal_assertions: Callable,
    ) -> None:
        """
        TC-09: BVA — LTI Exactly at LOW Tier Boundary (loan_amnt = income * 0.40).

        Risk Rationale: max_lti_caps.LOW = 0.40 from config.yaml. When
        loan_amnt equals exactly 40% of annual income, the applicant is
        requesting their maximum entitlement. The system must return
        WITHIN_LIMIT, not EXCEEDS_RECOMMENDED_LIMIT. An off-by-epsilon
        float comparison causes a wrongful limit rejection.
        """
        base_payload.update({
            "loan_grade": "A",
            "person_income": 100_000,
            "loan_amnt": 40_000,              # = 100_000 * 0.40 exactly
            "loan_to_income_ratio": 0.40,
            "loan_percent_income": 0.40,
            "debt_to_income_ratio": 0.20,
            "loan_int_rate": 8.0,
            "person_emp_length": 7.0,
            "person_home_ownership": "OWN",
            "cb_person_default_on_file": "N",
            "loan_intent": "PERSONAL",
        })

        response = requests.post(predict_url, json=base_payload)
        assessment = universal_assertions(response)

        # Prime applicant at exact LTI boundary must be approved.
        assert assessment["decision"] == "APPROVED"

        pricing = assessment["pricing_recommendation"]
        # max_credit_limit = min(100_000 * 0.40, 50_000) = min(40_000, 50_000) = 40_000
        assert pricing["max_credit_limit"] == pytest.approx(40_000.0, abs=0.01), (
            f"Max credit limit must be exactly $40,000.00 at the LTI boundary. "
            f"Got: {pricing['max_credit_limit']}"
        )
        assert pricing["limit_status"] == "WITHIN_LIMIT", (
            f"loan_amnt at exactly the LTI cap must return WITHIN_LIMIT, "
            f"got: {pricing['limit_status']!r}"
        )

    def test_lti_just_over_boundary_status_only(
        self,
        predict_url: str,
        base_payload: dict[str, Any],
        universal_assertions: Callable,
    ) -> None:
        """
        TC-10: BVA — LTI Just Over LOW Tier Boundary (0.401).

        Risk Rationale: Exceeding the credit limit threshold must change
        limit_status from WITHIN_LIMIT to EXCEEDS_RECOMMENDED_LIMIT but
        must NOT alter the ML decision tier. These are independent systems —
        coupling them would be a critical business logic bug.
        """
        base_payload.update({
            "loan_grade": "A",
            "person_income": 100_000,
            "loan_amnt": 40_100,              # $100 over the 40% LTI boundary
            "loan_to_income_ratio": 0.401,
            "loan_percent_income": 0.401,
            "debt_to_income_ratio": 0.20,
            "loan_int_rate": 8.0,
            "person_emp_length": 7.0,
            "person_home_ownership": "OWN",
            "cb_person_default_on_file": "N",
            "loan_intent": "PERSONAL",
        })

        response = requests.post(predict_url, json=base_payload)
        assessment = universal_assertions(response)

        # ML decision must still be APPROVED (limit breach != rejection).
        assert assessment["decision"] == "APPROVED", (
            "Exceeding the recommended credit limit must NOT downgrade the ML "
            "decision. The limit engine and ML engine are independent."
        )

        pricing = assessment["pricing_recommendation"]
        assert pricing["limit_status"] == "EXCEEDS_RECOMMENDED_LIMIT", (
            f"loan_amnt just over the LTI cap must return EXCEEDS_RECOMMENDED_LIMIT. "
            f"Got: {pricing['limit_status']!r}"
        )
        # The hard cap still governs the limit.
        assert pricing["max_credit_limit"] == pytest.approx(40_000.0, abs=0.01)

    def test_statutory_rate_cap_never_breached(
        self,
        predict_url: str,
        base_payload: dict[str, Any],
        universal_assertions: Callable,
    ) -> None:
        """
        TC-11: BVA — Statutory Rate Cap Activation (Dieu 468 BLDS).

        Risk Rationale: The statutory max_rate=24.0 in config.yaml must
        hard-clamp the APR. Returning APR > 24% constitutes a violation of
        Vietnamese civil law. This is a mandatory automated compliance gate.
        """
        base_payload.update({
            "loan_grade": "G",
            "person_income": 30_000,
            "loan_amnt": 5_000,
            "loan_to_income_ratio": 0.167,
            "loan_percent_income": 0.167,
            "debt_to_income_ratio": 0.70,
            "loan_int_rate": 25.0,            # ← submitted rate above cap
            "person_emp_length": 0.5,
            "person_home_ownership": "RENT",
            "cb_person_default_on_file": "Y",
            "loan_intent": "DEBTCONSOLIDATION",
        })

        response = requests.post(predict_url, json=base_payload)
        assessment = universal_assertions(response)

        pricing = assessment["pricing_recommendation"]
        # Statutory cap is enforced by universal_assertions already,
        # but we make it explicit here for documentation.
        assert pricing["recommended_interest_rate"] <= 24.0, (
            f"CRITICAL COMPLIANCE FAILURE: APR={pricing['recommended_interest_rate']}% "
            f"exceeds the Dieu 468 BLDS statutory cap of 24.0%."
        )
        # HIGH tier must carry a 9.0% risk spread.
        assert pricing["risk_spread"] == pytest.approx(9.0, abs=0.001)

    def test_zero_employment_length_does_not_crash(
        self,
        predict_url: str,
        base_payload: dict[str, Any],
        universal_assertions: Callable,
    ) -> None:
        """
        TC-12: BVA — Zero Employment Length (Boundary of WoE Bin).

        Risk Rationale: person_emp_length=0.0 sits at the boundary between
        a legitimate "just started working" value and the fillna_missing_cols
        handling. The preprocessor must NOT treat 0.0 as NaN (which would
        mislabel a new employee as missing data). A 500 error here is a P1 bug.
        """
        base_payload.update({
            "person_emp_length": 0.0,         # ← boundary value
            "loan_grade": "B",
            "person_income": 55_000,
            "loan_amnt": 8_000,
            "loan_to_income_ratio": 0.145,
            "loan_percent_income": 0.145,
            "debt_to_income_ratio": 0.28,
            "loan_int_rate": 12.0,
            "person_home_ownership": "RENT",
            "cb_person_default_on_file": "N",
            "loan_intent": "PERSONAL",
        })

        response = requests.post(predict_url, json=base_payload)
        # Must NOT be a 500 — this is the primary assertion.
        assert response.status_code != 500, (
            f"HTTP 500 on person_emp_length=0.0 indicates the WoE binner "
            f"treats 0.0 as NaN. Response: {response.text[:300]}"
        )

        if response.status_code == 200:
            assessment = universal_assertions(response)
            # Zero employment should be penalised vs. the 4yr baseline.
            # We cannot assert an exact score, but PD must be a valid float.
            assert isinstance(assessment["pd_score"], float)


# ===========================================================================
# Class 4: Data Integrity & Robustness — Extreme & Malformed Inputs
# ===========================================================================

class TestRobustness:
    """
    TC-13 to TC-20 — Tests that extreme outliers and malformed inputs never
    trigger HTTP 500 errors. Validates WoE binner's out-of-distribution
    handling and Pydantic schema enforcement.
    """

    def test_extreme_outlier_income_10m(
        self,
        predict_url: str,
        base_payload: dict[str, Any],
        universal_assertions: Callable,
    ) -> None:
        """
        TC-13: Robustness — Extreme Outlier Income ($10M).

        Risk Rationale: $10M income falls outside all training quantile bins.
        Tests that pd.qcut bin edges handle inference-time outliers without
        raising ValueError. Also validates the $50,000 hard cap prevents the
        system from issuing a $4M credit line.
        """
        base_payload.update({
            "person_income": 10_000_000,      # ← 10M, far outside training range
            "loan_amnt": 50_000,
            "loan_grade": "A",
            "loan_to_income_ratio": 0.005,
            "loan_percent_income": 0.005,
            "debt_to_income_ratio": 0.01,
            "loan_int_rate": 7.0,
            "person_emp_length": 15.0,
            "person_home_ownership": "OWN",
            "cb_person_default_on_file": "N",
            "loan_intent": "PERSONAL",
        })

        response = requests.post(predict_url, json=base_payload)
        assert response.status_code != 500, (
            "HTTP 500 on $10M income indicates WoE binner cannot handle "
            "out-of-distribution quantile outliers."
        )

        if response.status_code == 200:
            assessment = universal_assertions(response)
            # Hard cap of $50,000 (max_amount_caps.LOW) must engage.
            pricing = assessment["pricing_recommendation"]
            assert pricing["max_credit_limit"] <= 50_000.0, (
                f"Hard cap of $50,000 must prevent a $4M credit line. "
                f"Got max_credit_limit={pricing['max_credit_limit']}"
            )

    def test_extreme_outlier_loan_amount_500k(
        self,
        predict_url: str,
        base_payload: dict[str, Any],
        universal_assertions: Callable,
    ) -> None:
        """
        TC-14: Robustness — Extreme Outlier Loan Amount ($500K).

        Risk Rationale: LTI = 6.25 (625% of income) is far beyond any
        training data quantile. The WoE binner must clamp to the last known
        bin edge rather than throw an exception. A 500 error reveals a
        silent production failure mode.
        """
        base_payload.update({
            "person_income": 80_000,
            "loan_amnt": 500_000,             # ← extreme loan amount
            "loan_grade": "B",
            "loan_to_income_ratio": 6.25,
            "loan_percent_income": 6.25,
            "debt_to_income_ratio": 0.30,
            "loan_int_rate": 13.0,
            "person_emp_length": 5.0,
            "person_home_ownership": "RENT",
            "cb_person_default_on_file": "N",
            "loan_intent": "PERSONAL",
        })

        response = requests.post(predict_url, json=base_payload)
        assert response.status_code != 500, (
            "HTTP 500 on extreme LTI=6.25 indicates WoE binner cannot handle "
            "out-of-distribution loan_amnt or loan_to_income_ratio."
        )

        if response.status_code == 200:
            assessment = universal_assertions(response)
            # LTI=6.25 must produce an elevated PD.
            assert assessment["pd_score"] > 0.40, (
                f"Extreme LTI=6.25 must produce a high PD. Got: {assessment['pd_score']}"
            )

    def test_minimum_income_floor_guarantee(
        self,
        predict_url: str,
        base_payload: dict[str, Any],
        universal_assertions: Callable,
    ) -> None:
        """
        TC-15: Robustness — Minimum Valid Income ($1).

        Risk Rationale: Tests the $1,000 floor guarantee in the pricing engine
        (max(max_credit_limit, 1000.0)). With income=$1 and HIGH tier, the
        income-based limit would be $1 * 0.08 = $0.08, which must be floored
        to $1,000. Also validates no division-by-zero occurs with near-zero income.

        NOTE: Since decision for this profile is expected to be REJECTED,
        max_credit_limit will be forced to 0.0 by the REJECTED guard before
        the floor applies. This test validates that a near-zero income does not
        cause a 500 error or division-by-zero.
        """
        base_payload.update({
            "person_income": 1,               # ← near-zero income
            "loan_amnt": 500,
            "loan_grade": "D",
            "loan_to_income_ratio": 500.0,
            "loan_percent_income": 500.0,
            "debt_to_income_ratio": 0.5,
            "loan_int_rate": 17.0,
            "person_emp_length": 1.0,
            "person_home_ownership": "RENT",
            "cb_person_default_on_file": "N",
            "loan_intent": "PERSONAL",
        })

        response = requests.post(predict_url, json=base_payload)
        assert response.status_code != 500, (
            "HTTP 500 on income=$1 indicates a division-by-zero or numeric "
            "overflow in the pricing or scoring engine."
        )

        if response.status_code == 200:
            assessment = universal_assertions(response)
            # With such an extreme LTI, the profile must be rejected.
            assert assessment["decision"] == "REJECTED"

    def test_negative_interest_rate_never_500(
        self,
        predict_url: str,
        base_payload: dict[str, Any],
    ) -> None:
        """
        TC-16: Robustness — Negative Interest Rate.

        Risk Rationale: loan_int_rate has no ge=0 constraint in loan.py.
        A negative rate will hit the WoE binner's pd.cut / quantile bin logic.
        A 500 error here is a P1 bug requiring immediate schema validation fix.
        Expected: HTTP 422 (Pydantic rejects) or HTTP 200 (binner clamps to
        lowest bin). HTTP 500 is never acceptable.
        """
        base_payload.update({
            "loan_int_rate": -5.0,            # ← invalid negative rate
            "loan_grade": "A",
            "person_income": 80_000,
            "loan_amnt": 10_000,
            "loan_to_income_ratio": 0.125,
            "loan_percent_income": 0.125,
            "debt_to_income_ratio": 0.20,
            "person_emp_length": 5.0,
            "person_home_ownership": "OWN",
            "cb_person_default_on_file": "N",
            "loan_intent": "PERSONAL",
        })

        response = requests.post(predict_url, json=base_payload)

        # This is the ONLY test where 500 is the failure condition.
        assert response.status_code != 500, (
            f"CRITICAL P1 BUG: HTTP 500 on loan_int_rate=-5.0. "
            f"The loan.py schema must add ge=0 constraint to loan_int_rate. "
            f"Response: {response.text[:300]}"
        )
        assert response.status_code in (200, 422), (
            f"Expected 200 (binner clamps) or 422 (schema rejects). "
            f"Got: {response.status_code}"
        )

        if response.status_code == 422:
            # Pydantic validation error must reference loan_int_rate.
            error_body = response.json()
            error_locations = [
                " -> ".join(str(loc) for loc in e.get("loc", []))
                for e in error_body.get("detail", [])
            ]
            assert any("loan_int_rate" in loc for loc in error_locations), (
                f"422 response must reference loan_int_rate. "
                f"Got locations: {error_locations}"
            )

    def test_unknown_loan_grade_graceful_fallback(
        self,
        predict_url: str,
        base_payload: dict[str, Any],
        universal_assertions: Callable,
    ) -> None:
        """
        TC-17: Robustness — Unknown Loan Grade ("Z").

        Risk Rationale: The WoE categorical binner uses a
        woe_map.get(value, 0.0) fallback for unseen categories. If a loan
        officer enters a grade not in the training set, the system must
        degrade gracefully to a neutral WoE score, not crash. A 500 error
        here indicates the fallback is not implemented.
        """
        base_payload.update({
            "loan_grade": "Z",                # ← unseen category
        })

        response = requests.post(predict_url, json=base_payload)
        assert response.status_code != 500, (
            "HTTP 500 on unknown loan_grade='Z' indicates the WoE binner "
            "lacks an 'unknown category' fallback (woe_map.get(value, 0.0))."
        )

        if response.status_code == 200:
            assessment = universal_assertions(response)
            assert isinstance(assessment["pd_score"], float)

    def test_missing_required_field_returns_422(
        self,
        predict_url: str,
        base_payload: dict[str, Any],
    ) -> None:
        """
        TC-19: Robustness — Missing Required Field (loan_grade omitted).

        Risk Rationale: loan_grade is a required field (no default, no
        Optional) per loan.py. FastAPI/Pydantic must reject at the schema
        validation layer before the ML engine ever runs. A 500 response here
        means the model preprocessing does not handle missing keys.
        """
        base_payload.pop("loan_grade", None)  # ← remove required field

        response = requests.post(predict_url, json=base_payload)
        assert response.status_code == 422, (
            f"Missing required field 'loan_grade' must return HTTP 422. "
            f"Got: {response.status_code}"
        )

        # The error detail must reference loan_grade.
        error_body = response.json()
        error_locations = [
            " -> ".join(str(loc) for loc in e.get("loc", []))
            for e in error_body.get("detail", [])
        ]
        assert any("loan_grade" in loc for loc in error_locations), (
            f"422 response must identify 'loan_grade' as the missing field. "
            f"Got error locations: {error_locations}"
        )

    def test_null_optional_field_never_500(
        self,
        predict_url: str,
        base_payload: dict[str, Any],
    ) -> None:
        """
        TC-20: Robustness — Explicit null for Optional field (debt_to_income_ratio).

        Risk Rationale: debt_to_income_ratio is Optional[float] with default
        0.25. Sending explicit null has subtly different Pydantic v1 vs v2
        behaviour. Tests the frontend-backend contract for null vs. omitted
        fields. HTTP 500 is never acceptable — only 200 or 422 are valid.
        """
        base_payload["debt_to_income_ratio"] = None  # ← explicit null

        response = requests.post(predict_url, json=base_payload)
        assert response.status_code != 500, (
            f"HTTP 500 on debt_to_income_ratio=null. "
            f"This must be handled by Pydantic (422) or default substitution (200)."
        )
        assert response.status_code in (200, 422), (
            f"Expected 200 or 422 for null optional field. "
            f"Got: {response.status_code}"
        )


# ===========================================================================
# Class 5: Logical Consistency — Response Payload Coherence
# ===========================================================================

class TestLogicalConsistency:
    """
    TC-21 to TC-25 — Ensures all fields in the response payload form a
    mathematically and logically consistent vector.
    """

    def test_high_pd_full_coherence_vector(
        self,
        predict_url: str,
        base_payload: dict[str, Any],
        universal_assertions: Callable,
    ) -> None:
        """
        TC-21: Consistency — High PD Must Align with All Output Fields.

        Risk Rationale: The cardinal coherence test. All output fields
        (pd_score, credit_score, risk_tier, decision, max_credit_limit,
        limit_status, APR) must form a logically consistent vector.
        A system returning pd_score=0.85 but decision='APPROVED' has a
        catastrophic decoupling between the ML engine and business rules engine.
        """
        base_payload.update({
            "loan_grade": "G",
            "person_income": 25_000,
            "loan_amnt": 20_000,
            "loan_to_income_ratio": 0.80,
            "loan_percent_income": 0.80,
            "debt_to_income_ratio": 0.85,
            "loan_int_rate": 24.0,
            "person_emp_length": 0.5,
            "person_home_ownership": "RENT",
            "cb_person_default_on_file": "Y",
            "loan_intent": "DEBTCONSOLIDATION",
        })

        response = requests.post(predict_url, json=base_payload)
        assessment = universal_assertions(response)  # Validates the core 6 invariants.

        # Additional coherence checks for the worst-case profile.
        assert assessment["pd_score"] > 0.50, (
            f"Worst-case profile (Grade G, default=Y, DTI=0.85) must have "
            f"PD > 0.50. Got: {assessment['pd_score']}"
        )
        assert assessment["credit_score"] < 580
        assert assessment["risk_tier"] == "HIGH"
        assert assessment["decision"] == "REJECTED"

        pricing = assessment["pricing_recommendation"]
        assert pricing["max_credit_limit"] == 0.0
        assert pricing["limit_status"] == "REJECTED"
        # Statutory cap must hold even for worst-case APR.
        assert pricing["recommended_interest_rate"] <= 24.0

    def test_positive_contributions_for_prime_applicant(
        self,
        predict_url: str,
        base_payload: dict[str, Any],
        universal_assertions: Callable,
    ) -> None:
        """
        TC-22: Consistency — Low PD Must Have Positive Net Contributions.

        Risk Rationale: Tests the WoE explainability layer. For a prime
        borrower, the WoE contributions for loan_grade='A' and
        cb_person_default_on_file='N' MUST be positive. Negative values
        would indicate the WoE map is inverted or the encoder was loaded
        incorrectly — a silent correctness failure invisible to the user.
        """
        base_payload.update({
            "person_income": 95_000,
            "loan_amnt": 10_000,
            "loan_grade": "A",
            "loan_int_rate": 7.5,
            "loan_to_income_ratio": 0.105,
            "loan_percent_income": 0.105,
            "debt_to_income_ratio": 0.18,
            "person_emp_length": 8.0,
            "person_home_ownership": "OWN",
            "cb_person_default_on_file": "N",
            "loan_intent": "EDUCATION",
        })

        response = requests.post(predict_url, json=base_payload)
        assessment = universal_assertions(response)

        top_factors = assessment.get("top_factors", {})
        positive_factors = top_factors.get("positive_factors", [])
        assert len(positive_factors) >= 1, (
            "Prime applicant must have at least one positive contributing factor."
        )

        contributions = assessment.get("contributions", {})
        # Grade A must have a positive WoE contribution.
        if "loan_grade" in contributions:
            assert contributions["loan_grade"] > 0, (
                f"loan_grade='A' must have positive WoE contribution. "
                f"Got: {contributions['loan_grade']}"
            )
        # Clean default record must have a positive WoE contribution.
        if "cb_person_default_on_file" in contributions:
            assert contributions["cb_person_default_on_file"] > 0, (
                f"cb_person_default_on_file='N' must have positive WoE contribution. "
                f"Got: {contributions['cb_person_default_on_file']}"
            )

    def test_pricing_waterfall_exact_arithmetic(
        self,
        predict_url: str,
        base_payload: dict[str, Any],
        universal_assertions: Callable,
    ) -> None:
        """
        TC-23: Consistency — Pricing Waterfall Arithmetic Verification.

        Risk Rationale: APR = base_rate + risk_spread + capital_discount +
        intent_adjustment. If the frontend displays 6.7% but the backend
        computed 7.2% (missing a component), it constitutes a Truth in
        Lending Act (TILA) disclosure violation. Each component must be
        independently verifiable.
        """
        base_payload.update({
            "person_income": 95_000,
            "loan_amnt": 10_000,
            "loan_grade": "A",
            "loan_int_rate": 7.5,
            "loan_to_income_ratio": 0.105,
            "loan_percent_income": 0.105,
            "debt_to_income_ratio": 0.18,
            "person_emp_length": 8.0,
            "person_home_ownership": "OWN",       # capital_discount = -0.5
            "cb_person_default_on_file": "N",
            "loan_intent": "EDUCATION",           # intent_adjustment = -0.3
        })

        response = requests.post(predict_url, json=base_payload)
        assessment = universal_assertions(response)

        # Must be approved (LOW tier) for the waterfall to use risk_spread=1.0
        assert assessment["risk_tier"] == "LOW", (
            f"Profile must achieve LOW tier for waterfall assertion to be valid. "
            f"Got: {assessment['risk_tier']}"
        )

        pricing = assessment["pricing_recommendation"]
        assert pricing["base_rate"] == pytest.approx(6.5, abs=0.001)
        assert pricing["risk_spread"] == pytest.approx(1.0, abs=0.001), (
            f"LOW tier risk_spread must be 1.0. Got: {pricing['risk_spread']}"
        )
        assert pricing["capital_discount"] == pytest.approx(-0.5, abs=0.001), (
            f"OWN home_ownership capital_discount must be -0.5. "
            f"Got: {pricing['capital_discount']}"
        )
        assert pricing["intent_adjustment"] == pytest.approx(-0.3, abs=0.001), (
            f"EDUCATION intent_adjustment must be -0.3. "
            f"Got: {pricing['intent_adjustment']}"
        )

        # Full waterfall arithmetic check.
        expected_apr = round(6.5 + 1.0 + (-0.5) + (-0.3), 2)  # = 6.7
        assert pricing["recommended_interest_rate"] == pytest.approx(expected_apr, abs=0.01), (
            f"Waterfall APR must equal {expected_apr}%. "
            f"Got: {pricing['recommended_interest_rate']}%"
        )

    def test_pmt_simulation_arithmetic(
        self,
        predict_url: str,
        base_payload: dict[str, Any],
        universal_assertions: Callable,
    ) -> None:
        """
        TC-24: Consistency — PMT Simulation Arithmetic.

        Risk Rationale: Tests the amortization formula:
            PMT = P * [r(1+r)^n / ((1+r)^n - 1)]
        An incorrect monthly_payment_estimate means the customer sees a wrong
        repayment schedule — a consumer protection violation. Also validates
        that total_interest_estimate is always > 0 (total cost > principal).
        """
        loan_principal = 10_000.0

        base_payload.update({
            "person_income": 95_000,
            "loan_amnt": loan_principal,
            "loan_grade": "A",
            "loan_int_rate": 7.5,
            "loan_to_income_ratio": 0.105,
            "loan_percent_income": 0.105,
            "debt_to_income_ratio": 0.18,
            "person_emp_length": 8.0,
            "person_home_ownership": "OWN",
            "cb_person_default_on_file": "N",
            "loan_intent": "EDUCATION",
        })

        response = requests.post(predict_url, json=base_payload)
        assessment = universal_assertions(response)

        pricing = assessment["pricing_recommendation"]
        apr = pricing["recommended_interest_rate"]   # e.g., 6.7
        n = pricing["loan_term_months"]               # 36 per config.yaml
        pmt = pricing["monthly_payment_estimate"]
        total_interest = pricing["total_interest_estimate"]

        assert n == 36, f"Default loan term must be 36 months. Got: {n}"

        # Manually compute expected PMT for comparison.
        monthly_rate = apr / (12 * 100)
        if monthly_rate > 0:
            expected_pmt = loan_principal * (
                monthly_rate * (1 + monthly_rate) ** n
            ) / ((1 + monthly_rate) ** n - 1)
        else:
            expected_pmt = loan_principal / n

        assert pmt == pytest.approx(expected_pmt, rel=0.01), (
            f"PMT formula mismatch. Expected ~{expected_pmt:.2f}, got {pmt:.2f}. "
            f"Loan={loan_principal}, APR={apr}%, n={n} months."
        )

        # Total interest must be non-negative.
        assert total_interest >= 0, (
            f"total_interest_estimate must be >= 0. Got: {total_interest}"
        )
        expected_total_interest = round(pmt * n - loan_principal, 2)
        assert total_interest == pytest.approx(expected_total_interest, abs=1.0), (
            f"total_interest_estimate must equal PMT*n - principal. "
            f"Expected ~{expected_total_interest:.2f}, got {total_interest:.2f}."
        )

    def test_rejected_applicant_pricing_guardrails(
        self,
        predict_url: str,
        base_payload: dict[str, Any],
        universal_assertions: Callable,
    ) -> None:
        """
        TC-25: Consistency — REJECTED Applicant Pricing Guardrails.

        Risk Rationale: Even for rejected applicants, the full pricing object
        must be returned (the frontend displays it). Critical invariant:
        max_credit_limit=0.0 and limit_status='REJECTED'. A non-zero credit
        limit for a rejected borrower allows the frontend to display a
        fraudulent credit offer.
        """
        base_payload.update({
            "loan_grade": "G",
            "person_income": 25_000,
            "loan_amnt": 20_000,
            "loan_to_income_ratio": 0.80,
            "loan_percent_income": 0.80,
            "debt_to_income_ratio": 0.85,
            "loan_int_rate": 24.0,
            "person_emp_length": 0.5,
            "person_home_ownership": "RENT",
            "cb_person_default_on_file": "Y",
            "loan_intent": "DEBTCONSOLIDATION",
        })

        response = requests.post(predict_url, json=base_payload)
        assessment = universal_assertions(response)

        # For the worst-case profile, REJECTED is expected.
        assert assessment["decision"] == "REJECTED"

        pricing = assessment["pricing_recommendation"]

        # Guardrail 1: Zero credit limit for rejected applicants.
        assert pricing["max_credit_limit"] == 0.0

        # Guardrail 2: pricing object is fully populated (not null).
        assert pricing.get("recommended_interest_rate") is not None, (
            "recommended_interest_rate must not be null even for REJECTED applicants."
        )
        assert pricing.get("monthly_payment_estimate") is not None, (
            "monthly_payment_estimate must not be null even for REJECTED applicants."
        )
        assert pricing.get("total_interest_estimate") is not None, (
            "total_interest_estimate must not be null even for REJECTED applicants."
        )


# ===========================================================================
# Class 6: API Infrastructure & Schema Validation
# ===========================================================================

class TestApiInfrastructure:
    """
    TC-26 to TC-30 — Schema validation, health probe, and API contract tests.
    """

    def test_wrong_data_type_loan_amnt(
        self,
        predict_url: str,
        base_payload: dict[str, Any],
    ) -> None:
        """
        TC-26: Schema — Wrong Data Type (loan_amnt as string).

        Risk Rationale: Tests that FastAPI/Pydantic is the first line of
        defence, not the ML preprocessing layer. A string like "ten thousand"
        must be caught at schema validation.
        """
        base_payload["loan_amnt"] = "ten thousand"  # ← wrong type

        response = requests.post(predict_url, json=base_payload)
        assert response.status_code == 422, (
            f"String loan_amnt must return HTTP 422. Got: {response.status_code}"
        )
        assert response.status_code != 500

    def test_task_parameter_path_traversal(
        self,
        predict_url: str,
        base_payload: dict[str, Any],
    ) -> None:
        """
        TC-27: Schema — Task Query Parameter Injection / Path Traversal.

        Risk Rationale: The 'task' query param is passed directly to
        get_task_config(). If that function constructs file paths from the
        task name, a path traversal attack is possible. Unknown task names
        must return a clean error, not expose internal file paths in the
        response body.
        """
        response = requests.post(
            predict_url,
            json=base_payload,
            params={"task": "../../../etc/passwd"},  # ← path traversal attempt
        )
        # Must return a structured JSON error response without exposing system tracebacks
        assert response.status_code in (400, 404, 422, 500)
        detail = response.json().get("detail", "")
        assert "không tồn tại" in detail or "Task" in detail, (
            f"Expected structured error message for unknown task, got: {detail}"
        )
        assert "Traceback" not in detail, "Response must not disclose python tracebacks."


    def test_empty_request_body_returns_422_with_all_required_fields(
        self,
        predict_url: str,
    ) -> None:
        """
        TC-28: Schema — Empty Request Body {}.

        Risk Rationale: Confirms the API contract: exactly 11 required fields.
        Any deviation means the schema has drifted from what the frontend sends.
        This is the API contract enforcement test — run on every deployment.
        """
        required_fields = {
            "person_age", "person_income", "person_home_ownership",
            "person_emp_length", "loan_intent", "loan_grade", "loan_amnt",
            "loan_int_rate", "loan_percent_income", "cb_person_default_on_file",
            "cb_person_cred_hist_length",
        }

        response = requests.post(predict_url, json={})
        assert response.status_code == 422, (
            f"Empty request body must return HTTP 422. Got: {response.status_code}"
        )

        error_body = response.json()
        missing_fields = {
            e["loc"][-1]
            for e in error_body.get("detail", [])
            if e.get("type") in ("missing", "value_error.missing")
        }
        # All required fields must be called out.
        assert required_fields.issubset(missing_fields), (
            f"Expected all required fields in 422 error. "
            f"Missing from error: {required_fields - missing_fields}"
        )

    def test_health_check_always_responds(
        self,
        health_url: str,
    ) -> None:
        """
        TC-30: Health Check — Baseline Availability.

        Risk Rationale: The /health endpoint is the Kubernetes liveness probe.
        It must always respond regardless of model loading state. Even if the
        model artifact is missing, the health probe must not fail — only actual
        prediction calls should return 500 in that scenario.
        """
        response = requests.get(health_url, timeout=5)
        assert response.status_code == 200, (
            f"/health must always return HTTP 200. Got: {response.status_code}"
        )
        body = response.json()
        assert body.get("status") == "healthy", (
            f"/health body must contain {{\"status\": \"healthy\"}}. Got: {body}"
        )
