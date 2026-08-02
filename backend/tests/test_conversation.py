import os
from datetime import datetime

import requests


# ============================================================
# CONFIGURATION
# ============================================================

BASE_URL = "http://127.0.0.1:8000"

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATASETS_DIR = os.path.join(
    CURRENT_DIR,
    "dataset",
)


# ============================================================
# HTTP HELPERS
# ============================================================

def upload_dataset(filepath):
    """
    Uploads a dataset and returns its session ID.
    """

    with open(filepath, "rb") as file:

        response = requests.post(
            f"{BASE_URL}/upload/",
            files={
                "file": (
                    os.path.basename(filepath),
                    file,
                    "text/csv",
                )
            },
            timeout=30,
        )

    response.raise_for_status()

    data = response.json()

    if data.get("status") != "success":
        raise AssertionError(
            f"Dataset upload failed: {data}"
        )

    session_id = data.get("session_id")

    if not session_id:
        raise AssertionError(
            "Upload succeeded but session_id "
            "was not returned."
        )

    return session_id


def chat(session_id, question):
    """
    Sends a message through the real conversational
    /chat/ endpoint.
    """

    response = requests.post(
        f"{BASE_URL}/chat/",
        json={
            "session_id": session_id,
            "follow_up_question": question,
        },
        timeout=120,
    )

    # Give us the actual FastAPI validation response
    # if the request contract is ever wrong again.
    if response.status_code != 200:
        raise AssertionError(
            f"Chat endpoint returned HTTP "
            f"{response.status_code}: "
            f"{response.text}"
        )

    try:
        data = response.json()

    except ValueError as error:
        raise AssertionError(
            "Chat endpoint returned invalid JSON."
        ) from error

    if not data.get("success", False):
        raise AssertionError(
            f"Chat request failed: {data}"
        )

    return data


# ============================================================
# ASSERTION HELPERS
# ============================================================

def assert_mode(response, expected_mode):

    actual_mode = response.get("mode")

    if actual_mode != expected_mode:
        raise AssertionError(
            f"Expected mode '{expected_mode}', "
            f"got '{actual_mode}'."
        )


def assert_response_object(response):

    inner = response.get("response")

    if not isinstance(inner, dict):
        raise AssertionError(
            "Expected response.response to be "
            "a JSON object."
        )

    return inner


def assert_insight_response(response):

    inner = assert_response_object(
        response
    )

    if inner.get("type") != "insight":
        raise AssertionError(
            "Expected insight response type, "
            f"got '{inner.get('type')}'."
        )

    insight = inner.get("insight")

    if not isinstance(insight, str):
        raise AssertionError(
            "Insight response does not contain "
            "text."
        )

    if not insight.strip():
        raise AssertionError(
            "Insight response is empty."
        )

    return insight


def assert_analytics_response(response):

    inner = assert_response_object(
        response
    )

    if not inner.get("success", False):
        raise AssertionError(
            f"Inner analytics response failed: "
            f"{inner}"
        )

    response_type = inner.get("type")

    if response_type not in {
        "kpi",
        "structured",
    }:
        raise AssertionError(
            "Expected KPI or structured "
            f"analytics response, got "
            f"'{response_type}'."
        )

    return inner


# ============================================================
# TEST RUNNER
# ============================================================

class ConversationTestRunner:

    def __init__(self):

        self.passed = 0
        self.failed = 0
        self.failures = []

    def run(
        self,
        name,
        test_function,
    ):

        try:

            test_function()

            self.passed += 1

            print(
                f"✅ PASS | {name}"
            )

        except Exception as error:

            self.failed += 1

            self.failures.append(
                (name, str(error))
            )

            print(
                f"❌ FAIL | {name}"
            )

            print(
                f"         {error}"
            )


# ============================================================
# CARTOON CONVERSATION TESTS
# ============================================================

