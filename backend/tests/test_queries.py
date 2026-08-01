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
# DATASET TEST CONFIGURATION
# ============================================================

TEST_SUITES = {

    # --------------------------------------------------------
    # HOSPITAL
    # --------------------------------------------------------

    "hospital": {
        "filename": "hospital.csv",
        "queries": [

            # -----------------------------
            # Metadata / dataset overview
            # -----------------------------

            "describe dataset",
            "show columns",
            "show schema",

            # -----------------------------
            # Row retrieval
            # -----------------------------

            "show rows",
            "show 10 rows",
            "top 10 rows",
            "bottom 10 rows",

            # -----------------------------
            # Aggregations
            # -----------------------------

            "average cost",
            "maximum cost",
            "minimum cost",
            "average age",
            "average length of stay",

            # -----------------------------
            # Numeric filters
            # -----------------------------

            "average cost for age > 40",
            "average cost for age < 40",
            "average cost for age >= 40",
            "average cost for age <= 40",

            "average cost for age greater than 40",
            "average cost for age above 40",
            "average cost for age over 40",

            "average cost for age less than 40",
            "average cost for age below 40",
            "average cost for age under 40",

            "average cost for age at least 40",
            "average cost for age at most 40",
            "average cost for age equals 40",

            # -----------------------------
            # Categorical filters
            # -----------------------------

            "show rows where gender is female",
            "show rows where outcome is recovered",

            # -----------------------------
            # Grouped analytics
            # -----------------------------

            "average cost by condition",
            "average cost by procedure",
            "average length of stay by condition",

            # -----------------------------
            # Combined
            # -----------------------------

            "average cost where gender is female",
            "average length of stay where outcome is recovered",

            # -----------------------------
            # Ranking
            # -----------------------------

            "top 5 conditions by cost",
            "bottom 5 procedures by cost",
        ],
    },

    # --------------------------------------------------------
    # SALES
    # --------------------------------------------------------

    "sales": {
        "filename": "sales.csv",
        "queries": [

            # -----------------------------
            # Metadata
            # -----------------------------

            "describe dataset",
            "show columns",
            "show schema",

            # -----------------------------
            # Row retrieval
            # -----------------------------

            "show rows",
            "show me rows",
            "display rows",
            "list rows",

            "show 10 rows",
            "show 25 rows",
            "show all rows",

            "top 10 rows",
            "bottom 10 rows",
            "first 15 rows",
            "last 20 rows",

            # -----------------------------
            # Aggregations
            # -----------------------------

            "average transaction amount",
            "sum transaction amount",
            "maximum transaction amount",
            "minimum transaction amount",

            # -----------------------------
            # Grouping
            # -----------------------------

            "average transaction amount by category",
            "average transaction amount by city",
            "sum transaction amount by category",

            # -----------------------------
            # Filters
            # -----------------------------

            "show rows where city is delhi",
            "average transaction amount where city is delhi",

            # -----------------------------
            # Ranking
            # -----------------------------

            "top 5 categories by transaction amount",
            "bottom 10 cities by transaction amount",
        ],
    },

    # --------------------------------------------------------
    # CARTOON / VIEWER
    # --------------------------------------------------------

    "cartoon": {
        "filename": "cartoon.csv",
        "queries": [

            # -----------------------------
            # Metadata
            # -----------------------------

            "describe dataset",
            "show columns",
            "show schema",

            # -----------------------------
            # Row retrieval
            # -----------------------------

            "show rows",
            "show 10 rows",
            "show all rows",

            # -----------------------------
            # Aggregations
            # -----------------------------

            "average viewing time",
            "sum viewing time",
            "maximum viewing time",
            "minimum viewing time",

            # -----------------------------
            # Filters
            # -----------------------------

            "show rows where city is hyderabad",
            "average viewing time where city is hyderabad",

            "show viewers with age > 15",

            # -----------------------------
            # Grouped analytics
            # -----------------------------

            "average viewing time by city",
            "average viewing time by favorite cartoon",

            # -----------------------------
            # Ranking
            # -----------------------------

            "top 5 cities by viewing time",
            "bottom 5 favorite cartoons by viewing time",

            # Important regression case
            "which cartoon has the highest average viewing time?",

            # Comparison regression
            "How does average viewing time compare between subscribers and non-subscribers?",
        ],
    },

    # --------------------------------------------------------
    # FLOWER
    # --------------------------------------------------------

    "flower": {
        "filename": "flower.csv",
        "queries": [

            # -----------------------------
            # Metadata
            # -----------------------------

            "describe dataset",
            "show columns",
            "show schema",

            # -----------------------------
            # Row retrieval
            # -----------------------------

            "show rows",
            "show 10 rows",
            "show all rows",

            # -----------------------------
            # Aggregations
            # -----------------------------

            "average height",
            "sum height",
            "maximum height",
            "minimum height",

            # -----------------------------
            # Categorical filters
            # -----------------------------

            "average height for roses",
            "show rows where species is rose",
            "show rows where fragrance is mild",

            # -----------------------------
            # Numeric filters
            # -----------------------------

            "show species with height < 150",

            # -----------------------------
            # Multiple filters
            # -----------------------------

            "show species with height < 150 and fragrance strong",

            # -----------------------------
            # Grouped analytics
            # -----------------------------

            "average height by species",
            "average height by fragrance",
            "count species by size",

            # -----------------------------
            # Ranking
            # -----------------------------

            "top 3 species by height",
            "which species has the highest average height?",
        ],
    },
}


