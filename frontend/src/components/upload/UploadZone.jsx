import { Icon } from "../ui/Icons";

export default function UploadZone({
  dragOver,
  setDragOver,
  onDrop,
  fileRef,
  onFileChange,
}) {
  const openPicker = () => fileRef.current?.click();

  return (
    <div
      className={`ds-dropzone${dragOver ? " active" : ""}`}
      onClick={openPicker}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          openPicker();
        }
      }}
      role="button"
      tabIndex={0}
      aria-label="Upload dataset, CSV or XLSX"
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={onDrop}
    >

      <div className="ds-drop-icon">
        <Icon.Upload />
      </div>

      <div className="ds-drop-title">
        {dragOver ? "Drop it right here" : "Drop your dataset here"}
      </div>

      <div className="ds-drop-sub">
        Start a conversation with your data.
      </div>

      <div className="ds-drop-browse">
        or <span>browse files</span> · CSV, XLSX supported
      </div>

      <input
        ref={fileRef}
        type="file"
        accept=".csv,.xlsx,.xls"
        className="ds-hidden-input"
        onChange={onFileChange}
        tabIndex={-1}
      />
    </div>
  );
}