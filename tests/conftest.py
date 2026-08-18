"""
conftest.py — Shared pytest fixtures for the Credit Risk API test suite.

Fixtures:
    api_base_url    : Loads BASE_API_URL from .env (zero hardcoded URLs).
    predict_url     : Fully resolved POST /api/v1/predict endpoint.
    enrich_url      : Fully resolved POST /api/v1/enrich endpoint.
    base_payload    : The canonical baseline payload (mirrors initialFormData
                      from LoanApplicationPage.tsx#L13-32). All test cases
                      must deep-copy this and mutate only the field(s) under
                      test (DRY principle).
    universal_assertions : Callable fixture that enforces the six logical
                      invariants defined in Appendix A of api_test_cases.md
                      on every HTTP 200 response.
"""

import copy
import os
from typing import Any, Callable

import pytest
import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------------------------
# Searches for .env from the project root (two levels above this file).
_ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=_ENV_PATH, override=False)


# ---------------------------------------------------------------------------
# URL fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def api_base_url() -> str:
    """
    Reads BASE_API_URL from .env (key: VITE_API_BASE_URL, matching the
    existing project convention). Falls back to http://127.0.0.1:8000
    so tests are runnable without extra config during local development.
    """
    url = os.getenv("TEST_API_BASE_URL") or os.getenv("VITE_API_BASE_URL", "http://127.0.0.1:8000")
    return url.rstrip("/")


@pytest.fixture(scope="session")
def predict_url(api_base_url: str) -> str:
    """Fully resolved URL for POST /api/v1/predict."""
    return f"{api_base_url}/api/v1/predict"


@pytest.fixture(scope="session")
def enrich_url(api_base_url: str) -> str:
    """Fully resolved URL for POST /api/v1/enrich."""
    return f"{api_base_url}/api/v1/enrich"


@pytest.fixture(scope="session")
def health_url(api_base_url: str) -> str:
    """Fully resolved URL for GET /health."""
    return f"{api_base_url}/health"


# ---------------------------------------------------------------------------
# Baseline payload fixture
# ---------------------------------------------------------------------------

# Mirrors initialFormData from LoanApplicationPage.tsx#L13-32.
# The 10 fields that actually reach the XGBoost model are:
#   loan_grade, person_home_ownership, cb_person_default_on_file, loan_intent,
#   loan_to_income_ratio, debt_to_income_ratio, person_income, loan_int_rate,
#   person_emp_length, loan_amnt
# All remaining fields (gender, person_age, education_level, etc.) are
# silently dropped by the WoE binner per config.yaml#L39-54, but they are
# still required by the Pydantic schema.
_BASELINE_PAYLOAD: dict[str, Any] = {
    # ── Pydantic required fields ──────────────────────────────────────────
    "person_age": 28,
    "person_income": 65_000,
    "person_home_ownership": "RENT",
    "person_emp_length": 4.0,
    "loan_intent": "PERSONAL",
    "loan_grade": "B",
    "loan_amnt": 10_000,
    "loan_int_rate": 11.14,
    "loan_percent_income": 0.15,
    "cb_person_default_on_file": "N",
    "cb_person_cred_hist_length": 3,
    # ── Pydantic optional fields (with model defaults) ────────────────────
    "gender": "MALE",
    "marital_status": "SINGLE",
    "education_level": "BACHELOR",
    "employment_type": "FULL_TIME",
    "loan_to_income_ratio": 0.15,
    "debt_to_income_ratio": 0.25,
    "credit_utilization_ratio": 0.35,
    "past_delinquencies": 0,
}


@pytest.fixture
def base_payload() -> dict[str, Any]:
    """
    Returns a deep copy of the canonical baseline payload so each test
    can mutate its own isolated copy without affecting other tests.
    """
    return copy.deepcopy(_BASELINE_PAYLOAD)


