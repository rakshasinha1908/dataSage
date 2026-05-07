# from fastapi import FastAPI, File, UploadFile
# from fastapi.middleware.cors import CORSMiddleware
# import pandas as pd
# import io
# import os
# import re
# import requests
# import uuid
# from dotenv import load_dotenv
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib import colors
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


# # ------------------ HELPERS ------------------

# def classify_query(query):
#     q = query.lower()
#     structured_kw = [
#         "top", "bottom", "average", "mean", "trend", "distribution",
#         "compare", "highest", "lowest", "most", "least", "sum", "total",
#         "count", "show", "list", "rank"
#     ]
#     insight_kw = [
#         "explain", "why", "summary", "analysis", "insight", "describe",
#         "tell me", "what is", "what are", "how"
#     ]
#     has_struct  = any(k in q for k in structured_kw)
#     has_insight = any(k in q for k in insight_kw)

#     if has_struct and has_insight:
#         return "hybrid"
#     elif has_struct:
#         return "structured"
#     else:
#         return "ai"


# def find_column(query, columns):
#     """
#     1. Strict  – every word of the column name appears in the query.
#     2. Loose   – at least one meaningful word (len > 2) matches.
#     Returns None when nothing matches.
#     """
#     q = query.lower()
#     for col in columns:
#         words = [w for w in re.split(r'[\s_\-]+', col.lower()) if w]
#         if words and all(w in q for w in words):
#             return col
#     for col in columns:
#         words = re.split(r'[\s_\-]+', col.lower())
#         if any(w in q for w in words if len(w) > 2):
#             return col
#     return None


# def get_label_column(df):
#     for col in df.columns:
#         if df[col].dtype == "object":
#             return col
#     return df.columns[0]


# def extract_n(query, default=5):
#     nums = re.findall(r'\b(\d+)\b', query)
#     return int(nums[0]) if nums else default


# # ------------------ SUGGESTIONS ------------------

# def generate_suggestions(df):
#     suggestions = []
#     numeric_cols     = df.select_dtypes(include="number").columns.tolist()
#     categorical_cols = df.select_dtypes(exclude="number").columns.tolist()

#     for col in numeric_cols[:2]:
#         suggestions.append(f"Top 5 {col}")
#         suggestions.append(f"Average {col}")

#     if len(numeric_cols) >= 2:
#         suggestions.append(f"Compare {numeric_cols[0]} and {numeric_cols[1]}")

#     if categorical_cols:
#         suggestions.append(f"Distribution of {categorical_cols[0]}")

#     suggestions.append("Show trend")
#     suggestions.append("Explain this dataset")
#     return suggestions[:6]


# # ------------------ AI ------------------

# def call_ai(prompt):
#     if not API_KEY:
#         return "AI unavailable: OPENROUTER_API_KEY not configured."
#     try:
#         res = requests.post(
#             "https://openrouter.ai/api/v1/chat/completions",
#             headers={
#                 "Authorization": f"Bearer {API_KEY}",
#                 "Content-Type": "application/json"
#             },
#             json={
#                 "model": "openrouter/auto",
#                 "messages": [{"role": "user", "content": prompt}]
#             },
#             timeout=20
#         )
#         data = res.json()
#         return data.get("choices", [{}])[0].get("message", {}).get("content", "No response.")
#     except Exception as e:
#         return f"AI unavailable: {e}"


# def answer_with_ai(query, df):
#     sample = df.head(20).to_dict(orient="records")
#     prompt = (
#         "You are a data analyst. Answer the following question using ONLY the dataset provided. "
#         "Be concise and specific. If the data does not contain an answer, say so.\n\n"
#         f"Question: {query}\n"
#         f"Columns: {df.columns.tolist()}\n"
#         f"Sample data (up to 20 rows): {sample}"
#     )
#     return call_ai(prompt)


# def generate_ai_insight(query, result_df):
#     sample = result_df.head(10).to_dict(orient="records")
#     prompt = (
#         "You are a data analyst. Provide 2-3 short, specific, actionable insights about "
#         "the query result below. Put each insight on its own line starting with a dash (-).\n\n"
#         f"Query: {query}\n"
#         f"Result: {sample}"
#     )
#     return call_ai(prompt)


# # ------------------ UPLOAD ------------------

