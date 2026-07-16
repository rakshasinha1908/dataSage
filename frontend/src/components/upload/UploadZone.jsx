import { Icon } from "../ui/Icons";

export default function UploadZone({
  dragOver,
  setDragOver,
  onDrop,
  fileRef,
  onFileChange,
}) {
  return (
    <div
      className={`ds-dropzone${dragOver ? " active" : ""}`}
      onClick={() => fileRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={onDrop}
    >
      <div className="ds-sparkle-icon">
        <Icon.Sparkle />
      </div>

      <div className="ds-drop-icon">
        <Icon.Upload />
      </div>

      <div className="ds-drop-title">
        Drop your dataset here
      </div>

      <div className="ds-drop-sub">
        or browse <span>(CSV, XLSX supported)</span>
      </div>

      <input
        ref={fileRef}
        type="file"
        accept=".csv,.xlsx,.xls"
        className="ds-hidden-input"
        onChange={onFileChange}
      />
    </div>
  );
}