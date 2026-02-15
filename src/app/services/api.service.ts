import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

const BASE = environment.apiBaseUrl;

export interface ChatApiResponse {
  answer: string;
  sources: { text: string; source: string; page: number; similarity: number }[];
  hallucination: {
    overall_score: number;
    retrieval_confidence: number;
    response_grounding: number;
    numerical_fidelity: number;
    entity_consistency: number;
    sentence_details: { sentence: string; grounding_score: number; best_source: string; is_grounded: boolean }[];
    flagged_claims: string[];
    rating: string;
  };
  actions: { action: string; category: string; priority: string; details: string; source_reference: string }[];
  session_id: string;
}

export interface UploadApiResponse {
  document_id: string;
  filename: string;
  num_chunks: number;
  num_pages: number;
  status: string;
}

export interface DocumentApiInfo {
  document_id: string;
  filename: string;
  num_chunks: number;
  num_pages: number;
  upload_time: string;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);

  uploadDocument(file: File): Observable<UploadApiResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<UploadApiResponse>(`${BASE}/api/documents/upload`, formData);
  }

  listDocuments(): Observable<DocumentApiInfo[]> {
    return this.http.get<DocumentApiInfo[]>(`${BASE}/api/documents`);
  }

  deleteDocument(documentId: string): Observable<any> {
    return this.http.delete(`${BASE}/api/documents/${documentId}`);
  }

  chat(query: string, sessionId: string = 'default'): Observable<ChatApiResponse> {
    return this.http.post<ChatApiResponse>(`${BASE}/api/chat`, { query, session_id: sessionId });
  }

  clearSession(sessionId: string): Observable<any> {
    return this.http.delete(`${BASE}/api/chat/session/${sessionId}`);
  }

  bulkDeleteDocuments(documentIds: string[]): Observable<any> {
    return this.http.post(`${BASE}/api/documents/bulk-delete`, documentIds);
  }

  healthCheck(): Observable<{ status: string; gemini_configured: boolean }> {
    return this.http.get<{ status: string; gemini_configured: boolean }>(`${BASE}/health`);
  }
}
