import SafeCellRenderer from "../../utils/SafeCellRenderer";

export default function DataTable({ rows }) {
  if (!rows?.length) return null;

  const headers = Object.keys(rows[0]);

  return (
    <div className="ds-table-wrap">
      <table className="ds-table">
        <thead>
          <tr>
            {headers.map((header) => (
              <th key={header}>{header}</th>
            ))}
          </tr>
        </thead>

        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {headers.map((header) => (
                <td key={header}>
                  {SafeCellRenderer.renderCell(row[header])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}