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
  hallucination?: HallucinationReport;
  actions?: UWAction[];
  sources?: SourceReference[];
}

export interface SourceReference {
  text: string;
  source: string;
  page: number;
  similarity: number;
}

export interface SentenceGrounding {
  sentence: string;
  grounding_score: number;
  best_source: string;
  is_grounded: boolean;
}

export interface HallucinationReport {
  overall_score: number;
  retrieval_confidence: number;
  response_grounding: number;
  numerical_fidelity: number;
  entity_consistency: number;
  sentence_details: SentenceGrounding[];
  flagged_claims: string[];
  rating: 'low' | 'medium' | 'high';
}

export interface UWAction {
  action: string;
  category: 'coverage_gap' | 'risk_flag' | 'endorsement' | 'compliance' | 'pricing';
  priority: 'critical' | 'high' | 'medium' | 'low';
  details: string;
  source_reference: string;
}

export interface UWDocument {
  id: number;
  name: string;
  type: string;
  pages: number;
  status: 'uploading' | 'processing' | 'extracted' | 'reviewed' | 'indexed';
  extractedFields: number;
  totalFields: number;
  uploadDate: string;
  documentId?: string;
  numChunks?: number;
}