def test_cartoon_conversation(runner):

    filepath = os.path.join(
        DATASETS_DIR,
        "cartoon.csv",
    )

    session_id = upload_dataset(
        filepath
    )

    print()
    print("=" * 80)
    print("CARTOON — CONVERSATION QA")
    print("=" * 80)

    # --------------------------------------------------------
    # 1. Dataset exploration routing
    # --------------------------------------------------------

    def dataset_exploration():

        response = chat(
            session_id,
            "What can I analyze?",
        )

        assert_mode(
            response,
            "dataset_description",
        )

        insight = assert_insight_response(
            response
        )

        if len(insight) < 20:
            raise AssertionError(
                "Dataset description is "
                "unexpectedly short."
            )

    runner.run(
        "Dataset exploration routes to description",
        dataset_exploration,
    )

    # --------------------------------------------------------
    # 2. Deterministic analytics routing
    # --------------------------------------------------------

    def analytical_query():

        response = chat(
            session_id,
            "Which cartoon has the highest "
            "average viewing time?",
        )

        assert_mode(
            response,
            "analytics",
        )

        inner = assert_analytics_response(
            response
        )

        table = inner.get("table")

        if not isinstance(table, list):
            raise AssertionError(
                "Expected ranked analytics table."
            )

        if len(table) != 1:
            raise AssertionError(
                "Highest-ranking query should "
                "return exactly one result."
            )

    runner.run(
        "Analytical query routes to analytics",
        analytical_query,
    )

    # --------------------------------------------------------
    # 3. Contextual interpretation routing
    #
    # IMPORTANT:
    # Run a fresh analytical query immediately before
    # the follow-up so this test does not depend on
    # another test having populated session context.
    # --------------------------------------------------------

    def contextual_followup():

        chat(
            session_id,
            "Which cartoon has the highest "
            "average viewing time?",
        )

        response = chat(
            session_id,
            "What does this suggest?",
        )

        assert_mode(
            response,
            "insight",
        )

        assert_insight_response(
            response
        )

    runner.run(
        "Contextual follow-up routes to insight",
        contextual_followup,
    )

    # --------------------------------------------------------
    # 4. Explanation follow-up
    # --------------------------------------------------------

    def explanation_followup():

        chat(
            session_id,
            "Average viewing time by city",
        )

        response = chat(
            session_id,
            "Why might this differ?",
        )

        assert_mode(
            response,
            "insight",
        )

        assert_insight_response(
            response
        )

    runner.run(
        "Explanation follow-up routes to insight",
        explanation_followup,
    )

    # --------------------------------------------------------
    # 5. Evidence / conclusion follow-up
    # --------------------------------------------------------

    def evidence_followup():

        chat(
            session_id,
            "Which cartoon has the highest "
            "average viewing time?",
        )

        response = chat(
            session_id,
            "Does this prove that people "
            "prefer Mickey Mouse?",
        )

        assert_mode(
            response,
            "insight",
        )

        insight = assert_insight_response(
            response
        )

        normalized = insight.lower()

        # We do not assert exact AI wording.
        #
        # We only require some sign that the model
        # treats the conclusion cautiously.
        caution_markers = {
            "not",
            "cannot",
            "doesn't",
            "does not",
            "insufficient",
            "alone",
            "prove",
        }

        if not any(
            marker in normalized
            for marker in caution_markers
        ):
            raise AssertionError(
                "AI response does not appear to "
                "qualify the causal/evidential claim."
            )

    runner.run(
        "Evidence question receives cautious insight",
        evidence_followup,
    )

    # --------------------------------------------------------
    # 6. New analytics replaces latest context
    # --------------------------------------------------------

    def latest_context_replacement():

        # Old context
        chat(
            session_id,
            "Which cartoon has the highest "
            "average viewing time?",
        )

        # New context
        new_analysis = chat(
            session_id,
            "Average viewing time by city",
        )

        assert_mode(
            new_analysis,
            "analytics",
        )

        # Follow-up should now be grounded in the
        # city analysis rather than the cartoon one.
        followup = chat(
            session_id,
            "What does this suggest?",
        )

        assert_mode(
            followup,
            "insight",
        )

        insight = assert_insight_response(
            followup
        )

        normalized = insight.lower()

        # This is intentionally a lightweight
        # semantic check rather than exact wording.
        if (
            "city" not in normalized
            and "cities" not in normalized
        ):
            raise AssertionError(
                "Follow-up does not appear to use "
                "the latest city-based analysis."
            )

    runner.run(
        "Latest analytical result replaces old context",
        latest_context_replacement,
    )


# ============================================================
# FLOWER CONVERSATION TESTS
# ============================================================

def test_flower_conversation(runner):

    filepath = os.path.join(
        DATASETS_DIR,
        "flower.csv",
    )

    session_id = upload_dataset(
        filepath
    )

    print()
    print("=" * 80)
    print("FLOWER — CONVERSATION QA")
    print("=" * 80)

    # --------------------------------------------------------
    # 7. Dataset description on unrelated schema
    # --------------------------------------------------------

    def dataset_description():

        response = chat(
            session_id,
            "What is in this dataset?",
        )

        assert_mode(
            response,
            "dataset_description",
        )

        assert_insight_response(
            response
        )

    runner.run(
        "Flower dataset description",
        dataset_description,
    )

    # --------------------------------------------------------
    # 8. Scalar analytics through /chat/
    # --------------------------------------------------------

    def scalar_analytics():

        response = chat(
            session_id,
            "Average height for roses",
        )

        assert_mode(
            response,
            "analytics",
        )

        inner = assert_analytics_response(
            response
        )

        if inner.get("type") != "kpi":
            raise AssertionError(
                "Expected KPI response for "
                "scalar analytical query."
            )

        if "value" not in inner:
            raise AssertionError(
                "KPI response has no value."
            )

    runner.run(
        "Scalar analytics through chat",
        scalar_analytics,
    )

    # --------------------------------------------------------
    # 9. Follow-up after scalar result
    # --------------------------------------------------------

    def scalar_followup():

        chat(
            session_id,
            "Average height for roses",
        )

        response = chat(
            session_id,
            "What does this mean?",
        )

        assert_mode(
            response,
            "insight",
        )

        assert_insight_response(
            response
        )

    runner.run(
        "Scalar result supports contextual follow-up",
        scalar_followup,
    )


