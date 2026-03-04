export interface FileMetadata {
  page_count: number;
  confidence_score: number;
}

export interface FileUploadResult {
  file_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  raw_text: string;
  metadata: FileMetadata;
  error?: string;
}

export interface BatchUploadResponse {
  batch_id: string;
  results: FileUploadResult[];
}

export interface AskRequest {
  query: string;
}

export interface AskResponse {
  answer: string;
  source: string;
  method: string;
  confidence?: number;
}

export interface HealthResponse {
  status: string;
  service: string;
  llm_mode: string;
}
