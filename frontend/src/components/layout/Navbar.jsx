import { Icon } from "../ui/Icons";

export default function Navbar({
  hasUploaded,
  uploadedInfo,
  onExport,
}) {
  return (
    <nav className="ds-nav">
      <div className="ds-logo">DataSage</div>

      <div className="ds-nav-right">
        {hasUploaded && (
          <>
            <div className="ds-nav-pill">
              <Icon.File />

              {uploadedInfo.name}

              {uploadedInfo.rows !== "—" && (
                <span
                  style={{
                    color: "#9CA3AF",
                    marginLeft: 4,
                  }}
                >
                  ({Number(uploadedInfo.rows).toLocaleString()} rows)
                </span>
              )}
            </div>

            <button
              className="ds-download-btn"
              onClick={onExport}
            >
              <Icon.Download />
              Download Report
            </button>
          </>
        )}

        <div className="ds-nav-icon">
          <Icon.Bell />
        </div>

        <div className="ds-nav-icon">
          <Icon.User />
        </div>
      </div>
    </nav>
  );
}