# @app.post("/api/upload")
# async def upload(file: UploadFile = File(...)):
#     global df
#     contents = await file.read()
#     try:
#         if file.filename.endswith(".csv"):
#             df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
#         else:
#             df = pd.read_excel(io.BytesIO(contents))
#     except Exception as e:
#         return {"error": f"Failed to parse file: {e}"}

#     return {
#         "columns": df.columns.tolist(),
#         "rows": len(df),
#         "suggestions": generate_suggestions(df)
#     }


# # ------------------ QUERY ------------------

# @app.post("/api/query")
# async def query_endpoint(payload: dict):
#     global df

#     if df is None:
#         return {"error": "No dataset uploaded. Please upload a CSV or Excel file first."}

#     q = payload.get("query", "").strip()
#     if not q:
#         return {"error": "Empty query."}

#     intent  = classify_query(q)
#     q_lower = q.lower()

#     numeric_cols     = df.select_dtypes(include="number").columns.tolist()
#     categorical_cols = df.select_dtypes(exclude="number").columns.tolist()

#     # Best-match column: prefer numeric cols, then any column
#     col       = (find_column(q, numeric_cols) or find_column(q, df.columns.tolist())
#                  or (numeric_cols[0] if numeric_cols else df.columns[0]))
#     label_col = get_label_column(df)

#     try:

#         # ── PURE AI ──
#         if intent == "ai":
#             return {"type": "ai", "title": "AI Analysis",
#                     "insight": answer_with_ai(q, df)}

#         # ── AVERAGE / MEAN ──
#         if any(k in q_lower for k in ["average", "mean"]):
#             tc = find_column(q, numeric_cols) or (numeric_cols[0] if numeric_cols else None)
#             if tc is None:
#                 return {"type": "ai", "title": "No numeric column",
#                         "insight": "No numeric column found to average."}
#             avg = round(df[tc].mean(), 2)
#             return {
#                 "type": "structured",
#                 "title": f"Average — {tc}",
#                 "table": [{tc: avg}],
#                 "insight": f"The average of '{tc}' is {avg:,.2f}."
#             }

#         # ── SUM / TOTAL ──
#         if any(k in q_lower for k in ["sum", "total"]):
#             tc = find_column(q, numeric_cols) or (numeric_cols[0] if numeric_cols else None)
#             if tc is None:
#                 return {"type": "ai", "title": "No numeric column",
#                         "insight": "No numeric column found to sum."}
#             total = df[tc].sum()
#             return {
#                 "type": "structured",
#                 "title": f"Total — {tc}",
#                 "table": [{tc: round(total, 2)}],
#                 "insight": f"The total of '{tc}' is {total:,.2f}."
#             }

#         # ── DISTRIBUTION ──
#         if "distribution" in q_lower:
#             dc = (find_column(q, categorical_cols)
#                   or (categorical_cols[0] if categorical_cols else df.columns[0]))
#             result = df[dc].value_counts().reset_index()
#             result.columns = [dc, "count"]
#             insight = generate_ai_insight(q, result) if intent == "hybrid" else None
#             resp = {
#                 "type": "structured",
#                 "title": f"Distribution — {dc}",
#                 "table": result.to_dict(orient="records"),
#                 "chart": {
#                     "type": "bar",
#                     "labels": result[dc].astype(str).tolist(),
#                     "values": result["count"].tolist(),
#                     "x_label": dc,
#                     "y_label": "count"
#                 }
#             }
#             if insight:
#                 resp["insight"] = insight
#             return resp

#         # ── COMPARE ──
#         if "compare" in q_lower:
#             matched = [c for c in numeric_cols
#                        if any(w in q_lower
#                               for w in re.split(r'[\s_\-]+', c.lower()) if len(w) > 2)]
#             target_cols = matched[:3] if matched else numeric_cols[:3]
#             if not target_cols:
#                 return {"type": "ai", "title": "Compare",
#                         "insight": answer_with_ai(q, df)}
#             result = df[target_cols].describe().T.reset_index()
#             result.columns = ["metric"] + list(result.columns[1:])
#             insight = generate_ai_insight(q, result) if intent == "hybrid" else None
#             resp = {
#                 "type": "structured",
#                 "title": f"Comparison — {', '.join(target_cols)}",
#                 "table": result.to_dict(orient="records")
#             }
#             if insight:
#                 resp["insight"] = insight
#             return resp

