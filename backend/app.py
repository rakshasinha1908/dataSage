# from fastapi import FastAPI, File, UploadFile
# from fastapi.middleware.cors import CORSMiddleware
# import pandas as pd
# import io
# import os
# import requests
# import uuid
# from dotenv import load_dotenv
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet
# from fastapi.responses import FileResponse

# # ------------------ ENV ------------------
# load_dotenv()
# API_KEY = os.getenv("OPENROUTER_API_KEY")

# # ------------------ APP ------------------
# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# df = None

# # ------------------ ROOT ------------------
# @app.get("/")
# def home():
#     return {"message": "DataSage API is running"}


# # ------------------ UPLOAD ------------------
# @app.post("/api/upload")
# async def upload_file(file: UploadFile = File(...)):
#     global df

#     try:
#         contents = await file.read()

#         if file.filename.endswith(".csv"):
#             df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
#         elif file.filename.endswith(".xlsx"):
#             df = pd.read_excel(io.BytesIO(contents))
#         else:
#             return {"error": "Unsupported file format"}

#         numeric_cols = df.select_dtypes(include="number").columns.tolist()

#         return {
#             "message": "File uploaded successfully",
#             "columns": df.columns.tolist(),
#             "rows": len(df),
#             "dtypes": df.dtypes.astype(str).to_dict(),
#             "missing_values": df.isnull().sum().to_dict(),
#             "suggestions": [
#                 f"Top 5 {numeric_cols[0]}" if numeric_cols else "Top 5 values",
#                 f"Average {numeric_cols[0]}" if numeric_cols else "Average values",
#                 "Show trend",
#                 "Explain this dataset"
#             ]
#         }

#     except Exception as e:
#         return {"error": str(e)}


# # ------------------ HELPERS ------------------

# def classify_query(query):
#     query = query.lower()

#     structured_keywords = ["top", "bottom", "average", "mean", "trend"]
#     insight_keywords = ["insight", "summary", "explain", "analysis", "why", "pattern"]

#     has_structure = any(k in query for k in structured_keywords)
#     wants_insight = any(k in query for k in insight_keywords)

#     if has_structure and wants_insight:
#         return "hybrid"
#     elif has_structure:
#         return "structured"
#     else:
#         return "ai"


# def find_column_from_query(query, columns):
#     query = query.lower()

#     for col in columns:
#         col_clean = col.lower().replace("_", " ")
#         words = col_clean.split()

#         if all(word in query for word in words):
#             return col

#     return None


# def get_label_column(df):
#     preferred = ["name", "category", "building"]

#     for col in df.columns:
#         if any(p in col.lower() for p in preferred):
#             return col

#     non_numeric = df.select_dtypes(exclude="number").columns
#     return non_numeric[0] if len(non_numeric) > 0 else None


# def generate_basic_insight(df, col):
#     try:
#         max_val = df[col].max()
#         min_val = df[col].min()
#         avg_val = df[col].mean()

#         return (
#             f"{col} ranges from {min_val} to {max_val}, "
#             f"with an average of {round(avg_val, 2)}."
#         )
#     except:
#         return "Basic insight unavailable"


# def generate_ai_insight(query, df, result_df, target_col):
#     try:
#         sample = result_df.head(10).to_dict(orient="records")

#         prompt = f"""
# You are a data analyst.

# Query: {query}
# Column: {target_col}
# Data: {sample}

# Give short actionable insights.
# """

#         response = requests.post(
#             "https://openrouter.ai/api/v1/chat/completions",
#             headers={
#                 "Authorization": f"Bearer {API_KEY}",
#                 "Content-Type": "application/json"
#             },
#             json={
#                 "model": "openrouter/auto",
#                 "messages": [{"role": "user", "content": prompt}]
#             }
#         )

#         result = response.json()

#         return result.get("choices", [{}])[0].get("message", {}).get("content", "AI insight unavailable")

#     except:
#         return "AI insight unavailable"


# def answer_with_ai(query, df):
#     try:
#         sample = df.head(20).to_dict(orient="records")
#         columns = df.columns.tolist()

#         prompt = f"""
# You are a data analyst.

# User question: {query}

# Columns: {columns}

# Sample data:
# {sample}

# Answer ONLY based on dataset.
# If not possible, say so clearly.
# """

#         response = requests.post(
#             "https://openrouter.ai/api/v1/chat/completions",
#             headers={
#                 "Authorization": f"Bearer {API_KEY}",
#                 "Content-Type": "application/json"
#             },
#             json={
#                 "model": "openrouter/auto",
#                 "messages": [{"role": "user", "content": prompt}]
#             }
#         )

#         result = response.json()

#         return result.get("choices", [{}])[0].get("message", {}).get("content", "No answer")

