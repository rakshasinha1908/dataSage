import { Icon } from "../ui/Icons";

export default function ChatInput({
  hasUploaded,
  chatHistory,
  suggestions,
  onSuggestionClick,
  onFileChange,
  query,
  setQuery,
  onSend,
  loading,
}) {
  return (
    <div className="ds-input-bar">

      {hasUploaded && chatHistory.length === 0 && (
        <div className="ds-bar-chips">
          {suggestions.map((s, i) => (
            <div
              key={i}
              className="ds-bar-chip"
              onClick={() => onSuggestionClick(s)}
            >
              {s}
            </div>
          ))}
        </div>
      )}

      <div className="ds-input-inner">

        <label
          className="ds-input-attach"
          htmlFor="inline-file"
        >
          <Icon.Attach />

          <input
            id="inline-file"
            type="file"
            accept=".csv,.xlsx,.xls"
            className="ds-hidden-input"
            onChange={onFileChange}
          />
        </label>

        <div
          className="ds-input-attach"
          style={{ cursor: "default" }}
        >
          <Icon.Chart />
        </div>

        <input
          className="ds-input-field"
          placeholder={
            hasUploaded
              ? "Ask something about your dataset…"
              : "Upload a dataset first to start querying…"
          }
          value={query}
          disabled={!hasUploaded}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) =>
            e.key === "Enter" && onSend()
          }
        />

        <button
          className="ds-send-btn"
          onClick={onSend}
          disabled={
            loading ||
            !query.trim() ||
            !hasUploaded
          }
        >
          <Icon.Send />
        </button>

      </div>

    </div>
  );
}