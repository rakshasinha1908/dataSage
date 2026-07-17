export const EXAMPLE_QUERIES = [
  "Summarize this dataset in plain English.",
  "What trends stand out in this data?",
  "Find unusual patterns or anomalies.",
  "What insights would an analyst notice first?",
];

export default function ExampleQueries({ queries }) {
  return (
    <>
      <p className="ds-examples-label">
        Example queries
      </p>

      <div className="ds-examples">
        {queries.map((query, index) => (
          <div
            key={index}
            className="ds-example-chip"
          >
            "{query}"
          </div>
        ))}
      </div>
    </>
  );
}