import requests
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

# ---------------------------------------------
# IMPORTANT
# Paste your session_id here after uploading
# a dataset once from the frontend.
# ---------------------------------------------
SESSION_ID = "2153de99-a5eb-4796-8a76-4acbc9eb4f19"

print(f"Using Session ID: {SESSION_ID}")

# hospital dataset
TEST_QUERIES = [

    # Metadata
    "describe dataset",
    "dataset summary",
    "show columns",
    "show schema",

    # Row Retrieval
    "show rows",
    "show 10 rows",
    "show all rows",
    "top 10 rows",
    "bottom 10 rows",
    "first 15 rows",
    "last 20 rows",

    # Conditions
    "show rows where gender is female",
    "show rows where readmission is no",
    "show rows where outcome is recovered",

    "show 10 rows where condition is heart disease",

    # Aggregations
    "average cost",
    "sum cost",
    "maximum cost",
    "minimum cost",
    "average age",
    "average length of stay",
    "count patients",

    # Group By
    "average cost by condition",
    "average cost by procedure",
    "average length of stay by condition",
    "count patients by gender",
    "count patients by outcome",

    # Combined
    "average cost where gender is female",
    "count patients where readmission is no",
    "average length of stay where outcome is recovered",

    # Ranking
    "top 5 conditions by cost",
    "bottom 5 procedures by cost",

    # Invalid
    "average procedure",
    "sum patient id",
]

# flower dataset
# TEST_QUERIES = [

#     # Metadata
#     "describe dataset",
#     "dataset summary",
#     "show columns",
#     "show schema",

#     # Row Retrieval
#     "show rows",
#     "show 10 rows",
#     "show all rows",
#     "top 10 rows",
#     "bottom 10 rows",
#     "first 15 rows",
#     "last 20 rows",

#     # Conditions
#     "show rows where species is rose",
#     "show rows where fragrance is mild",

#     "show 10 rows where species is rose",

#     # Aggregations
#     "average height",
#     "sum height",
#     "maximum height",
#     "minimum height",
#     "count flowers",

#     # Group By
#     "average height by species",
#     "average height by fragrance",
#     "count flowers by species",
#     "count flowers by fragrance",

#     # Combined
#     "average height where species is rose",
#     "count flowers where fragrance is mild",

#     # Ranking
#     "top 5 species by height",
#     "bottom 5 fragrances by height",

#     # Invalid
#     "average fragrance",
#     "sum species",
# ]

# sales dataset
# TEST_QUERIES = [

#     # =====================================
#     # Metadata
#     # =====================================
#     "describe dataset",
#     "dataset summary",
#     "show columns",
#     "show schema",

#     # =====================================
#     # Row Retrieval
#     # =====================================
#     "show rows",
#     "show me rows",
#     "display rows",
#     "list rows",

#     "show 10 rows",
#     "show 25 rows",
#     "show 50 rows",
#     "show 100 rows",
#     "show 500 rows",

#     "show all rows",
#     "show every row",
#     "show all records",

#     # =====================================
#     # Ranking
#     # =====================================
#     "top 10 rows",
#     "bottom 10 rows",
#     "first 15 rows",
#     "last 20 rows",

#     "top 10 rows where city is delhi",
#     "bottom 10 rows where city is delhi",

#     # =====================================
#     # Conditions
#     # =====================================
#     "show rows where city is delhi",
#     "show rows where prepaid order is yes",
#     "show rows where membership customer is yes",

#     "show 10 rows where city is delhi",
#     "show all rows where city is delhi",

#     # =====================================
#     # Aggregations
#     # =====================================
#     "average transaction amount",
#     "sum transaction amount",
#     "maximum transaction amount",
#     "minimum transaction amount",
#     "count customers",

#     # =====================================
#     # Group By
#     # =====================================
#     "average transaction amount by category",
#     "average transaction amount by city",
#     "sum transaction amount by category",
#     "count customers by city",

#     # =====================================
#     # Combined
#     # =====================================
#     "average transaction amount where city is delhi",
#     "count customers where prepaid order is yes",
#     "sum transaction amount where membership customer is yes",

#     # =====================================
#     # Ranking + Group By
#     # =====================================
#     "top 5 categories by transaction amount",
#     "bottom 10 cities by transaction amount",

#     # =====================================
#     # Invalid Queries
#     # =====================================
#     "show 0 rows",
#     "show 99999 rows",
#     "average comments",
#     "sum customer full name",
# ]

# cartoon dataset
# TEST_QUERIES = [

#     # =====================================
#     # Metadata
#     # =====================================
#     "describe dataset",
#     "dataset summary",
#     "show columns",
#     "show schema",

#     # =====================================
#     # Row Retrieval
#     # =====================================
#     "show rows",
#     "show 10 rows",
#     "show all rows",
#     "top 10 rows",
#     "bottom 10 rows",
#     "first 15 rows",
#     "last 20 rows",

#     # =====================================
#     # Conditions
#     # =====================================
#     "show rows where city is hyderabad",
#     "show rows where subscription status is yes",

#     "show 10 rows where city is hyderabad",
#     "show all rows where subscription status is yes",

#     # =====================================
#     # Aggregations
#     # =====================================
#     "average viewing time",
#     "sum viewing time",
#     "maximum viewing time",
#     "minimum viewing time",
#     "count viewers",

#     # =====================================
#     # Group By
#     # =====================================
#     "average viewing time by city",
#     "average viewing time by favorite cartoon",
#     "count viewers by city",
#     "count viewers by favorite cartoon",

#     # =====================================
#     # Combined
#     # =====================================
#     "average viewing time where city is hyderabad",
#     "count viewers where subscription status is yes",

#     # =====================================
#     # Ranking
#     # =====================================
#     "top 5 cities by viewing time",
#     "bottom 5 favorite cartoons by viewing time",

#     # =====================================
#     # Invalid
#     # =====================================
#     "average viewer name",
#     "sum favorite cartoon",
# ]




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