import { useState } from "react";
import axios from "axios";
import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

export default function App() {
  const [file, setFile] = useState(null);
  const [response, setResponse] = useState(null);

  const handleUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post(
        "http://127.0.0.1:8000/api/upload",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      setResponse(res.data);
      console.log(res.data);

    } catch (err) {
      console.error(err);
    }
  };

  const [query, setQuery] = useState("");
const [result, setResult] = useState(null);

const handleQuery = async () => {
  try {
    const res = await axios.post("http://127.0.0.1:8000/api/query", {
      query: query,
    });

    setResult(res.data);
    console.log(res.data);

  } catch (err) {
    console.error(err);
  }
};

  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-4">
      <h1 className="text-3xl font-bold">DataSage Upload</h1>

      <input
        type="file"
        onChange={(e) => setFile(e.target.files[0])}
        className="border p-2"
      />

      <button
        onClick={handleUpload}
        className="bg-blue-500 text-white px-4 py-2 rounded"
      >
        Upload
      </button>

      {response && (
  <div className="mt-4 p-4 border rounded w-full max-w-md">
    
    <p><strong>Rows:</strong> {response.rows}</p>

    <p className="mt-2"><strong>Columns:</strong></p>
    <ul className="list-disc ml-5">
      {response.columns.map((col, i) => (
        <li key={i}>{col}</li>
      ))}
    </ul>

    <p className="mt-2"><strong>Column Types:</strong></p>
    <ul className="list-disc ml-5">
      {Object.entries(response.dtypes).map(([col, type], i) => (
        <li key={i}>{col}: {type}</li>
      ))}
    </ul>

    <p className="mt-2"><strong>Missing Values:</strong></p>
    <ul className="list-disc ml-5">
      {Object.entries(response.missing_values).map(([col, val], i) => (
        <li key={i}>{col}: {val}</li>
      ))}
    </ul>

  </div>
)}

<div className="mt-6 w-full max-w-md">
  <input
    type="text"
    placeholder="Ask something like 'top 5 rows'"
    value={query}
    onChange={(e) => setQuery(e.target.value)}
    className="border p-2 w-full"
  />

  <button
    onClick={handleQuery}
    className="bg-green-500 text-white px-4 py-2 mt-2 rounded"
  >
    Ask
  </button>
</div>

{result && (
  <div className="mt-4 p-4 border rounded w-full max-w-md">
    <h2 className="font-bold">{result.title}</h2>

    <pre className="text-xs mt-2 overflow-auto">
      {JSON.stringify(result.table, null, 2)}
    </pre>
  </div>
)}

{result?.chart && (
  <div className="mt-6 w-full max-w-md">
    <BarChart
      width={300}
      height={250}
      data={result.chart.labels.map((label, i) => ({
        name: label,
        value: result.chart.values[i],
      }))}
    >
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="name" />
      <YAxis />
      <Tooltip />
      <Bar dataKey="value" />
    </BarChart>
  </div>
)}
    </div>
  );
}