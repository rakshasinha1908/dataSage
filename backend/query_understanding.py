import re
import pandas as pd

from typing import Dict, Any, Optional, Tuple


def detect_operation(query: str) -> str:
    q = query.lower()

    if re.search(r"\b(count|how many|number of|frequency)\b", q):
        return "count"

    if re.search(r"\b(unique|distinct)\b", q):
        return "unique_count"

    if re.search(r"\b(average|avg|mean)\b", q):
        return "avg"

    if re.search(r"\b(total|sum|overall|cumulative)\b", q):
        return "sum"

    if re.search(r"\b(minimum|min|smallest)\b", q):
        return "min"

    if re.search(r"\b(maximum|max)\b", q):
        return "max"

    return None

def is_categorical_distribution_query(query: str, meta: dict) -> Tuple[bool, Optional[str]]:
    q = query.lower()
    dist_patterns = [
        r'\bdistribution\b', r'\bbreakdown\b', r'\bspread\b',
        r'\bproportions?\b', r'\bshare\b', r'\bcomposition\b',
        r'\bfrequency\b', r'\bhow is\b.+\bdistributed\b',
    ]
    if not any(re.search(p, q) for p in dist_patterns):
        return False, None

    free_text = set(meta.get("free_text_cols", []))
    cat_cols  = (meta.get("low_cardinality_cols", []) +
                 meta.get("categorical_cols", []))
    safe_cat  = [c for c in cat_cols if c not in free_text]

    for col in safe_cat:
        words = [w for w in re.split(r'[\s_\-/]+', col.lower()) if len(w) > 2]
        if any(w in q for w in words):
            return True, col

    return (True, safe_cat[0]) if safe_cat else (False, None)


def detect_group_by(query: str, df: pd.DataFrame, meta: dict) -> Optional[str]:
    q         = query.lower()
    synonyms  = meta.get("synonyms", {})
    free_text = set(meta.get("free_text_cols", []))
    id_cols   = set(meta.get("id_like_cols", []))
    schema_registry = meta.get("schema_registry", {})

    safe_cat = [
        c for c in (
            meta.get("low_cardinality_cols", [])
            + meta.get("categorical_cols", [])
            + meta.get("boolean_cols", [])
        )
        if (
            c not in free_text
            and c not in id_cols
            and schema_registry.get(c, {}).get("is_groupable")
        )
    ]
    
    # ─────────────────────────────
    # Semantic grouping prioritization
    # ─────────────────────────────
    schema_registry = meta.get("schema_registry", {})

    safe_cat = sorted(
        safe_cat,
        key=lambda c: schema_registry.get(c, {}).get(
            "group_priority",
            0
        ),
        reverse=True
    )

    group_patterns = [
        r'\b(?:by|per|for each|grouped by|across|among|within|breakdown by)\s+'
        r'([a-z][\w\s]*?)(?:\s+and|\s+where|\s+with|\s+in\s+(?:the\s+)?(?:dataset|data)|[?.,]|$)',
        r'\beach\s+([a-z][\w\s]*?)(?:\s|$)',
    ]
    for pattern in group_patterns:
        m = re.search(pattern, q)
        if m:
            hint = (
                m.group(1)
                .strip()
                .rstrip("?.,")
            )

            hint = re.split(
                r'\b(where|with|having|from|in)\b',
                hint
            )[0].strip()

            scored_cols = []

            for col_candidate in safe_cat:
                score = score_column_match(
                    query=hint,
                    column=col_candidate,
                    synonyms=synonyms,
                    meta=meta,
                    expected_type="dimension"
                )

                # prefer lower cardinality
                nunique = df[col_candidate].nunique()

                if nunique <= 15:
                    score += 12
                elif nunique <= 40:
                    score += 6
                elif nunique > 200:
                    score -= 15

                # semantic grouping priority
                schema_registry = meta.get("schema_registry", {})
                score += schema_registry.get(
                    col_candidate,
                    {}
                ).get("group_priority", 0) * 0.1

                scored_cols.append((col_candidate, score))

            scored_cols.sort(
                key=lambda x: x[1],
                reverse=True
            )

            col = (
                scored_cols[0][0]
                if scored_cols
                and scored_cols[0][1] >= 15
                else None
            )
            if col:
                return col

    entity_map = {
        "city":       ["city", "location", "store", "branch"],
        "region":     ["region", "territory", "zone", "area", "market"],
        "store":      ["store", "branch", "location", "outlet"],
        "product":    ["product", "item", "sku", "category"],
        "customer":   ["customer", "client", "buyer", "name"],
        "category":   ["category", "segment", "type", "department"],
        "country":    ["country", "nation", "market"],
        "month":      ["month", "period"],
        "year":       ["year", "period"],
        "quarter":    ["quarter", "q1", "q2", "q3", "q4"],
        "department": ["department", "team", "division"],
        "channel":    ["channel", "medium", "source", "platform"],
        "brand":      ["brand", "label", "make"],
    }
    # low-priority fallback only

    best_col = None
    best_score = 0

    for entity, signals in entity_map.items():
        if entity in q:
            for cat_col in safe_cat:
                score = 0
                for s in signals:
                    if s in cat_col.lower():
                        score += 1

                # prefer lower cardinality
                nunique = df[cat_col].nunique()

                if nunique <= 20:
                    score += 3
                elif nunique <= 50:
                    score += 1

                if score > best_score:
                    best_score = score
                    best_col = cat_col

    if best_col:
        return best_col

    return None


