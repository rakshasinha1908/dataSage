# from fastapi import FastAPI, File, UploadFile
# import pandas as pd
# from fastapi.middleware.cors import CORSMiddleware

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # for development (later restrict)
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# df = None

# @app.get("/")
# def home():
#     return {"message": "DataSage API is running"}

# @app.post("/api/upload")
# async def upload_file(file: UploadFile = File(...)):
#     global df

#     try:
#         if file.filename.endswith(".csv"):
#             df = pd.read_csv(file.file)
#         elif file.filename.endswith(".xlsx"):
#             import io

#             contents = await file.read()
#             df = pd.read_excel(io.BytesIO(contents))
#         else:
#             return {"error": "Unsupported file format"}

#         return {
#             "message": "File uploaded successfully",
#             "columns": df.columns.tolist(),
#             "rows": len(df),
#             "dtypes": df.dtypes.astype(str).to_dict(),
#             "missing_values": df.isnull().sum().to_dict()
#         }

#     except Exception as e:
#         return {"error": str(e)}
    

# def find_column_from_query(query, columns):
#     query = query.lower()

#     for col in columns:
#         col_clean = col.lower().replace("_", " ")
#         if col_clean in query:
#             return col

#     return None

# @app.post("/api/query")
# async def query_data(payload: dict):
#     global df

#     query = payload.get("query", "").lower()

#     if df is None:
#         return {"error": "No dataset uploaded"}

#     try:
#         columns = df.columns.tolist()
#         numeric_cols = df.select_dtypes(include="number").columns.tolist()

#         target_col = find_column_from_query(query, columns)

#         # 👇 fallback if no column found
#         if not target_col and len(numeric_cols) > 0:
#             target_col = numeric_cols[0]

#         # TOP N
#         if "top" in query:
#             n = 5
#             for word in query.split():
#                 if word.isdigit():
#                     n = int(word)

#             result = df.sort_values(by=target_col, ascending=False).head(n)

#             non_numeric_cols = df.select_dtypes(exclude="number").columns

#             if len(non_numeric_cols) > 0:
#                 label_col = non_numeric_cols[0]
#                 labels = result[label_col].astype(str).tolist()
#             else:
#                 labels = result.index.astype(str).tolist()
                
#             values = result[target_col].tolist()

#             return {
#                 "title": f"Top {n} by {target_col}",
#                 "table": result.to_dict(orient="records"),
#                 "chart": {
#                     "type": "bar",
#                     "labels": labels,
#                     "values": values
#                 }
#             }

#         # BOTTOM N
#         elif "bottom" in query:
#             n = 5
#             for word in query.split():
#                 if word.isdigit():
#                     n = int(word)

#             result = df.sort_values(by=target_col, ascending=True).head(n)

#             labels = result.index.astype(str).tolist()
#             values = result[target_col].tolist()

#             return {
#                 "title": f"Top {n} by {target_col}",
#                 "table": result.to_dict(orient="records"),
#                 "chart": {
#                     "type": "bar",
#                     "labels": labels,
#                     "values": values
#                 }
#             }

#         # AVERAGE
#         elif "average" in query or "mean" in query:
#             if target_col in numeric_cols:
#                 avg = df[target_col].mean()

#                 return {
#                     "title": f"Average of {target_col}",
#                     "table": [{target_col: avg}],
#                     "chart": {
#                         "type": "bar",
#                         "labels": [target_col],
#                         "values": [avg]
#                     }
#                 }

#             return {"error": "Column is not numeric"}

#         else:
#             return {"error": "Query not understood"}

#     except Exception as e:
#         return {"error": str(e)}



from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io

app = FastAPI()

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Global dataset
df = None


# ------------------ ROOT ------------------
@app.get("/")
def home():
    return {"message": "DataSage API is running"}


# ------------------ UPLOAD ------------------
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    global df

    try:
        contents = await file.read()

        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        elif file.filename.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            return {"error": "Unsupported file format"}

        return {
            "message": "File uploaded successfully",
            "columns": df.columns.tolist(),
            "rows": len(df),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "missing_values": df.isnull().sum().to_dict()
        }

    except Exception as e:
        return {"error": str(e)}


# ------------------ HELPER ------------------
def find_column_from_query(query, columns):
    query = query.lower()

    for col in columns:
        col_clean = col.lower().replace("_", " ")
        if col_clean in query:
            return col

    return None


# ------------------ QUERY ------------------
@app.post("/api/query")
async def query_data(payload: dict):
    global df

    query = payload.get("query", "").lower()

    if df is None:
        return {"error": "No dataset uploaded"}

    try:
        columns = df.columns.tolist()
        numeric_cols = df.select_dtypes(include="number").columns.tolist()

        target_col = find_column_from_query(query, columns)

        # fallback if no column found
        if not target_col and len(numeric_cols) > 0:
            target_col = numeric_cols[0]

        # ------------------ TOP ------------------
        if "top" in query:
            n = 5
            for word in query.split():
                if word.isdigit():
                    n = int(word)

            result = df.sort_values(by=target_col, ascending=False).head(n)

            # better labels
            non_numeric_cols = df.select_dtypes(exclude="number").columns
            if len(non_numeric_cols) > 0:
                label_col = non_numeric_cols[0]
                labels = result[label_col].astype(str).tolist()
            else:
                labels = result.index.astype(str).tolist()

            values = result[target_col].tolist()

            return {
                "title": f"Top {n} by {target_col}",
                "table": result.to_dict(orient="records"),
                "chart": {
                    "type": "bar",
                    "labels": labels,
                    "values": values
                }
            }

        # ------------------ BOTTOM ------------------
        elif "bottom" in query:
            n = 5
            for word in query.split():
                if word.isdigit():
                    n = int(word)

            result = df.sort_values(by=target_col, ascending=True).head(n)

            non_numeric_cols = df.select_dtypes(exclude="number").columns
            if len(non_numeric_cols) > 0:
                label_col = non_numeric_cols[0]
                labels = result[label_col].astype(str).tolist()
            else:
                labels = result.index.astype(str).tolist()

            values = result[target_col].tolist()

            return {
                "title": f"Bottom {n} by {target_col}",
                "table": result.to_dict(orient="records"),
                "chart": {
                    "type": "bar",
                    "labels": labels,
                    "values": values
                }
            }

        # ------------------ AVERAGE ------------------
        elif "average" in query or "mean" in query:
            if target_col in numeric_cols:
                avg = df[target_col].mean()

                return {
                    "title": f"Average of {target_col}",
                    "table": [{target_col: avg}],
                    "chart": {
                        "type": "bar",
                        "labels": [target_col],
                        "values": [avg]
                    }
                }

            return {"error": "Column is not numeric"}

        # ------------------ FALLBACK ------------------
        else:
            return {"error": "Query not understood"}

    except Exception as e:
        return {"error": str(e)}