# ============================================================
# KNOWN V1 LIMITATIONS
# ============================================================

KNOWN_LIMITATIONS = {

    "flower": [
        (
            "how does average height compare between small and large sizes?",
            "Multi-value comparison on the same categorical column "
            "is deferred to V1.1.",
        ),
    ],
}


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
        raise RuntimeError(
            f"Dataset upload failed: {data}"
        )

    session_id = data.get("session_id")

    if not session_id:
        raise RuntimeError(
            "Upload succeeded but no session_id was returned."
        )

    return session_id, data


def run_query(session_id, question):
    """
    Executes a deterministic analytics query.
    """

    return requests.get(
        f"{BASE_URL}/query",
        params={
            "session_id": session_id,
            "question": question,
        },
        timeout=30,
    )


# ============================================================
# RESPONSE VALIDATION
# ============================================================

def validate_success_response(response):
    """
    Phase 1 regression validation.

    A query passes when:
    - HTTP status is 200
    - response is valid JSON
    - response reports success=True

    Exact analytical correctness assertions will be added
    during Phase 2.
    """

    if response.status_code != 200:
        return (
            False,
            f"HTTP {response.status_code}",
            None,
        )

    try:
        data = response.json()
    except Exception:
        return (
            False,
            "Response is not valid JSON.",
            None,
        )

    if not data.get("success", False):
        return (
            False,
            data.get(
                "error",
                "Response returned success=False.",
            ),
            data,
        )

    return True, None, data


# ============================================================
# LOGGING HELPERS
# ============================================================

def separator(character="=", length=80):
    return character * length


# ============================================================
# DATASET TEST RUNNER
# ============================================================

