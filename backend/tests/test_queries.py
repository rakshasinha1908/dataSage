import requests
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

# ---------------------------------------------
# IMPORTANT
# Paste your session_id here after uploading
# a dataset once from the frontend.
# ---------------------------------------------
SESSION_ID = "35549f47-fde1-41ee-9388-78c102d67ed8"

print(f"Using Session ID: {SESSION_ID}")

TEST_QUERIES = [

    # =====================================
    # Metadata
    # =====================================
    "describe dataset",
    "dataset summary",
    "show columns",
    "show schema",

    # =====================================
    # Row Retrieval
    # =====================================
    "show rows",
    "show me rows",
    "display rows",
    "list rows",

    "show 10 rows",
    "show 25 rows",
    "show 50 rows",
    "show 100 rows",
    "show 500 rows",

    "show all rows",
    "show every row",
    "show all records",

    # =====================================
    # Ranking
    # =====================================
    "top 10 rows",
    "bottom 10 rows",
    "first 15 rows",
    "last 20 rows",

    "top 10 rows where city is delhi",
    "bottom 10 rows where city is delhi",

    # =====================================
    # Conditions
    # =====================================
    "show rows where city is delhi",
    "show rows where prepaid order is yes",
    "show rows where membership customer is yes",

    "show 10 rows where city is delhi",
    "show all rows where city is delhi",

    # =====================================
    # Aggregations
    # =====================================
    "average transaction amount",
    "sum transaction amount",
    "maximum transaction amount",
    "minimum transaction amount",
    "count customers",

    # =====================================
    # Group By
    # =====================================
    "average transaction amount by category",
    "average transaction amount by city",
    "sum transaction amount by category",
    "count customers by city",

    # =====================================
    # Combined
    # =====================================
    "average transaction amount where city is delhi",
    "count customers where prepaid order is yes",
    "sum transaction amount where membership customer is yes",

    # =====================================
    # Ranking + Group By
    # =====================================
    "top 5 categories by transaction amount",
    "bottom 10 cities by transaction amount",

    # =====================================
    # Invalid Queries
    # =====================================
    "show 0 rows",
    "show 99999 rows",
    "average comments",
    "sum customer full name",
]





def run_query(question):
    return requests.get(
        f"{BASE_URL}/query",
        params={
            "session_id": SESSION_ID,
            "question": question,
        },
    )


def main():

    passed = 0
    failed = 0

    failed_queries = []

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"regression_results_{timestamp}.txt"

    with open(log_file, "w", encoding="utf-8") as log:

        def write(text=""):
            print(text)
            log.write(text + "\n")

        write("=" * 80)
        write("DataSage V2 Regression Report")
        write(f"Generated : {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
        write(f"Session ID: {SESSION_ID}")
        write("=" * 80)
        write()

        for query in TEST_QUERIES:

            try:

                response = run_query(query)

                if response.status_code != 200:
                    failed += 1

                    failed_queries.append(
                        (query, f"HTTP {response.status_code}")
                    )

                    write(f"❌ FAIL | {query}")
                    continue

                data = response.json()

                if data.get("success", False):

                    passed += 1
                    write(f"✅ PASS | {query}")

                else:

                    failed += 1

                    reason = data.get("error", "Unknown Error")

                    failed_queries.append(
                        (query, reason)
                    )

                    write(f"❌ FAIL | {query}")

            except Exception as e:

                failed += 1

                failed_queries.append(
                    (query, str(e))
                )

                write(f"❌ ERROR | {query}")

        write()
        write("=" * 80)
        write("SUMMARY")
        write("=" * 80)
        write(f"Passed : {passed}")
        write(f"Failed : {failed}")

        accuracy = (passed / len(TEST_QUERIES)) * 100

        write(f"Success Rate : {accuracy:.2f}%")
        write("=" * 80)

        if failed_queries:

            write()
            write("FAILED QUERIES")
            write("-" * 80)

            for query, reason in failed_queries:

                write(f"• {query}")
                write(f"  Reason : {reason}")
                write()

    print()
    print("=" * 80)
    print(f"Regression report saved to:")
    print(log_file)
    print("=" * 80)


if __name__ == "__main__":
    main()