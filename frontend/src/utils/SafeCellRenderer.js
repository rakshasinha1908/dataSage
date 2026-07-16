export default class SafeCellRenderer {
  /**
   * Convert any cell value to a safely renderable string.
   * Handles: primitives, objects, arrays, null, undefined
   */
  static renderCell(value) {
    if (value === null || value === undefined) {
      return "—";
    }

    const primitiveType = typeof value;

    if (primitiveType === "string") {
      return value.length > 100
        ? value.substring(0, 100) + "…"
        : value;
    }

    if (primitiveType === "number") {
      return Number.isFinite(value)
        ? value.toLocaleString()
        : "—";
    }

    if (primitiveType === "boolean") {
      return value ? "true" : "false";
    }

    if (primitiveType === "object") {
      try {
        const json = JSON.stringify(value);

        return json.length > 50
          ? json.substring(0, 50) + "…"
          : json;
      } catch {
        return "[Object]";
      }
    }

    return String(value);
  }
}