def run_dataset_suite(
    dataset_name,
    config,
    write,
):
    """
    Uploads one dataset and executes all supported
    V1 regression queries for that dataset.
    """

    filename = config["filename"]

    filepath = os.path.join(
        DATASETS_DIR,
        filename,
    )

    write()
    write(separator())
    write(f"DATASET: {dataset_name.upper()}")
    write(separator())
    write(f"File: {filepath}")

    if not os.path.exists(filepath):

        write(
            f"❌ DATASET NOT FOUND: {filename}"
        )

        return {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "dataset_error": True,
        }

    # --------------------------------------------------------
    # Upload dataset
    # --------------------------------------------------------

    try:

        session_id, upload_data = upload_dataset(
            filepath
        )

    except Exception as error:

        write(
            f"❌ UPLOAD FAILED: {error}"
        )

        return {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "dataset_error": True,
        }

    write(
        f"Session ID : {session_id}"
    )

    write(
        f"Rows       : {upload_data.get('rows')}"
    )

    write(
        f"Columns    : {upload_data.get('columns')}"
    )

    write(separator("-"))

    passed = 0
    failed = 0
    skipped = 0

    # --------------------------------------------------------
    # Supported regression tests
    # --------------------------------------------------------

    for question in config["queries"]:

        try:

            response = run_query(
                session_id,
                question,
            )

            (
                success,
                reason,
                _,
            ) = validate_success_response(
                response
            )

            if success:

                passed += 1

                write(
                    f"✅ PASS | {question}"
                )

            else:

                failed += 1

                write(
                    f"❌ FAIL | {question}"
                )

                write(
                    f"         Reason: {reason}"
                )

        except Exception as error:

            failed += 1

            write(
                f"❌ ERROR | {question}"
            )

            write(
                f"          Reason: {error}"
            )

    # --------------------------------------------------------
    # Known V1 limitations
    # --------------------------------------------------------

    limitations = KNOWN_LIMITATIONS.get(
        dataset_name,
        [],
    )

    if limitations:

        write()
        write("KNOWN V1 LIMITATIONS")
        write(separator("-"))

        for question, reason in limitations:

            skipped += 1

            write(
                f"🟡 SKIP | {question}"
            )

            write(
                f"         Reason: {reason}"
            )

    # --------------------------------------------------------
    # Dataset summary
    # --------------------------------------------------------

    write()
    write(
        f"Dataset Result: "
        f"{passed} passed, "
        f"{failed} failed, "
        f"{skipped} known limitations"
    )

    return {
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "dataset_error": False,
    }


# ============================================================
# MAIN REGRESSION RUNNER
# ============================================================

def main():

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    log_file = os.path.join(
        CURRENT_DIR,
        f"regression_results_{timestamp}.txt",
    )

    total_passed = 0
    total_failed = 0
    total_skipped = 0

    dataset_errors = 0

    with open(
        log_file,
        "w",
        encoding="utf-8",
    ) as log:

        def write(text=""):
            print(text)
            log.write(text + "\n")

        write(separator())
        write("DataSage V1 — Regression Report")
        write(
            "Generated: "
            + datetime.now().strftime(
                "%d-%m-%Y %H:%M:%S"
            )
        )
        write(separator())

        # ----------------------------------------------------
        # Run every dataset suite
        # ----------------------------------------------------

        for (
            dataset_name,
            config,
        ) in TEST_SUITES.items():

            result = run_dataset_suite(
                dataset_name,
                config,
                write,
            )

            total_passed += result["passed"]
            total_failed += result["failed"]
            total_skipped += result["skipped"]

            if result["dataset_error"]:
                dataset_errors += 1

        # ----------------------------------------------------
        # Final report
        # ----------------------------------------------------

        write()
        write(separator())
        write("FINAL REGRESSION SUMMARY")
        write(separator())

        write(
            f"Passed             : {total_passed}"
        )

        write(
            f"Failed             : {total_failed}"
        )

        write(
            f"Known Limitations  : {total_skipped}"
        )

        write(
            f"Dataset Errors     : {dataset_errors}"
        )

        executed_tests = (
            total_passed
            + total_failed
        )

        if executed_tests > 0:

            success_rate = (
                total_passed
                / executed_tests
                * 100
            )

        else:
            success_rate = 0.0

        write(
            f"Success Rate       : "
            f"{success_rate:.2f}%"
        )

        write(separator())

        # ----------------------------------------------------
        # Release gate
        # ----------------------------------------------------

        if (
            total_failed == 0
            and dataset_errors == 0
        ):

            write()
            write(
                "🟢 V1 CORE REGRESSION GATE: PASS"
            )

            write(
                "No failures were detected in the "
                "supported regression suite."
            )

        else:

            write()
            write(
                "🔴 V1 CORE REGRESSION GATE: FAIL"
            )

            write(
                "Review failing supported tests before "
                "deployment."
            )

    print()
    print(separator())
    print("Regression report saved to:")
    print(log_file)
    print(separator())


if __name__ == "__main__":
    main()