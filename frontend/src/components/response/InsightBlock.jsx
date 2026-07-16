import { Icon } from "../ui/Icons";

export default function InsightBlock({
  text,
  label = "Key Insight",
}) {
  if (!text) return null;

  return (
    <div className="ds-insight">
      <div className="ds-insight-header">
        <Icon.Bulb />
        {label}
      </div>

      {text
        .split("\n")
        .filter(Boolean)
        .map((line, i) => (
          <p key={i}>
            {line.replace(/\*\*/g, "")}
          </p>
        ))}
    </div>
  );
}