#         # ── TREND ──
#         if any(k in q_lower for k in ["trend", "over time", "time series"]):
#             date_col = next(
#                 (c for c in df.columns
#                  if any(k in c.lower() for k in ["date","time","month","year","week","day"])),
#                 None
#             )
#             tc = find_column(q, numeric_cols) or (numeric_cols[0] if numeric_cols else None)
#             if tc is None:
#                 return {"type": "ai", "title": "No numeric column",
#                         "insight": "No numeric column found to plot trend."}

#             if date_col:
#                 result = df[[date_col, tc]].dropna().sort_values(by=date_col)
#                 x_labels = result[date_col].astype(str).tolist()
#             else:
#                 result = df[[tc]].dropna().reset_index()
#                 x_labels = result["index"].astype(str).tolist()

#             insight = generate_ai_insight(q, result) if intent == "hybrid" else None
#             resp = {
#                 "type": "structured",
#                 "title": f"Trend — {tc}",
#                 "table": result.head(10).to_dict(orient="records"),
#                 "chart": {
#                     "type": "line",
#                     "labels": x_labels,
#                     "values": result[tc].tolist(),
#                     "x_label": date_col or "Index",
#                     "y_label": tc
#                 }
#             }
#             if insight:
#                 resp["insight"] = insight
#             return resp

#         # ── TOP / HIGHEST / MOST ──
#         if any(k in q_lower for k in ["top", "highest", "most"]):
#             n      = extract_n(q)
#             result = df.sort_values(by=col, ascending=False).head(n)
#             labels = (result[label_col].astype(str).tolist()
#                       if label_col in result.columns else result.index.astype(str).tolist())
#             values = result[col].tolist() if col in result.columns else []
#             insight = generate_ai_insight(q, result) if intent == "hybrid" else None
#             resp = {
#                 "type": "structured",
#                 "title": q.capitalize(),
#                 "table": result.to_dict(orient="records"),
#                 "chart": {"type": "bar", "labels": labels, "values": values,
#                           "x_label": label_col, "y_label": col}
#             }
#             if insight:
#                 resp["insight"] = insight
#             return resp

#         # ── BOTTOM / LOWEST / LEAST ──
#         if any(k in q_lower for k in ["bottom", "lowest", "least"]):
#             n      = extract_n(q)
#             result = df.sort_values(by=col, ascending=True).head(n)
#             labels = (result[label_col].astype(str).tolist()
#                       if label_col in result.columns else result.index.astype(str).tolist())
#             values = result[col].tolist() if col in result.columns else []
#             insight = generate_ai_insight(q, result) if intent == "hybrid" else None
#             resp = {
#                 "type": "structured",
#                 "title": q.capitalize(),
#                 "table": result.to_dict(orient="records"),
#                 "chart": {"type": "bar", "labels": labels, "values": values,
#                           "x_label": label_col, "y_label": col}
#             }
#             if insight:
#                 resp["insight"] = insight
#             return resp

#         # ── COUNT ──
#         if "count" in q_lower:
#             if categorical_cols:
#                 cc     = find_column(q, categorical_cols) or categorical_cols[0]
#                 result = df[cc].value_counts().reset_index()
#                 result.columns = [cc, "count"]
#                 return {
#                     "type": "structured",
#                     "title": f"Count — {cc}",
#                     "table": result.to_dict(orient="records"),
#                     "chart": {"type": "bar",
#                               "labels": result[cc].astype(str).tolist(),
#                               "values": result["count"].tolist(),
#                               "x_label": cc, "y_label": "count"}
#                 }
#             return {
#                 "type": "structured",
#                 "title": "Row Count",
#                 "table": [{"total_rows": len(df)}],
#                 "insight": f"The dataset contains {len(df):,} rows."
#             }