#     except:
#         return "AI could not answer"


# # ------------------ QUERY ------------------

# @app.post("/api/query")
# async def query_data(payload: dict):
#     global df

#     query = payload.get("query", "").lower()

#     if df is None:
#         return {"error": "No dataset uploaded"}

#     try:
#         intent = classify_query(query)

#         columns = df.columns.tolist()
#         numeric_cols = df.select_dtypes(include="number").columns.tolist()

#         target_col = find_column_from_query(query, columns)

#         if not target_col and numeric_cols:
#             target_col = numeric_cols[0]

#         label_col = get_label_column(df)

#         # ------------------ STRUCTURED ------------------
#         if intent in ["structured", "hybrid"]:

#             if "top" in query:
#                 n = next((int(w) for w in query.split() if w.isdigit()), 5)
#                 result = df.sort_values(by=target_col, ascending=False).head(n)

#             elif "bottom" in query:
#                 n = next((int(w) for w in query.split() if w.isdigit()), 5)
#                 result = df.sort_values(by=target_col, ascending=True).head(n)

#             elif "average" in query or "mean" in query:
#                 avg = df[target_col].mean()
#                 result = pd.DataFrame([{target_col: round(avg, 2)}])

#             elif "trend" in query:
#                 date_col = next((c for c in df.columns if "date" in c.lower()), None)

#                 if not date_col:
#                     return {"error": "No date column found"}

#                 result = df.sort_values(by=date_col)

#                 return {
#                     "type": "structured",
#                     "title": f"Trend of {target_col}",
#                     "description": "Time series trend",
#                     "insight": generate_ai_insight(query, df, result, target_col) if intent == "hybrid" else None,
#                     "table": result.head(10).to_dict(orient="records"),
#                     "chart": {
#                         "type": "line",
#                         "labels": result[date_col].astype(str).tolist(),
#                         "values": result[target_col].tolist()
#                     }
#                 }

#             labels = result[label_col].astype(str).tolist() if label_col and target_col in result else result.index.astype(str).tolist()
#             values = result[target_col].tolist() if target_col in result else []

#             return {
#                 "type": "structured",
#                 "title": f"{target_col} Analysis",
#                 "description": f"Result for {query}",
#                 "insight": generate_ai_insight(query, df, result, target_col) if intent == "hybrid" else None,
#                 "table": result.to_dict(orient="records"),
#                 "chart": {
#                     "type": "bar",
#                     "labels": labels,
#                     "values": values
#                 } if values else None
#             }

#         # ------------------ AI ONLY ------------------
#         else:
#             answer = answer_with_ai(query, df)

#             # ❗ FIX 1: fallback if empty
#             if not answer or len(answer.strip()) < 10:
#                 return {
#                     "type": "ai",
#                     "title": "AI Analysis",
#                     "insight": "Sorry, I couldn't confidently answer that based on the dataset."
#                 }

#             # ❗ FIX 2: NO TABLE / NO CHART
#             return {
#                 "type": "ai",
#                 "title": "AI Analysis",
#                 "insight": answer
#             }

#     except Exception as e:
#         return {"error": str(e)}

# # ------------------ EXPORT ------------------

# @app.post("/api/export")
# async def export_report(payload: dict):
#     try:
#         chats = payload.get("chatHistory", [])

#         file_path = f"report_{uuid.uuid4().hex}.pdf"

#         doc = SimpleDocTemplate(file_path)
#         styles = getSampleStyleSheet()
#         elements = []

#         elements.append(Paragraph("DataSage Report", styles["Title"]))
#         elements.append(Spacer(1, 12))

#         for chat in chats:
#             elements.append(Paragraph(f"<b>Query:</b> {chat['query']}", styles["Normal"]))
#             elements.append(Spacer(1, 6))

#             res = chat["response"]

#             if res.get("title"):
#                 elements.append(Paragraph(res["title"], styles["Heading2"]))

#             if res.get("insight"):
#                 elements.append(Paragraph(res["insight"], styles["Normal"]))

#             elements.append(Spacer(1, 12))

#         doc.build(elements)

#         return FileResponse(file_path, filename="DataSage_Report.pdf")

#     except Exception as e:
#         return {"error": str(e)}


from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import os
import requests
import uuid
from dotenv import load_dotenv
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from fastapi.responses import FileResponse

# ------------------ ENV ------------------
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

# ------------------ APP ------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

df = None


# ------------------ HELPERS ------------------

def classify_query(query):
    query = query.lower()

    structured = ["top", "bottom", "average", "mean", "trend"]
    insight = ["explain", "why", "summary", "analysis", "insight"]

    has_struct = any(k in query for k in structured)
    has_insight = any(k in query for k in insight)

    if has_struct and has_insight:
        return "hybrid"
    elif has_struct:
        return "structured"
    else:
        return "ai"


