export type DashboardSummary = {
  corporation_count: number;
  project_count: number;
  document_count: number;
};

export type Corporation = {
  id: number;
  name: string;
  business_category: string;
  region: string;
  certifications_json: string;
  company_size_classification: string;
  internal_notes: string;
  created_at: string;
  updated_at: string;
};

export type Project = {
  id: number;
  name: string;
  corporation_id: number;
  status: string;
  notes: string;
  created_at: string;
  updated_at: string;
};

export type DocumentRecord = {
  id: number;
  project_id: number;
  document_type: string;
  original_file_name: string;
  stored_file_path: string;
  mime_type: string;
  file_size: number;
  memo: string;
  revision_note: string;
  parsing_status: string;
  ocr_status: string;
  analysis_status: string;
  latest_analysis_id: number | null;
  created_at: string;
  updated_at: string;
};

export type AnalysisRecord = {
  id: number;
  project_document_id: number;
  analysis_type: string;
  model_provider: string;
  model_name: string;
  prompt_version: string;
  input_hash: string;
  output_json: string;
  output_markdown: string;
  token_usage_json: string;
  status: string;
  error_message: string;
  created_at: string;
};
