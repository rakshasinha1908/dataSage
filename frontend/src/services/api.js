const BASE_URL =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000";


export async function uploadDataset(file) {
  const formData = new FormData();

  formData.append("file", file);

  const response = await fetch(
    `${BASE_URL}/upload`,
    {
      method: "POST",
      body: formData,
    }
  );

  if (!response.ok) {
    throw new Error("Upload failed.");
  }

  return response.json();
}


export async function chat(
  sessionId,
  message
) {
  const response = await fetch(
    `${BASE_URL}/chat`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: sessionId,
        follow_up_question: message,
      }),
    }
  );

  if (!response.ok) {
    throw new Error("Chat request failed.");
  }

  return response.json();
}