#         # ── GENERIC FALLBACK ──
#         cols_to_show = ([label_col, col] if label_col != col and label_col in df.columns
#                         else [col])
#         result = df[cols_to_show].dropna().head(10)
#         labels = (result[label_col].astype(str).tolist()
#                   if label_col in result.columns else result.index.astype(str).tolist())
#         values = result[col].tolist() if col in result.columns else []
#         insight = generate_ai_insight(q, result) if intent == "hybrid" else None
#         resp = {
#             "type": "structured",
#             "title": q.capitalize(),
#             "table": result.to_dict(orient="records")
#         }
#         if values:
#             resp["chart"] = {"type": "bar", "labels": labels, "values": values,
#                              "x_label": label_col, "y_label": col}
#         if insight:
#             resp["insight"] = insight
#         return resp

#     except Exception as e:
#         return {"error": str(e)}


# # ------------------ EXPORT ------------------

# @app.post("/api/export")
# async def export(payload: dict):
#     chats     = payload.get("chatHistory", [])
#     file_path = f"report_{uuid.uuid4().hex}.pdf"

#     doc      = SimpleDocTemplate(file_path)
#     styles   = getSampleStyleSheet()
#     elements = []

#     elements.append(Paragraph("DataSage Report", styles["Title"]))
#     elements.append(Spacer(1, 20))

#     for i, chat in enumerate(chats):
#         elements.append(Paragraph(f"Q{i+1}: {chat['query']}", styles["Heading2"]))
#         elements.append(Spacer(1, 6))

#         res = chat.get("response", {})

#         if res.get("insight"):
#             clean = res["insight"].replace("**", "")
#             elements.append(Paragraph(clean, styles["Normal"]))
#             elements.append(Spacer(1, 8))

#         table_data = res.get("table", [])
#         if table_data:
#             headers = list(table_data[0].keys())
#             rows    = [headers] + [
#                 [str(row.get(h, "")) for h in headers] for row in table_data
#             ]
#             t = Table(rows, repeatRows=1)
#             t.setStyle(TableStyle([
#                 ("BACKGROUND",     (0, 0), (-1, 0), colors.HexColor("#7C3AED")),
#                 ("TEXTCOLOR",      (0, 0), (-1, 0), colors.white),
#                 ("FONTSIZE",       (0, 0), (-1, -1), 9),
#                 ("GRID",           (0, 0), (-1, -1), 0.5, colors.HexColor("#E4E0FA")),
#                 ("ROWBACKGROUNDS", (0, 1), (-1, -1),
#                     [colors.white, colors.HexColor("#F5F4FF")]),
#                 ("PADDING",        (0, 0), (-1, -1), 6),
#             ]))
#             elements.append(t)

#         elements.append(Spacer(1, 24))

#     doc.build(elements)
#     return FileResponse(file_path, filename="DataSage_Report.pdf")


from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import os
import re
import requests
import uuid
import json
from datetime import datetime
from dotenv import load_dotenv
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
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

# ─────────────────── SESSION STORAGE ───────────────────
datasets = {}  # {session_id: df}
dataset_context = {}  # {session_id: summary}
ai_call_count = {}  # {session_id: count}
ai_response_cache = {}  # {prompt_hash: response} — global cache
AI_CALL_LIMIT = 20  # Per session

# ─────────────────── HELPERS ───────────────────


def classify_query(query):
    """
    Classify query intent as 'structured', 'hybrid', or 'ai' based on keywords.
    Returns low-confidence tuple if no strong match.
    """
    q = query.lower()
    structured_kw = [
        "top", "bottom", "average", "mean", "trend", "distribution",
        "compare", "highest", "lowest", "most", "least", "sum", "total",
        "count", "show", "list", "rank"
    ]
    insight_kw = [
        "explain", "why", "summary", "analysis", "insight", "describe",
        "tell me", "what is", "what are", "how"
    ]
    has_struct = any(k in q for k in structured_kw)
    has_insight = any(k in q for k in insight_kw)

    if has_struct and has_insight:
        return "hybrid"
    elif has_struct:
        return "structured"
    else:
        return "ai"


def find_column(query, columns):
    """
    1. Strict – every word of the column name appears in the query.
    2. Loose – at least one meaningful word (len > 2) matches.
    Returns None when nothing matches.
    """
    q = query.lower()
    for col in columns:
        words = [w for w in re.split(r'[\s_\-]+', col.lower()) if w]
        if words and all(w in q for w in words):
            return col
    for col in columns:
        words = re.split(r'[\s_\-]+', col.lower())
        if any(w in q for w in words if len(w) > 2):
            return col
    return None


