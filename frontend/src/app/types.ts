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

export type NaraIntegrationStatus = {
  configured: boolean;
  masked_key: string;
  bid_public_base_url: string;
  pubdata_base_url: string;
  response_type: string;
  last_tested_at: string | null;
  last_test_status: string;
  last_test_http_status: number | null;
  last_test_result_code: string;
  last_test_result_msg: string;
  last_test_total_count: number;
  last_test_detail: string;
};

export type NaraIntegrationTestResult = {
  status: string;
  http_status: number | null;
  result_code: string;
  result_msg: string;
  total_count: number;
  tested_at: string;
  detail?: string;
};

export type NaraAttachmentCandidate = {
  file_name: string;
  source_url: string;
  source_field: string;
  file_extension: string;
  support_status: string;
};

export type NaraNoticeSearchItem = {
  bid_ntce_no: string;
  bid_ntce_ord: string;
  bid_ntce_nm: string;
  ntce_instt_nm: string;
  dminstt_nm: string;
  bid_ntce_dt: string;
  bid_begin_dt: string;
  bid_clse_dt: string;
  openg_dt: string;
  presmpt_prce: string;
  bdgt_amt: string;
  bssamt: string;
  region_text: string;
  license_text: string;
  source_url: string;
  attachment_count: number;
  supported_attachment_count: number;
  attachments: NaraAttachmentCandidate[];
  raw: Record<string, unknown>;
};

export type NaraNoticeSearchResponse = {
  items: NaraNoticeSearchItem[];
  total_count: number;
  page_no: number;
  page_size: number;
  result_code: string;
  result_msg: string;
  http_status: number;
  queried_at: string;
};

export type SavedNaraAttachment = {
  id: number;
  nara_notice_id: number;
  file_name: string;
  source_url: string;
  source_field: string;
  file_extension: string;
  support_status: string;
  download_status: string;
  stored_file_path: string;
  file_size: number;
  parse_status: string;
  analysis_status: string;
  extracted_text_preview: string;
  error_message: string;
  created_at: string;
  updated_at: string;
};

export type SavedNaraNotice = {
  id: number;
  bid_ntce_no: string;
  bid_ntce_ord: string;
  bid_ntce_nm: string;
  ntce_instt_nm: string;
  dminstt_nm: string;
  bid_ntce_dt: string;
  bid_begin_dt: string;
  bid_clse_dt: string;
  openg_dt: string;
  presmpt_prce: string;
  bdgt_amt: string;
  bssamt: string;
  region_text: string;
  license_text: string;
  source_url: string;
  raw_json: string;
  detail_json: string;
  save_status: string;
  download_status: string;
  analysis_status: string;
  analysis_summary_json: string;
  analysis_summary_markdown: string;
  error_message: string;
  created_at: string;
  updated_at: string;
  attachments?: SavedNaraAttachment[];
};