def find_column(query, columns):
    query = query.lower()

    for col in columns:
        words = col.lower().replace("_", " ").split()
        if all(w in query for w in words):
            return col
    return None


def get_label_column(df):
    for col in df.columns:
        if df[col].dtype == "object":
            return col
    return df.columns[0]


# ------------------ 🔥 SMART SUGGESTIONS ------------------

def generate_suggestions(df):
    suggestions = []

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(exclude="number").columns.tolist()

    # --- Top / Average ---
    for col in numeric_cols[:2]:
        suggestions.append(f"Top 5 {col}")
        suggestions.append(f"Average {col}")

    # --- Comparison ---
    if len(numeric_cols) >= 2:
        suggestions.append(f"Compare {numeric_cols[0]} and {numeric_cols[1]}")

    # --- Distribution ---
    if categorical_cols:
        suggestions.append(f"Distribution of {categorical_cols[0]}")

    # --- Trend ---
    suggestions.append("Show trend")

    # --- AI based ---
    suggestions.append("Explain this dataset")

    return suggestions[:6]


# ------------------ AI ------------------

def call_ai(prompt):
    try:
        res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openrouter/auto",
                "messages": [{"role": "user", "content": prompt}]
            }
        )

        data = res.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "No response")

    except:
        return "AI unavailable"


def answer_with_ai(query, df):
    sample = df.head(20).to_dict(orient="records")

    prompt = f"""
Answer based ONLY on dataset.

Question: {query}
Data sample: {sample}
Columns: {df.columns.tolist()}
"""

    return call_ai(prompt)


def generate_ai_insight(query, result_df):
    sample = result_df.head(10).to_dict(orient="records")

    prompt = f"""
Give 2-3 short insights.

Query: {query}
Data: {sample}
"""

    return call_ai(prompt)


# ------------------ UPLOAD ------------------

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    global df

    contents = await file.read()

    if file.filename.endswith(".csv"):
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
    else:
        df = pd.read_excel(io.BytesIO(contents))

    return {
        "columns": df.columns.tolist(),
        "rows": len(df),
        "suggestions": generate_suggestions(df)
    }


# ------------------ QUERY ------------------

@app.post("/api/query")
async def query(payload: dict):
    global df

    if df is None:
        return {"error": "No dataset"}

    q = payload.get("query", "")
    intent = classify_query(q)

    columns = df.columns.tolist()
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    col = find_column(q, columns) or (numeric_cols[0] if numeric_cols else columns[0])
    label_col = get_label_column(df)

    try:

        # ---------------- STRUCTURED ----------------
        if intent in ["structured", "hybrid"]:

            if "top" in q:
                n = 5
                result = df.sort_values(by=col, ascending=False).head(n)

            elif "bottom" in q:
                n = 5
                result = df.sort_values(by=col, ascending=True).head(n)

            elif "average" in q:
                avg = df[col].mean()
                result = pd.DataFrame([{col: round(avg, 2)}])

            elif "trend" in q:

                date_col = next((c for c in df.columns if "date" in c.lower()), None)

                if date_col:
                    result = df.sort_values(by=date_col)
                    labels = result[date_col].astype(str).tolist()
                else:
                    result = df.reset_index()
                    labels = result.index.astype(str).tolist()

                return {
                    "type": "structured",
                    "title": f"Trend of {col}",
                    "table": result.head(10).to_dict(orient="records"),
                    "chart": {
                        "type": "line",
                        "labels": labels,
                        "values": result[col].tolist()
                    }
                }

            labels = result[label_col].astype(str).tolist() if label_col in result else result.index.astype(str).tolist()
            values = result[col].tolist() if col in result else []

            return {
                "type": "structured",
                "title": f"{q}",
                "table": result.to_dict(orient="records"),
                "chart": {
                    "type": "bar",
                    "labels": labels,
                    "values": values
                }
            }

        # ---------------- AI ----------------
        else:
            answer = answer_with_ai(q, df)

            return {
                "type": "ai",
                "title": "AI Analysis",
                "insight": answer
            }

    except Exception as e:
        return {"error": str(e)}


# ------------------ EXPORT ------------------

@app.post("/api/export")
async def export(payload: dict):
    chats = payload.get("chatHistory", [])

    file_path = f"report_{uuid.uuid4().hex}.pdf"

    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("DataSage Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    for chat in chats:
        elements.append(Paragraph(f"<b>Query:</b> {chat['query']}", styles["Normal"]))
        res = chat["response"]

        if res.get("insight"):
            elements.append(Paragraph(res["insight"], styles["Normal"]))

        elements.append(Spacer(1, 12))

    doc.build(elements)

    return FileResponse(file_path, filename="DataSage_Report.pdf")