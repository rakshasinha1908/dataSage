export const EXAMPLE_QUERIES = [
  "Summarize this dataset in plain English.",
  "What trends stand out in this data?",
  "Find unusual patterns or anomalies.",
  "What insights would an analyst notice first?",
];
 

import { useState, useEffect } from "react";

export default function ExampleQueries({ queries, onQueryClick }) {
  const [index, setIndex] = useState(0);
  const [fade, setFade] = useState(true);

  useEffect(() => {
    const interval = setInterval(() => {
      setFade(false);
      setTimeout(() => {
        setIndex((prev) => (prev + 1) % queries.length);
        setFade(true);
      }, 200);
    }, 2800);
    return () => clearInterval(interval);
  }, [queries.length]);

  return (
    <div className="ds-example-rotator">
      <span className="ds-example-try">Try:</span>
      <div className="ds-example-pill-zone">
        <button
          className={`ds-example-pill${fade ? " visible" : ""}`}
          onClick={() => onQueryClick?.(queries[index])}
        >
          "{queries[index]}"
        </button>
      </div>
    </div>
  );
}