def extract_filters(query: str, df: pd.DataFrame, meta: dict) -> Dict[str, Any]:
    filters  = {}
    q        = query.lower()
    synonyms = meta.get("synonyms", {})
    all_cols = df.columns.tolist()

    filter_patterns = [
        # explicit filters
        r'where\s+([\w\s]+?)\s+(?:is|=|equals?|==)\s+["\']?([^"\']+?)["\']?(?:\s+and|\s+or|\s*$)',

        # filtered by
        r'(?:filter|filtered)\s+(?:by|for)\s+([\w\s]+?)\s+(?:is|=|equals?)?\s*["\']?([^"\']+?)["\']?(?:\s|$)',

        # generic "with"
        r'with\s+([a-zA-Z][\w\s\-]+?)(?:\s|$)',

        # generic "having"
        r'having\s+([a-zA-Z][\w\s\-]+?)(?:\s|$)',

        # generic "from"
        r'from\s+([a-zA-Z][\w\s\-]+?)(?:\s|$)',

        # generic "in"
        r'in\s+([a-zA-Z][\w\s\-]+?)(?:\s|$)',
    ]

    for pattern in filter_patterns:
        for m in re.finditer(pattern, q):
            groups = m.groups()

            # ─────────────────────────────
            # explicit column=value filters
            # ─────────────────────────────
            if len(groups) >= 2:
                col_hint = groups[0].strip()
                val = groups[1].strip()

                matched = find_column(
                    col_hint,
                    all_cols,
                    synonyms,
                    meta,
                    expected_type="dimension"
                )

                if matched:
                    filters.setdefault(
                        matched,
                        normalize_boolean_value(val)
                    )

            # ─────────────────────────────
            # semantic value matching
            # ─────────────────────────────
            elif len(groups) == 1:
                semantic_text = groups[0].strip()

                semantic_match = resolve_semantic_value(
                    semantic_text,
                    meta
                )

                if semantic_match:
                    filters.setdefault(
                        semantic_match["column"],
                        semantic_match["value"]
                    )

    for val_hint in re.findall(
        r'\bfor\s+["\']?([a-zA-Z][\w\s\-]+?)["\']?(?:\s+in\s+|\s+from\s+|\s+by\s+|\s+where|\s*$)', q
    ):
        val_hint = val_hint.strip()
        if len(val_hint) < 2 or val_hint in ("each", "the", "all", "this", "that"):
            continue
        cat_cols = meta.get("low_cardinality_cols", []) + meta.get("categorical_cols", [])
        for col in cat_cols:
            if col in filters:
                continue
            col_vals = df[col].astype(str).str.lower().unique()
            if val_hint in col_vals:
                matched_val = next(
                    (
                        v for v in col_vals
                        if str(v).lower() == val_hint
                    ),
                    val_hint
                )
                filters[col] = matched_val
                break
            for cv in col_vals:
                cv_str = str(cv).lower()
                if (
                    val_hint in cv_str
                    or cv_str in val_hint
                ):
                    filters[col] = cv
                    break

    for val_hint in re.findall(r'\bin\s+["\']?([a-zA-Z][\w\s\-]+?)["\']?(?:\s|$)', q):
        val_hint = val_hint.strip()
        if len(val_hint) < 2 or val_hint in ("the", "this", "that", "a", "an"):
            continue
        cat_cols = meta.get("low_cardinality_cols", []) + meta.get("categorical_cols", [])
        for col in cat_cols:
            if col in filters:
                continue
            if val_hint in df[col].astype(str).str.lower().unique():
                filters[col] = val_hint
                break

    numeric_cols = meta.get("numeric_cols", [])
    for pattern, op in [
        (r'([\w\s]+?)\s+(?:above|greater than|more than|over|exceeds?|>)\s*(\d+(?:\.\d+)?)', ">"),
        (r'([\w\s]+?)\s+(?:below|less than|under|beneath|<)\s*(\d+(?:\.\d+)?)', "<"),
        (r'([\w\s]+?)\s+(?:at least|>=|minimum of)\s*(\d+(?:\.\d+)?)', ">="),
        (r'([\w\s]+?)\s+(?:at most|<=|maximum of)\s*(\d+(?:\.\d+)?)', "<="),
        (r'([\w\s]+?)\s+(?:!=|not equal to|excluding)\s*(\d+(?:\.\d+)?)', "!="),
    ]:
        for m in re.finditer(pattern, q):
            col_hint, val = m.group(1).strip(), m.group(2)
            matched = find_column(col_hint, numeric_cols, synonyms, meta, expected_type="metric")
            if matched:
                filters.setdefault(matched, {"op": op, "val": float(val)})
    
    # ─────────────────────────────
    # Semantic Value Matching
    # ─────────────────────────────
    semantic_match = resolve_semantic_value(query, meta)

    if semantic_match:
        semantic_col = semantic_match["column"]
        semantic_val = semantic_match["value"]

        if semantic_col not in filters:
            filters[semantic_col] = semantic_val

    return filters