def get_label_column(df):
    """Return first categorical column, fallback to first column."""
    for col in df.columns:
        if df[col].dtype == "object":
            return col
    return df.columns[0]


def extract_n(query, default=5):
    """Extract count from query (e.g., 'Top 10' → 10)."""
    nums = re.findall(r'\b(\d+)\b', query)
    return int(nums[0]) if nums else default


def is_datetime_column(series):
    """Check if a column is datetime-like (dtype or name heuristic)."""
    # Check dtype first
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    # Check name heuristic
    if any(k in series.name.lower() for k in ["date", "time", "month", "year", "week", "day"]):
        return True
    return False


def hash_prompt(prompt):
    """Simple hash for caching (could be improved with hashlib)."""
    return str(hash(prompt))


# ─────────────────── AI FUNCTIONS ───────────────────


def call_ai(prompt, use_cache=True):
    """
    Call OpenRouter API with optional caching.
    Returns (response_text, is_cached) tuple.
    """
    if not API_KEY:
        return "AI unavailable: OPENROUTER_API_KEY not configured.", False

    prompt_hash = hash_prompt(prompt)
    if use_cache and prompt_hash in ai_response_cache:
        return ai_response_cache[prompt_hash], True

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
            },
            timeout=20
        )
        data = res.json()
        response = data.get("choices", [{}])[0].get("message", {}).get("content", "No response.")
        
        # Cache it
        if use_cache:
            ai_response_cache[prompt_hash] = response
        
        return response, False
    except Exception as e:
        return f"AI unavailable: {e}", False


def parse_query_with_ai(query, columns):
    """
    AI-powered fallback query parser.
    
    Returns: {
        "intent": "structured" | "ai" | None,
        "column": "column_name" | None,
        "n": 5 | None
    }
    
    Or None if parsing fails entirely.
    """
    if not columns:
        return None

    # Build compact prompt
    prompt = (
        f"Parse this data query into structured JSON. Return ONLY valid JSON, no markdown.\n"
        f"Query: {query}\n"
        f"Available columns: {columns}\n"
        f"Response format:\n"
        f'{{"intent": "structured"|"ai"|null, "column": "<column_name>"|null, "n": <number>|null}}\n'
        f"Examples:\n"
        f'"Top 10 revenue" → {{"intent":"structured","column":"revenue","n":10}}\n'
        f'"Why is profit low?" → {{"intent":"ai","column":null,"n":null}}'
    )

    response, _ = call_ai(prompt, use_cache=False)  # Don't cache parser

    try:
        # Extract JSON from response (strip markdown if needed)
        clean = response.strip()
        if "```" in clean:
            clean = clean.split("```")[1].strip()
            if clean.startswith("json"):
                clean = clean[4:].strip()
        
        parsed = json.loads(clean)
        
        # Validate structure
        if isinstance(parsed, dict) and all(k in ["intent", "column", "n"] for k in parsed.keys()):
            return parsed
    except (json.JSONDecodeError, ValueError, IndexError):
        pass

    return None


def answer_with_ai(query, df):
    """Answer query with AI using dataset sample."""
    sample = df.head(20).to_dict(orient="records")
    prompt = (
        "You are a data analyst. Answer the following question using ONLY the dataset provided. "
        "Be concise and specific. If the data does not contain an answer, say so.\n\n"
        f"Question: {query}\n"
        f"Columns: {df.columns.tolist()}\n"
        f"Sample data (up to 20 rows): {sample}"
    )
    response, _ = call_ai(prompt)
    return response


def generate_ai_insight(query, result_df):
    """Generate 2-3 short insights from result."""
    sample = result_df.head(10).to_dict(orient="records")
    prompt = (
        "You are a data analyst. Provide 2-3 short, specific, actionable insights about "
        "the query result below. Put each insight on its own line starting with a dash (-).\n\n"
        f"Query: {query}\n"
        f"Result: {sample}"
    )
    response, _ = call_ai(prompt)
    return response


def summarize_dataset(df):
    """
    One-time AI call to summarize the uploaded dataset.
    Sent only column names and 5 sample rows.
    """
    sample = df.head(5).to_dict(orient="records")
    prompt = (
        "Summarize this dataset in 1-2 sentences. Be very concise.\n\n"
        f"Columns: {df.columns.tolist()}\n"
        f"Sample rows (first 5): {sample}"
    )
    response, _ = call_ai(prompt)
    return response