# ============================================================
# SESSION ISOLATION
# ============================================================

def test_session_isolation(runner):

    cartoon_path = os.path.join(
        DATASETS_DIR,
        "cartoon.csv",
    )

    flower_path = os.path.join(
        DATASETS_DIR,
        "flower.csv",
    )

    cartoon_session = upload_dataset(
        cartoon_path
    )

    flower_session = upload_dataset(
        flower_path
    )

    print()
    print("=" * 80)
    print("SESSION ISOLATION")
    print("=" * 80)

    # --------------------------------------------------------
    # 10. Two sessions use different datasets
    # --------------------------------------------------------

    def independent_datasets():

        cartoon_response = chat(
            cartoon_session,
            "Average viewing time",
        )

        flower_response = chat(
            flower_session,
            "Average height",
        )

        assert_mode(
            cartoon_response,
            "analytics",
        )

        assert_mode(
            flower_response,
            "analytics",
        )

        cartoon_inner = (
            assert_analytics_response(
                cartoon_response
            )
        )

        flower_inner = (
            assert_analytics_response(
                flower_response
            )
        )

        cartoon_title = (
            cartoon_inner
            .get("title", "")
            .lower()
        )

        flower_title = (
            flower_inner
            .get("title", "")
            .lower()
        )

        if "viewing" not in cartoon_title:
            raise AssertionError(
                "Cartoon session appears to have "
                "lost its dataset context."
            )

        if "height" not in flower_title:
            raise AssertionError(
                "Flower session appears to have "
                "lost its dataset context."
            )

    runner.run(
        "Sessions retain independent datasets",
        independent_datasets,
    )

    # --------------------------------------------------------
    # 11. Insight context remains session-local
    # --------------------------------------------------------

    def independent_followup_context():

        chat(
            cartoon_session,
            "Average viewing time by city",
        )

        chat(
            flower_session,
            "Average height by species",
        )

        cartoon_followup = chat(
            cartoon_session,
            "What does this suggest?",
        )

        flower_followup = chat(
            flower_session,
            "What does this suggest?",
        )

        assert_mode(
            cartoon_followup,
            "insight",
        )

        assert_mode(
            flower_followup,
            "insight",
        )

        cartoon_insight = (
            assert_insight_response(
                cartoon_followup
            )
            .lower()
        )

        flower_insight = (
            assert_insight_response(
                flower_followup
            )
            .lower()
        )

        if (
            "city" not in cartoon_insight
            and "cities" not in cartoon_insight
        ):
            raise AssertionError(
                "Cartoon insight may not be using "
                "its own latest analysis."
            )

        if (
            "species" not in flower_insight
            and "height" not in flower_insight
        ):
            raise AssertionError(
                "Flower insight may not be using "
                "its own latest analysis."
            )

    runner.run(
        "Insight context remains session-local",
        independent_followup_context,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print(
        "DataSage V1 — Conversation QA"
    )
    print(
        "Generated:",
        datetime.now().strftime(
            "%d-%m-%Y %H:%M:%S"
        ),
    )
    print("=" * 80)

    runner = ConversationTestRunner()

    test_cartoon_conversation(
        runner
    )

    test_flower_conversation(
        runner
    )

    test_session_isolation(
        runner
    )

    print()
    print("=" * 80)
    print(
        "CONVERSATION QA SUMMARY"
    )
    print("=" * 80)

    print(
        f"Passed : {runner.passed}"
    )

    print(
        f"Failed : {runner.failed}"
    )

    total = (
        runner.passed
        + runner.failed
    )

    success_rate = (
        runner.passed
        / total
        * 100
        if total
        else 0.0
    )

    print(
        f"Success Rate : "
        f"{success_rate:.2f}%"
    )

    if runner.failures:

        print()
        print("FAILURES")
        print("-" * 80)

        for name, reason in runner.failures:

            print(
                f"❌ {name}"
            )

            print(
                f"   {reason}"
            )

    print("=" * 80)

    if runner.failed == 0:

        print()
        print(
            "🟢 V1 CONVERSATION QA GATE: PASS"
        )

        print(
            "Routing, contextual follow-ups, "
            "latest-result context, and session "
            "isolation passed."
        )

    else:

        print()
        print(
            "🔴 V1 CONVERSATION QA GATE: FAIL"
        )

        print(
            "Review conversation-layer failures "
            "before deployment."
        )


if __name__ == "__main__":
    main()