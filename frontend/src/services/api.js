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