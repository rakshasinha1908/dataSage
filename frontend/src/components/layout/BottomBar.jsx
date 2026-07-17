import ChatInput from "../chat/ChatInput";
import Footer from "./Footer";

export default function BottomBar({
  hasUploaded,
  chatHistory,
  suggestions,
  onSuggestionClick,
  onFileChange,
  query,
  setQuery,
  onSend,
  loading,
}) {
  return (
    <div className="ds-bottom-bar">
      <ChatInput
        hasUploaded={hasUploaded}
        chatHistory={chatHistory}
        suggestions={suggestions}
        onSuggestionClick={onSuggestionClick}
        onFileChange={onFileChange}
        query={query}
        setQuery={setQuery}
        onSend={onSend}
        loading={loading}
      />

      <Footer />
    </div>
  );
}