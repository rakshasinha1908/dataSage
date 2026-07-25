import ReactMarkdown from "react-markdown";
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

      <div className="ds-markdown">
        <ReactMarkdown>
          {text}
        </ReactMarkdown>
      </div>
    </div>
  );
}