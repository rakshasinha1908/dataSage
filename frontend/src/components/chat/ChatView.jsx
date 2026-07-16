import WelcomeCard from "./WelcomeCard";
import SparkleAvatar from "./SparkleAvatar";
import ResponseRenderer from "../response/ResponseRenderer";
import LoadingDots from "../ui/LoadingDots";

export default function ChatView({
  uploadedInfo,
  chatHistory,
  loading,
  suggestions,
  onSuggestionClick,
  bottomRef,
}) {
  return (
    <div className="ds-chat">

      <WelcomeCard uploadedInfo={uploadedInfo} />

      {chatHistory.map((chat, idx) => {
        const res = chat.response;
        const isLast = idx === chatHistory.length - 1;

        return (
          <div
            key={idx}
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 12,
            }}
          >

            {/* User */}

            <div className="ds-user-row">
              <div className="ds-user-bubble">
                {chat.query}
              </div>
            </div>

            {/* Assistant */}

            <div className="ds-msg">

              <div className="ds-msg-header">

                <SparkleAvatar />

                <div>
                  <div className="ds-msg-name">
                    DataSage
                  </div>

                  <div className="ds-msg-sub">
                    AI Analyst
                  </div>
                </div>

              </div>

              <ResponseRenderer response={res} />

              {!res.error && isLast && (
                <div className="ds-chips">

                  {suggestions.map((s, i) => (
                    <div
                      key={i}
                      className="ds-chip"
                      onClick={() => onSuggestionClick(s)}
                    >
                      {s}
                    </div>
                  ))}

                </div>
              )}

            </div>

          </div>
        );
      })}

      {loading && <LoadingDots />}

      <div ref={bottomRef} />

    </div>
  );
}