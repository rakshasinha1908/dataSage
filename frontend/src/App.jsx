import { useState, useRef, useEffect, useCallback } from "react";
import Landing from "./components/upload/Landing";
import "./styles/globals.css";
import {
  generateMockResponse,
} from "./services/mockApi";
import {
  uploadDataset,
  queryDataset,
} from "./services/api";
import Navbar from "./components/layout/Navbar";
import ChatView from "./components/chat/ChatView";
import BottomBar from "./components/layout/BottomBar";
import { EXAMPLE_QUERIES } from "./components/upload/ExampleQueries";


// ─── App ──────────────────────────────────────────────────────────────────────
export default function App() {
  const [uploadedInfo, setUploadedInfo] = useState(null);
  const [query, setQuery]               = useState("");
  const [chatHistory, setChatHistory]   = useState([]);
  const [loading, setLoading]           = useState(false);
  const [dragOver, setDragOver]         = useState(false);
  const [sessionId, setSessionId] = useState(null);

  const bottomRef = useRef(null);
  const fileRef   = useRef(null);

  // Scroll to bottom whenever chat updates
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory, loading]);

  // Suggestions come from the mock dataset info after upload
  const suggestions = uploadedInfo?.suggestions ?? [
    "Summarize this dataset.",
  "What trends stand out in this data?",
  "Find unusual patterns or anomalies.",
  "What insights would an analyst notice first?",
  ];

  // ── Upload (mocked locally) ──────────────────────────────────────────────────
  const handleUpload = async (file) => {
  if (!file) return;

  try {
    const response = await uploadDataset(file);

    setSessionId(response.session_id);

setUploadedInfo({
  name: response.filename,
  rows: response.rows,
  columns: response.columns,
  summary: `${response.rows} rows • ${response.columns} columns`,
});

    
  } catch (error) {
    console.error(error);
  }
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
  const handleQuery = async (customQuery) => {
  const q = (customQuery ?? query).trim();

  if (!q || loading || !uploadedInfo || !sessionId) {
    return;
  }

  setQuery("");
  setLoading(true);

  try {
    const response = await queryDataset(sessionId, q);
    console.log(response);

    setChatHistory((prev) => [
      ...prev,
      {
        query: q,
        response,
      },
    ]);
  } catch (error) {
    console.error(error);
  } finally {
    setLoading(false);
  }
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
      <BottomBar
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

    </div>
  );
}