# ─────────────────── SUGGESTIONS ───────────────────


def generate_suggestions(df):
    """Generate 6 query suggestions from dataset structure."""
    suggestions = []
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(exclude="number").columns.tolist()

    for col in numeric_cols[:2]:
        suggestions.append(f"Top 5 {col}")
        suggestions.append(f"Average {col}")

    if len(numeric_cols) >= 2:
        suggestions.append(f"Compare {numeric_cols[0]} and {numeric_cols[1]}")

    if categorical_cols:
        suggestions.append(f"Distribution of {categorical_cols[0]}")

    suggestions.append("Show trend")
    suggestions.append("Explain this dataset")
    return suggestions[:6]


# ─────────────────── UPLOAD ───────────────────


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    """
    Upload CSV/Excel file.
    - Generate session_id
    - Call AI once to summarize dataset
    - Return session_id, columns, rows, suggestions, and summary
    """
    session_id = str(uuid.uuid4())
    contents = await file.read()
    
    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        return {"error": f"Failed to parse file: {e}"}

    # Store dataset
    datasets[session_id] = df
    ai_call_count[session_id] = 0

    # Get one-time AI summary
    summary = summarize_dataset(df)
    dataset_context[session_id] = summary
    ai_call_count[session_id] += 1

    return {
        "session_id": session_id,
        "columns": df.columns.tolist(),
        "rows": len(df),
        "suggestions": generate_suggestions(df),
        "summary": summary
    }


# ─────────────────── QUERY ───────────────────