# ---------------------------------------------------------------------------
# Universal assertions fixture (Appendix A of api_test_cases.md)
# ---------------------------------------------------------------------------

# Immutable mapping of valid (risk_tier, decision) pairs derived from the
# _assign_risk_tier() method in predict.py#L72-88.
_VALID_TIER_DECISION_PAIRS: dict[str, str] = {
    "LOW":         "APPROVED",
    "MEDIUM_LOW":  "APPROVED_CONDITIONAL",
    "MEDIUM_HIGH": "MANUAL_REVIEW",
    "HIGH":        "REJECTED",
}

# Pricing bounds from config.yaml (pricing_policy section).
_APR_MIN: float = 6.0    # min_rate
_APR_MAX: float = 24.0   # max_rate — Dieu 468 BLDS statutory cap


@pytest.fixture(scope="session")
def universal_assertions() -> Callable[[requests.Response], dict[str, Any]]:
    """
    Returns a callable that enforces the six baseline invariants on every
    HTTP 200 response from POST /api/v1/predict.

    Call signature inside tests:
        assessment = universal_assertions(response)

    Returns the `credit_risk_assessment` dict for further test-specific
    assertions.
    """

    def _assert(response: requests.Response) -> dict[str, Any]:
        """
        Invariant 1: Response is HTTP 200.
        Invariant 2: pd_score is a valid probability [0.0, 1.0].
        Invariant 3: credit_score is within FICO bounds [300, 850].
        Invariant 4: risk_tier and decision are always paired correctly.
        Invariant 5: Pricing APR is within statutory bounds [6.0, 24.0].
        Invariant 6: REJECTED decision always yields max_credit_limit = 0.0.
        """
        assert response.status_code == 200, (
            f"Expected HTTP 200, got {response.status_code}. "
            f"Body: {response.text[:500]}"
        )

        body: dict[str, Any] = response.json()
        assert body.get("success") is True, "Response field 'success' must be True."

        assessment: dict[str, Any] = body["credit_risk_assessment"]

        # Invariant 2 — PD is a valid probability
        pd_score: float = assessment["pd_score"]
        assert 0.0 <= pd_score <= 1.0, (
            f"pd_score {pd_score!r} is outside valid probability range [0.0, 1.0]."
        )

        # Invariant 3 — Credit score within FICO bounds
        credit_score: int = assessment["credit_score"]
        assert 300 <= credit_score <= 850, (
            f"credit_score {credit_score!r} is outside FICO bounds [300, 850]."
        )

        # Invariant 4 — Risk tier / decision coupling (no mixed state allowed)
        risk_tier: str = assessment["risk_tier"]
        decision: str = assessment["decision"]
        expected_decision: str = _VALID_TIER_DECISION_PAIRS.get(risk_tier, "__UNKNOWN__")
        assert decision == expected_decision, (
            f"Mixed state detected: risk_tier={risk_tier!r} implies "
            f"decision={expected_decision!r}, but got {decision!r}."
        )

        # Invariant 5 — APR within statutory bounds (if pricing_recommendation is present)
        pricing: dict[str, Any] | None = assessment.get("pricing_recommendation")
        if pricing is not None:
            apr: float = pricing["recommended_interest_rate"]
            assert _APR_MIN <= apr <= _APR_MAX, (
                f"APR {apr}% violates statutory bounds [{_APR_MIN}, {_APR_MAX}]. "
                f"This may constitute a Dieu 468 BLDS violation."
            )

            # Invariant 6 — REJECTED => zero credit limit
            if decision == "REJECTED":
                assert pricing["max_credit_limit"] == 0.0, (
                    f"REJECTED applicant must have max_credit_limit=0.0, "
                    f"got {pricing['max_credit_limit']}."
                )
                assert pricing["limit_status"] == "REJECTED", (
                    f"REJECTED applicant must have limit_status='REJECTED', "
                    f"got {pricing['limit_status']!r}."
                )

        return assessment


    return _assert