def extract_semantic_roles(query: str, df: pd.DataFrame, meta: dict) -> Dict[str, Any]:
    q = query.lower()
    # remove filler phrases
    q = re.sub(
        r'\b(show|give me|display|tell me|what is|how many)\b',
        '',
        q
    )
    q = re.sub(r'\s+', ' ', q).strip()

    id_cols  = set(meta.get("id_like_cols", []))
    synonyms = meta.get("synonyms", {})
    safe_num = [c for c in meta.get("numeric_cols", []) if c not in id_cols]

    roles: Dict[str, Any] = {
        "metric": None, "aggregation": None, "operation": None, "grouping_entity": None,
        "filters": {}, "ranking": {"direction": None, "limit": 5},
        "date_range": None, "is_count": False,
        "is_cat_dist": False, "cat_dist_col": None,
    }

    roles["operation"] = detect_operation(query)
    if roles["operation"] == "unique_count":
        roles["is_count"] = True
    roles["aggregation"] = roles["operation"]

    if roles["operation"] == "count":
        roles["is_count"] = True
    
    # Improvement #1, #2: Explicit KPI pattern detection (total number, row count, dataset size)
    if re.search(r'\b(total\s+(number|count|records?|entries)|row\s+count|record\s+count|dataset\s+size)\b', q):
        roles["is_count"] = True
        roles["metric"] = None
        roles["grouping_entity"] = None
        logger.debug("KPI: Detected explicit row count query")
    
    # Improvement #2: How many → count query conversion
    if re.search(r'\bhow\s+many\b', q):
        roles["is_count"] = True
        if not roles.get("grouping_entity"):
            roles["metric"] = None
        logger.debug("KPI: Detected 'how many' count query")
        
    # implicit count/grouping queries
    if (
        not roles["metric"]
        and detect_group_by(query, df, meta)
        and re.search(
            r'\b(most|least|highest|lowest|top|bottom|used|common|frequent)\b',
            q
        )
    ):
        roles["is_count"] = True

        if roles["is_count"]:
            roles["metric"] = None

        # Scalar count queries should not force grouping
        if roles["is_count"] and not roles.get("grouping_entity"):
            roles["grouping_entity"] = None

    is_cat, cat_col       = is_categorical_distribution_query(q, meta)
    roles["is_cat_dist"]  = is_cat
    roles["cat_dist_col"] = cat_col

    # Metric detection should NOT run for pure count queries
    if not roles["is_count"]:
        for col in safe_num:
            words = [
                w for w in re.split(r'[\s_\-/]+', col.lower())
                if len(w) > 2
            ]

            if any(w in q for w in words):
                roles["metric"] = col
                logger.debug(f"Metric: Direct match found: {col}")
                break

        if not roles["metric"]:
            # Improvement #9: Business language mapping (sales → revenue, orders → transactions, etc.)
            for biz_term, col_patterns in BUSINESS_LANGUAGE_MAP.items():
                if biz_term in q.split():
                    for col in safe_num:
                        col_lower = col.lower()
                        if any(pattern in col_lower for pattern in col_patterns):
                            roles["metric"] = col
                            logger.debug(f"Metric: Business language match: '{biz_term}' → {col}")
                            break
                    if roles["metric"]:
                        break
            
            # avoid forcing metrics for grouped count queries
            if not roles["metric"] and not (
                roles.get("grouping_entity")
                and roles.get("is_count")
            ):
                roles["metric"] = find_column(
                    query,
                    safe_num,
                    synonyms,
                    meta,
                    expected_type="metric"
                )

    roles["grouping_entity"] = detect_group_by(query, df, meta)
    
    # Improvement #13: Improve group-by detection confidence - never lose explicit groupings
    if roles["grouping_entity"]:
        logger.debug(f"GroupBy: Detected grouping entity: {roles['grouping_entity']}")

    if re.search(r'\b(top|highest|largest|most|best|leading|greatest)\b', q):
        roles["ranking"]["direction"] = "desc"
    elif re.search(r'\b(bottom|lowest|least|worst|smallest|trailing|fewest)\b', q):
        roles["ranking"]["direction"] = "asc"

    for n in re.findall(r'\b(\d+)\b', query):
        n_int = int(n)
        if 1 <= n_int <= 1000:
            roles["ranking"]["limit"] = n_int
            break

    roles["filters"] = extract_filters(query, df, meta)
    
    # Improvement #10: Semantic value matching - create filters for dataset values automatically
    if meta.get("value_index"):
        value_index = meta["value_index"]
        for token, entries in value_index.get("token_map", {}).items():
            if token.lower() in q.split() and len(token) > 2:
                for entry in entries:
                    col = entry.get("column")
                    val = entry.get("value")
                    if col and val and col in df.columns:
                        if col not in roles["filters"]:
                            roles["filters"][col] = val
                            logger.debug(f"Filter: Auto-created from value index: {col}={val}")
    
    # Improvement #11: Fix boolean filter resolution - generate column==True/False
    boolean_cols = meta.get("boolean_cols", [])
    for col in boolean_cols:
        if col in df.columns:
            col_lower = col.lower()
            # Check for boolean value keywords indicating True
            for keyword in ["active", "enabled", "yes", "true", "paid", "completed", "member", "approved"]:
                if keyword in q and col_lower in q:
                    roles["filters"][col] = True
                    logger.debug(f"Filter: Boolean true detected: {col}=True")
                    break
            # Check for keywords indicating False
            if col not in roles["filters"]:
                for keyword in ["inactive", "disabled", "no", "false", "unpaid", "cancelled", "not approved", "rejected"]:
                    if keyword in q and col_lower in q:
                        roles["filters"][col] = False
                        logger.debug(f"Filter: Boolean false detected: {col}=False")
                        break

    return roles
