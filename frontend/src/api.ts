const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export type KnowledgeBase = {
  id: string;
  name: string;
  slug: string;
  department: string | null;
  description: string | null;
};

export type Citation = {
  document_id: string;
  filename: string;
  chunk_index: number;
  page_number: number | null;
  snippet: string;
  score: number;
};

export type ChatResponse = {
  answer: string;
  citations: Citation[];
  conversation_id: string;
};

export async function login(email: string, password: string): Promise<string> {
  const body = new URLSearchParams({ username: email, password });
  const response = await fetch(`${API_BASE}/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!response.ok) {
    throw new Error("Login failed");
  }
  const data = await response.json();
  return data.access_token as string;
}

export async function fetchKnowledgeBases(token: string): Promise<KnowledgeBase[]> {
  const response = await fetch(`${API_BASE}/knowledge-bases`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error("Failed to load knowledge bases");
  }
  return response.json();
}

export async function askQuestion(
  token: string,
  knowledgeBaseId: string,
  question: string
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      knowledge_base_id: knowledgeBaseId,
      stream: false,
    }),
  });
  if (!response.ok) {
    throw new Error("Chat request failed");
  }
  return response.json();
}

export async function uploadDocument(
  token: string,
  knowledgeBaseId: string,
  file: File
): Promise<void> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(
    `${API_BASE}/documents/upload?knowledge_base_id=${knowledgeBaseId}`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    }
  );
  if (!response.ok) {
    throw new Error("Upload failed");
  }
}
