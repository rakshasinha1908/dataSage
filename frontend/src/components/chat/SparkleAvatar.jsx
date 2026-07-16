import { Icon } from "../ui/Icons";

export default function SparkleAvatar({
  size = "md",
  thinking = false,
}) {
  return (
    <div
      className={`ds-avatar ds-avatar-${size} ${
        thinking ? "thinking" : ""
      }`}
    >
      <div className="ds-avatar-gradient">
        <Icon.Sparkle />
      </div>
    </div>
  );
}