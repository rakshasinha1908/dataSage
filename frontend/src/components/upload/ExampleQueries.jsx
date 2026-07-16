export const EXAMPLE_QUERIES = [
  "Top 5 products by revenue",
  "Show sales trends over time",
  "Distribution by category",
  "Compare revenue and profit",
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