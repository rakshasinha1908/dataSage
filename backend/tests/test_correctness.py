import math
import os
from datetime import datetime

import pandas as pd
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
    Uploads a dataset and returns the generated session ID.
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

    return session_id


def run_query(session_id, question):
    """
    Executes a query against DataSage.
    """

    response = requests.get(
        f"{BASE_URL}/query",
        params={
            "session_id": session_id,
            "question": question,
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if not data.get("success", False):
        raise AssertionError(
            data.get(
                "error",
                "DataSage returned success=False.",
            )
        )

    return data


# ============================================================
# ASSERTION HELPERS
# ============================================================

def assert_number_close(
    actual,
    expected,
    rel_tol=1e-9,
    abs_tol=1e-9,
):
    """
    Safely compares floating-point analytical values.
    """

    if not math.isclose(
        float(actual),
        float(expected),
        rel_tol=rel_tol,
        abs_tol=abs_tol,
    ):
        raise AssertionError(
            f"Expected {expected}, got {actual}"
        )


def assert_kpi_value(
    response,
    expected,
):
    """
    Verifies a scalar KPI response.
    """

    if response.get("type") != "kpi":
        raise AssertionError(
            f"Expected KPI response, got: "
            f"{response.get('type')}"
        )

    if "value" not in response:
        raise AssertionError(
            "KPI response does not contain 'value'."
        )

    assert_number_close(
        response["value"],
        expected,
    )


def table_to_dict(response):
    """
    Converts a grouped DataSage response into:

        {
            label: value
        }
    """

    if response.get("type") != "structured":
        raise AssertionError(
            f"Expected structured response, got: "
            f"{response.get('type')}"
        )

    table = response.get("table")

    if not isinstance(table, list):
        raise AssertionError(
            "Structured response does not contain "
            "a valid table."
        )

    result = {}

    for row in table:

        if (
            "label" not in row
            or "value" not in row
        ):
            raise AssertionError(
                f"Invalid grouped row: {row}"
            )

        result[row["label"]] = row["value"]

    return result


def assert_grouped_values(
    response,
    expected_series,
):
    """
    Compares a grouped DataSage result against
    an independently computed Pandas Series.
    """

    actual = table_to_dict(response)

    expected = expected_series.to_dict()

    if set(actual.keys()) != set(expected.keys()):
        raise AssertionError(
            "Grouped labels differ.\n"
            f"Expected: {set(expected.keys())}\n"
            f"Actual:   {set(actual.keys())}"
        )

    for label, expected_value in expected.items():

        assert_number_close(
            actual[label],
            expected_value,
        )


def assert_ranked_values(
    response,
    expected_series,
):
    """
    Verifies ranking labels, ordering, limits,
    and values.
    """

    if response.get("type") != "structured":
        raise AssertionError(
            "Expected structured ranked response."
        )

    table = response.get("table", [])

    actual_labels = [
        row["label"]
        for row in table
    ]

    actual_values = [
        row["value"]
        for row in table
    ]

    expected_labels = list(
        expected_series.index
    )

    expected_values = list(
        expected_series.values
    )

    if actual_labels != expected_labels:
        raise AssertionError(
            "Ranking order differs.\n"
            f"Expected: {expected_labels}\n"
            f"Actual:   {actual_labels}"
        )

    if len(actual_values) != len(expected_values):
        raise AssertionError(
            f"Expected {len(expected_values)} rows, "
            f"got {len(actual_values)}."
        )

    for actual, expected in zip(
        actual_values,
        expected_values,
    ):
        assert_number_close(
            actual,
            expected,
        )


# ============================================================
# GOLDEN TEST RUNNER
# ============================================================

class GoldenTestRunner:

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
# FLOWER GOLDEN TESTS
# ============================================================

def test_flower_dataset(runner):

    filepath = os.path.join(
        DATASETS_DIR,
        "flower.csv",
    )

    df = pd.read_csv(filepath)

    session_id = upload_dataset(
        filepath
    )

    print()
    print("=" * 80)
    print("FLOWER — GOLDEN CORRECTNESS")
    print("=" * 80)

    # --------------------------------------------------------
    # 1. Scalar mean
    # --------------------------------------------------------

    def scalar_mean():

        response = run_query(
            session_id,
            "average height",
        )

        expected = df[
            "height_cm"
        ].mean()

        assert_kpi_value(
            response,
            expected,
        )

    runner.run(
        "Flower scalar mean",
        scalar_mean,
    )

    # --------------------------------------------------------
    # 2. Scalar maximum
    # --------------------------------------------------------

    def scalar_max():

        response = run_query(
            session_id,
            "maximum height",
        )

        expected = df[
            "height_cm"
        ].max()

        assert_kpi_value(
            response,
            expected,
        )

    runner.run(
        "Flower scalar maximum",
        scalar_max,
    )

    # --------------------------------------------------------
    # 3. Categorical filter + mean
    # --------------------------------------------------------

    def filtered_mean():

        response = run_query(
            session_id,
            "average height for roses",
        )

        expected = (
            df.loc[
                df["species"] == "rose",
                "height_cm",
            ]
            .mean()
        )

        assert_kpi_value(
            response,
            expected,
        )

    runner.run(
        "Flower categorical filter + mean",
        filtered_mean,
    )

    # --------------------------------------------------------
    # 4. Grouped mean
    # --------------------------------------------------------

    def grouped_mean():

        response = run_query(
            session_id,
            "average height by species",
        )

        expected = (
            df.groupby("species")[
                "height_cm"
            ]
            .mean()
            .sort_values(
                ascending=False
            )
        )

        assert_grouped_values(
            response,
            expected,
        )

    runner.run(
        "Flower grouped mean",
        grouped_mean,
    )

    # --------------------------------------------------------
    # 5. Grouped count
    # --------------------------------------------------------

    def grouped_count():

        response = run_query(
            session_id,
            "count species by size",
        )

        expected = (
            df.groupby("size")
            .size()
            .sort_values(
                ascending=False
            )
        )

        assert_grouped_values(
            response,
            expected,
        )

    runner.run(
        "Flower grouped count",
        grouped_count,
    )

    # --------------------------------------------------------
    # 6. Top 3 grouped sum
    # --------------------------------------------------------

    def top_three():

        response = run_query(
            session_id,
            "top 3 species by height",
        )

        expected = (
            df.groupby("species")[
                "height_cm"
            ]
            .sum()
            .sort_values(
                ascending=False
            )
            .head(3)
        )

        assert_ranked_values(
            response,
            expected,
        )

    runner.run(
        "Flower top 3 ranking",
        top_three,
    )

    # --------------------------------------------------------
    # 7. Highest average
    # --------------------------------------------------------

    def highest_average():

        response = run_query(
            session_id,
            "which species has the highest average height?",
        )

        expected = (
            df.groupby("species")[
                "height_cm"
            ]
            .mean()
            .sort_values(
                ascending=False
            )
            .head(1)
        )

        assert_ranked_values(
            response,
            expected,
        )

    runner.run(
        "Flower singular highest ranking",
        highest_average,
    )


# ============================================================
# HOSPITAL GOLDEN TESTS
# ============================================================

def test_hospital_dataset(runner):

    filepath = os.path.join(
        DATASETS_DIR,
        "hospital.csv",
    )

    df = pd.read_csv(filepath)

    session_id = upload_dataset(
        filepath
    )

    print()
    print("=" * 80)
    print("HOSPITAL — GOLDEN CORRECTNESS")
    print("=" * 80)

    # --------------------------------------------------------
    # 8. Numeric filter + mean
    # --------------------------------------------------------

    def numeric_filter_mean():

        response = run_query(
            session_id,
            "average cost for age > 40",
        )

        expected = (
            df.loc[
                df["Age"] > 40,
                "Cost",
            ]
            .mean()
        )

        assert_kpi_value(
            response,
            expected,
        )

    runner.run(
        "Hospital numeric filter + mean",
        numeric_filter_mean,
    )

    # --------------------------------------------------------
    # 9. Categorical filter + mean
    # --------------------------------------------------------

    def categorical_filter_mean():

        response = run_query(
            session_id,
            "average cost where gender is female",
        )

        expected = (
            df.loc[
                df["Gender"].str.lower()
                == "female",
                "Cost",
            ]
            .mean()
        )

        assert_kpi_value(
            response,
            expected,
        )

    runner.run(
        "Hospital categorical filter + mean",
        categorical_filter_mean,
    )

    # --------------------------------------------------------
    # 10. Grouped mean
    # --------------------------------------------------------

    def grouped_mean():

        response = run_query(
            session_id,
            "average cost by condition",
        )

        expected = (
            df.groupby("Condition")[
                "Cost"
            ]
            .mean()
            .sort_values(
                ascending=False
            )
        )

        assert_grouped_values(
            response,
            expected,
        )

    runner.run(
        "Hospital grouped mean",
        grouped_mean,
    )


# ============================================================
# SALES GOLDEN TESTS
# ============================================================

def test_sales_dataset(runner):

    filepath = os.path.join(
        DATASETS_DIR,
        "sales.csv",
    )

    df = pd.read_csv(filepath)

    session_id = upload_dataset(
        filepath
    )

    print()
    print("=" * 80)
    print("SALES — GOLDEN CORRECTNESS")
    print("=" * 80)

    # --------------------------------------------------------
    # 11. Scalar sum
    # --------------------------------------------------------

    def scalar_sum():

        response = run_query(
            session_id,
            "sum transaction amount",
        )

        expected = df[
            "transaction_amount"
        ].sum()

        assert_kpi_value(
            response,
            expected,
        )

    runner.run(
        "Sales scalar sum",
        scalar_sum,
    )

    # --------------------------------------------------------
    # 12. Grouped mean
    # --------------------------------------------------------

    def grouped_mean():

        response = run_query(
            session_id,
            "average transaction amount by city",
        )

        expected = (
            df.groupby("city")[
                "transaction_amount"
            ]
            .mean()
            .sort_values(
                ascending=False
            )
        )

        assert_grouped_values(
            response,
            expected,
        )

    runner.run(
        "Sales grouped mean",
        grouped_mean,
    )


# ============================================================
# CARTOON GOLDEN TESTS
# ============================================================

def test_cartoon_dataset(runner):

    filepath = os.path.join(
        DATASETS_DIR,
        "cartoon.csv",
    )

    df = pd.read_csv(filepath)

    session_id = upload_dataset(
        filepath
    )

    print()
    print("=" * 80)
    print("CARTOON — GOLDEN CORRECTNESS")
    print("=" * 80)

    # --------------------------------------------------------
    # 13. Scalar mean
    # --------------------------------------------------------

    def scalar_mean():

        response = run_query(
            session_id,
            "average viewing time",
        )

        expected = df[
            "Viewing Time (hours)"
        ].mean()

        assert_kpi_value(
            response,
            expected,
        )

    runner.run(
        "Cartoon scalar mean",
        scalar_mean,
    )

    # --------------------------------------------------------
    # 14. Grouped mean
    # --------------------------------------------------------

    def grouped_mean():

        response = run_query(
            session_id,
            "average viewing time by favorite cartoon",
        )

        expected = (
            df.groupby(
                "Favorite Cartoon"
            )[
                "Viewing Time (hours)"
            ]
            .mean()
            .sort_values(
                ascending=False
            )
        )

        assert_grouped_values(
            response,
            expected,
        )

    runner.run(
        "Cartoon grouped mean",
        grouped_mean,
    )

    # --------------------------------------------------------
    # 15. Highest average
    # --------------------------------------------------------

    def highest_average():

        response = run_query(
            session_id,
            "which cartoon has the highest average viewing time?",
        )

        expected = (
            df.groupby(
                "Favorite Cartoon"
            )[
                "Viewing Time (hours)"
            ]
            .mean()
            .sort_values(
                ascending=False
            )
            .head(1)
        )

        assert_ranked_values(
            response,
            expected,
        )

    runner.run(
        "Cartoon singular highest ranking",
        highest_average,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print("DataSage V1 — Golden Correctness Tests")
    print(
        "Generated:",
        datetime.now().strftime(
            "%d-%m-%Y %H:%M:%S"
        ),
    )
    print("=" * 80)

    runner = GoldenTestRunner()

    test_flower_dataset(
        runner
    )

    test_hospital_dataset(
        runner
    )

    test_sales_dataset(
        runner
    )

    test_cartoon_dataset(
        runner
    )

    print()
    print("=" * 80)
    print("GOLDEN CORRECTNESS SUMMARY")
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

    if total:

        success_rate = (
            runner.passed
            / total
            * 100
        )

    else:
        success_rate = 0.0

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
            "🟢 V1 ANALYTICAL CORRECTNESS GATE: PASS"
        )

        print(
            "All golden analytical results match "
            "independent Pandas calculations."
        )

    else:

        print()
        print(
            "🔴 V1 ANALYTICAL CORRECTNESS GATE: FAIL"
        )

        print(
            "Review correctness failures before deployment."
        )


if __name__ == "__main__":
    main()