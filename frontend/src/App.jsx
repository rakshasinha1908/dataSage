import { useState, useRef, useEffect, useCallback } from "react";
import Landing from "./components/upload/Landing";
import "./styles/globals.css";
import {
  buildMockUploadInfo,
  generateMockResponse,
} from "./services/mockApi";
import Navbar from "./components/layout/Navbar";
import Footer from "./components/layout/Footer";
import ChatView from "./components/chat/ChatView";
import ChatInput from "./components/chat/ChatInput";
import { EXAMPLE_QUERIES } from "./components/upload/ExampleQueries";


// ─── App ──────────────────────────────────────────────────────────────────────
export default function App() {
  const [uploadedInfo, setUploadedInfo] = useState(null);
  const [query, setQuery]               = useState("");
  const [chatHistory, setChatHistory]   = useState([]);
  const [loading, setLoading]           = useState(false);
  const [dragOver, setDragOver]         = useState(false);

  const bottomRef = useRef(null);
  const fileRef   = useRef(null);

  // Scroll to bottom whenever chat updates
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory, loading]);

  // Suggestions come from the mock dataset info after upload
  const suggestions = uploadedInfo?.suggestions ?? [
    "Top 5 by value",
    "Show trend",
    "Distribution by category",
    "Explain this dataset",
  ];

  // ── Upload (mocked locally) ──────────────────────────────────────────────────
  const handleUpload = (f) => {
    if (!f) return;
    setUploadedInfo(buildMockUploadInfo(f.name));
    setChatHistory([]);
  };

  const onFileChange = (e) => {
    const f = e.target.files[0];
    if (f) handleUpload(f);
    e.target.value = "";
  };

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) handleUpload(f);
  }, []);

  // ── Query (mocked locally) ───────────────────────────────────────────────────
  const handleQuery = (customQuery) => {
    const q = (customQuery ?? query).trim();
    if (!q || loading || !uploadedInfo) return;
    setQuery("");
    setLoading(true);

    // Simulate a short thinking delay so the loading UI is still visible.
    setTimeout(() => {
      const response = generateMockResponse(q);
      setChatHistory(prev => [...prev, { query: q, response }]);
      setLoading(false);
    }, 650);
  };

  // ── Export (stubbed — no backend available) ─────────────────────────────────
  const handleExport = () => {
    // No backend to generate a report from; kept as a no-op stub so the
    // button remains present and functional-looking in the UI.
  };

  const hasUploaded = !!uploadedInfo;

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="ds-root">

      {/* Navbar */}
      <Navbar
        hasUploaded={hasUploaded}
        uploadedInfo={uploadedInfo}
        onExport={handleExport}
      />

      {/* Main content */}
      <div className="ds-main">

        {/* Landing */}
        {!hasUploaded && (
          <div className="ds-landing">
            <Landing
              dragOver={dragOver}
              setDragOver={setDragOver}
              onDrop={onDrop}
              fileRef={fileRef}
              onFileChange={onFileChange}
              exampleQueries={EXAMPLE_QUERIES}
            />
          </div>
        )}

        {/* Chat view */}
        {hasUploaded && (
          <ChatView
          uploadedInfo={uploadedInfo}
          chatHistory={chatHistory}
          loading={loading}
          suggestions={suggestions}
          onSuggestionClick={handleQuery}
          bottomRef={bottomRef}
          />
        )}
 
      </div>

      {/* Sticky input bar */}
      <ChatInput
        hasUploaded={hasUploaded}
        chatHistory={chatHistory}
        suggestions={suggestions}
        onSuggestionClick={handleQuery}
        onFileChange={onFileChange}
        query={query}
        setQuery={setQuery}
        onSend={handleQuery}
        loading={loading}
      />

      {/* Footer */}
      <Footer />

    </div>
  );
}