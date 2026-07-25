import SafeCellRenderer from "../../utils/SafeCellRenderer";
import ChartBlock from "./ChartBlock";
import DataTable from "./DataTable";
import InsightBlock from "./InsightBlock";

export default function ResponseRenderer({ response }) {
  if (!response) {
    return (
      <div className="ds-error-card">
        ⚠ No response data available
      </div>
    );
  }

  const isError = !!response.error;
  const isAI = response.type === "ai";
  const isInsight = response.type === "insight";
  const isStructured = response.type === "structured";
  const isKPI = response.type === "kpi";

  if (isError) {
    return (
      <div className="ds-error-card">
        ⚠ {response.error}
      </div>
    );
  }

  if (
    !isAI &&
    !isInsight &&
    !isStructured &&
    !isKPI 
  ) {
    return (
      <div className="ds-response-card">
        <div className="ds-response-body">
          <div className="ds-response-title">
            {response.title || "Result"}
          </div>

          <div
            style={{
              fontSize: "14px",
              color: "#6B7280",
              marginTop: "12px",
            }}
          >
            Response type "{response.type}" not supported. Raw message:
          </div>

          <div
            style={{
              fontSize: "13px",
              color: "#4B5563",
              marginTop: "8px",
              fontFamily: "'DM Mono', monospace",
            }}
          >
            {response.message ??
              JSON.stringify(response).substring(0, 200)}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="ds-response-card">
      <div className="ds-response-body">
        <div className="ds-response-title">
          {response.title || "Result"}
        </div>

        {(isAI || isInsight) && response.insight && (
    <InsightBlock
        text={response.insight}
        label="AI Insight"
    />
)}

        {isKPI && (
          <>
            <div
              style={{
                marginTop: "20px",
                fontSize: "52px",
                fontWeight: "700",
                color: "#7C3AED",
                letterSpacing: "-2px",
                lineHeight: "1",
              }}
            >
              {typeof response.value === "number"
                ? response.value.toLocaleString()
                : SafeCellRenderer.renderCell(response.value)}
            </div>

            {response.insight && (
              <InsightBlock
                text={response.insight}
                label="Key Insight"
              />
            )}
          </>
        )}

        {isStructured && (
          <>
            {response.insight && (
              <InsightBlock
                text={response.insight}
                label="Key Insight"
              />
            )}

            {response.metadata && (
              <div
                style={{
                  marginTop: "12px",
                  marginBottom: "16px",
                  fontSize: "13px",
                  color: "#6B7280",
                }}
              >
                {response.metadata.truncated ? (
                  <>
                    Showing{" "}
                    <strong>
                      {response.metadata.returned_rows}
                    </strong>{" "}
                    of{" "}
                    <strong>
                      {response.metadata.total_matching_rows}
                    </strong>{" "}
                    matching rows
                  </>
                ) : (
                  <>
                    Showing all{" "}
                    <strong>
                      {response.metadata.returned_rows}
                    </strong>{" "}
                    matching rows
                  </>
                )}
              </div>
            )}

            <DataTable rows={response.table} />
          </>
        )}
      </div>

      {isStructured &&
  response?.chart &&
  response?.table?.length > 0 && (
    <ChartBlock
      chart={response.chart}
      rows={response.table}
    />
)}
    </div>
  );
}