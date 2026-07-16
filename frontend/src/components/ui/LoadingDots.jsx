export default function LoadingDots() {
  return (
    <div className="ds-loading">
      <div className="ds-dots">
        <div className="ds-dot" />
        <div className="ds-dot" />
        <div className="ds-dot" />
      </div>

      <div className="ds-loading-text">
        Analysing your dataset…
      </div>
    </div>
  );
}