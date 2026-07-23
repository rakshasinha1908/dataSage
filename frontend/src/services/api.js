const BASE_URL = "http://127.0.0.1:8000";

export async function uploadDataset(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${BASE_URL}/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Upload failed.");
  } 

  return response.json();
}

export async function queryDataset(sessionId, question) {
  const params = new URLSearchParams({
    session_id: sessionId,
    question,
  });

  const response = await fetch(`${BASE_URL}/query?${params}`);

  if (!response.ok) {
    throw new Error("Query failed.");
  }

  return response.json();
}

export async function generateInsight(sessionId, question) {
  const response = await fetch(`${BASE_URL}/insight`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session_id: sessionId,
      follow_up_question: question,
    }),
  });

  if (!response.ok) {
    throw new Error("Insight generation failed.");
  }

  return response.json();
}