@app.post("/api/query")
async def query_endpoint(payload: dict):
    """
    Main query endpoint.
    
    Flow:
    1. Fetch dataframe from session
    2. Classify query (rule-based first)
    3. If LOW CONFIDENCE → call AI parser as fallback
    4. Execute structured logic
    5. Return response with optional AI insights
    """
    session_id = payload.get("session_id")
    if not session_id or session_id not in datasets:
        return {"error": "Invalid or missing session_id. Please re-upload your dataset."}

    df = datasets[session_id]
    q = payload.get("query", "").strip()
    if not q:
        return {"error": "Empty query."}

    # Check AI call limit
    if ai_call_count.get(session_id, 0) >= AI_CALL_LIMIT:
        return {
            "error": f"AI call limit ({AI_CALL_LIMIT}) reached for this session. "
                     "Please start a new session or use structured queries."
        }

    # ── RULE-BASED CLASSIFICATION ──
    intent = classify_query(q)
    q_lower = q.lower()

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(exclude="number").columns.tolist()

    # Find best column match
    col = (find_column(q, numeric_cols) or find_column(q, df.columns.tolist())
           or (numeric_cols[0] if numeric_cols else df.columns[0]))
    label_col = get_label_column(df)

    # ── LOW CONFIDENCE DETECTION ──
    # If no column found OR query doesn't match known keywords → use AI parser
    use_ai_parser = (
        col is None or 
        (intent == "ai" and not any(k in q_lower for k in [
            "average", "mean", "sum", "total", "count", "top", "bottom",
            "highest", "lowest", "trend", "distribution", "compare"
        ]))
    )

    # ── AI PARSER (FALLBACK) ──
    if use_ai_parser:
        parsed = parse_query_with_ai(q, df.columns.tolist())
        if parsed:
            ai_call_count[session_id] += 1
            if parsed.get("intent"):
                intent = parsed["intent"]
            if parsed.get("column"):
                col = parsed["column"]
            if parsed.get("n"):
                n_override = parsed["n"]
            else:
                n_override = None
        else:
            n_override = None
    else:
        n_override = None

    try:

        # ── PURE AI ──
        if intent == "ai":
            ai_call_count[session_id] += 1
            return {
                "type": "ai",
                "title": "AI Analysis",
                "insight": answer_with_ai(q, df)
            }

        # ── AVERAGE / MEAN ──
        if any(k in q_lower for k in ["average", "mean"]):
            tc = find_column(q, numeric_cols) or (numeric_cols[0] if numeric_cols else None)
            if tc is None:
                return {"type": "ai", "title": "No numeric column",
                        "insight": "No numeric column found to average."}
            avg = round(df[tc].mean(), 2)
            return {
                "type": "structured",
                "title": f"Average — {tc}",
                "table": [{tc: avg}],
                "insight": f"The average of '{tc}' is {avg:,.2f}."
            }

        # ── SUM / TOTAL ──
        if any(k in q_lower for k in ["sum", "total"]):
            tc = find_column(q, numeric_cols) or (numeric_cols[0] if numeric_cols else None)
            if tc is None:
                return {"type": "ai", "title": "No numeric column",
                        "insight": "No numeric column found to sum."}
            total = df[tc].sum()
            return {
                "type": "structured",
                "title": f"Total — {tc}",
                "table": [{tc: round(total, 2)}],
                "insight": f"The total of '{tc}' is {total:,.2f}."
            }

        # ── DISTRIBUTION ──
        if "distribution" in q_lower:
            dc = (find_column(q, categorical_cols)
                  or (categorical_cols[0] if categorical_cols else df.columns[0]))
            result = df[dc].value_counts().reset_index()
            result.columns = [dc, "count"]
            
            insight = None
            if intent == "hybrid":
                ai_call_count[session_id] += 1
                insight = generate_ai_insight(q, result)
            
            resp = {
                "type": "structured",
                "title": f"Distribution — {dc}",
                "table": result.to_dict(orient="records"),
                "chart": {
                    "type": "bar",
                    "labels": result[dc].astype(str).tolist()[:10],
                    "values": result["count"].tolist()[:10],
                    "x_label": dc,
                    "y_label": "count"
                }
            }
            if insight:
                resp["insight"] = insight
            return resp

        # ── COMPARE ──
        if "compare" in q_lower:
            matched = [c for c in numeric_cols
                       if any(w in q_lower
                              for w in re.split(r'[\s_\-]+', c.lower()) if len(w) > 2)]
            target_cols = matched[:3] if matched else numeric_cols[:3]
            if not target_cols:
                ai_call_count[session_id] += 1
                return {"type": "ai", "title": "Compare",
                        "insight": answer_with_ai(q, df)}
            
            result = df[target_cols].describe().T.reset_index()
            result.columns = ["metric"] + list(result.columns[1:])
            
            insight = None
            if intent == "hybrid":
                ai_call_count[session_id] += 1
                insight = generate_ai_insight(q, result)
            
            resp = {
                "type": "structured",
                "title": f"Comparison — {', '.join(target_cols)}",
                "table": result.to_dict(orient="records")
            }
            if insight:
                resp["insight"] = insight
            return resp

        # ── TREND ──
        if any(k in q_lower for k in ["trend", "over time", "time series"]):
            # Find datetime column
            date_col = None
            for col_name in df.columns:
                if is_datetime_column(df[col_name]):
                    date_col = col_name
                    break
            
            tc = find_column(q, numeric_cols) or (numeric_cols[0] if numeric_cols else None)
            if tc is None:
                return {"type": "ai", "title": "No numeric column",
                        "insight": "No numeric column found to plot trend."}

            if date_col:
                result = df[[date_col, tc]].dropna().sort_values(by=date_col)
                x_labels = result[date_col].astype(str).tolist()
            else:
                result = df[[tc]].dropna().reset_index()
                x_labels = result["index"].astype(str).tolist()

            insight = None
            if intent == "hybrid":
                ai_call_count[session_id] += 1
                insight = generate_ai_insight(q, result)
            
            # Limit chart data to top 10
            chart_limit = min(10, len(result))
            
            resp = {
                "type": "structured",
                "title": f"Trend — {tc}",
                "table": result.head(10).to_dict(orient="records"),
                "chart": {
                    "type": "line",
                    "labels": x_labels[:chart_limit],
                    "values": result[tc].tolist()[:chart_limit],
                    "x_label": date_col or "Index",
                    "y_label": tc
                }
            }
            if insight:
                resp["insight"] = insight
            return resp

        # ── TOP / HIGHEST / MOST ──
        if any(k in q_lower for k in ["top", "highest", "most"]):
            n = n_override or extract_n(q)
            result = df.sort_values(by=col, ascending=False).head(n)
            labels = (result[label_col].astype(str).tolist()
                      if label_col in result.columns else result.index.astype(str).tolist())
            values = result[col].tolist() if col in result.columns else []
            
            insight = None
            if intent == "hybrid":
                ai_call_count[session_id] += 1
                insight = generate_ai_insight(q, result)
            
            resp = {
                "type": "structured",
                "title": q.capitalize(),
                "table": result.to_dict(orient="records"),
                "chart": {"type": "bar", "labels": labels[:10], "values": values[:10],
                          "x_label": label_col, "y_label": col}
            }
            if insight:
                resp["insight"] = insight
            return resp

        # ── BOTTOM / LOWEST / LEAST ──
        if any(k in q_lower for k in ["bottom", "lowest", "least"]):
            n = n_override or extract_n(q)
            result = df.sort_values(by=col, ascending=True).head(n)
            labels = (result[label_col].astype(str).tolist()
                      if label_col in result.columns else result.index.astype(str).tolist())
            values = result[col].tolist() if col in result.columns else []
            
            insight = None
            if intent == "hybrid":
                ai_call_count[session_id] += 1
                insight = generate_ai_insight(q, result)
            
            resp = {
                "type": "structured",
                "title": q.capitalize(),
                "table": result.to_dict(orient="records"),
                "chart": {"type": "bar", "labels": labels[:10], "values": values[:10],
                          "x_label": label_col, "y_label": col}
            }
            if insight:
                resp["insight"] = insight
            return resp

        # ── COUNT ──
        if "count" in q_lower:
            if categorical_cols:
                cc = find_column(q, categorical_cols) or categorical_cols[0]
                result = df[cc].value_counts().reset_index()
                result.columns = [cc, "count"]
                return {
                    "type": "structured",
                    "title": f"Count — {cc}",
                    "table": result.to_dict(orient="records"),
                    "chart": {"type": "bar",
                              "labels": result[cc].astype(str).tolist()[:10],
                              "values": result["count"].tolist()[:10],
                              "x_label": cc, "y_label": "count"}
                }
            return {
                "type": "structured",
                "title": "Row Count",
                "table": [{"total_rows": len(df)}],
                "insight": f"The dataset contains {len(df):,} rows."
            }

        # ── GENERIC FALLBACK ──
        cols_to_show = ([label_col, col] if label_col != col and label_col in df.columns
                        else [col])
        result = df[cols_to_show].dropna().head(10)
        labels = (result[label_col].astype(str).tolist()
                  if label_col in result.columns else result.index.astype(str).tolist())
        values = result[col].tolist() if col in result.columns else []
        
        insight = None
        if intent == "hybrid":
            ai_call_count[session_id] += 1
            insight = generate_ai_insight(q, result)
        
        resp = {
            "type": "structured",
            "title": q.capitalize(),
            "table": result.to_dict(orient="records")
        }
        if values:
            resp["chart"] = {"type": "bar", "labels": labels[:10], "values": values[:10],
                             "x_label": label_col, "y_label": col}
        if insight:
            resp["insight"] = insight
        return resp

    except Exception as e:
        return {"error": str(e)}


# ─────────────────── EXPORT ───────────────────


@app.post("/api/export")
async def export(payload: dict):
    """Export chat history as PDF report."""
    chats = payload.get("chatHistory", [])
    file_path = f"report_{uuid.uuid4().hex}.pdf"

    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("DataSage Report", styles["Title"]))
    elements.append(Spacer(1, 20))

    for i, chat in enumerate(chats):
        elements.append(Paragraph(f"Q{i+1}: {chat['query']}", styles["Heading2"]))
        elements.append(Spacer(1, 6))

        res = chat.get("response", {})

        if res.get("insight"):
            clean = res["insight"].replace("**", "")
            elements.append(Paragraph(clean, styles["Normal"]))
            elements.append(Spacer(1, 8))

        table_data = res.get("table", [])
        if table_data:
            headers = list(table_data[0].keys())
            rows = [headers] + [
                [str(row.get(h, "")) for h in headers] for row in table_data
            ]
            t = Table(rows, repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7C3AED")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E4E0FA")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                    [colors.white, colors.HexColor("#F5F4FF")]),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]))
            elements.append(t)

        elements.append(Spacer(1, 24))

    doc.build(elements)
    return FileResponse(file_path, filename="DataSage_Report.pdf")