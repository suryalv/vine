export interface Insight {
  id: number;
  type: 'critical' | 'warning' | 'info';
  category: string;
  title: string;
  content: string;
  impact: string;
  confidence: number;
}

export interface Submission {
  id: string;
  insured: string;
  type: string;
  premium: string;
  status: 'new' | 'in_review' | 'quoted' | 'bound' | 'declined';
  risk: 'low' | 'medium' | 'high';
  date: string;
  broker: string;
}

export interface ChatMessage {
  id: number;
  role: 'user' | 'ai';
  content: string;
  timestamp: string;
}

export interface UWDocument {
  id: number;
  name: string;
  type: string;
  pages: number;
  status: 'uploading' | 'processing' | 'extracted' | 'reviewed';
  extractedFields: number;
  totalFields: number;
  uploadDate: string;
}
