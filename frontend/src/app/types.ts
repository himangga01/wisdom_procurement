export type DashboardSummary = {
  corporation_count: number;
  project_count: number;
  document_count: number;
};

export type OperationsHealthItem = {
  status: string;
  message?: string;
  configured?: boolean;
  masked_key?: string;
  provider?: string;
  model?: string;
  engine?: string;
  path_exists?: boolean;
  free_space_gb?: number;
  rebuild_required?: boolean;
  can_search?: boolean;
  chunk_count?: number;
  db_indexed_chunk_count?: number;
};

export type OperationsFailure = {
  operation_type: string;
  target_type: string;
  target_id: number;
  target_label: string;
  status: string;
  error_message: string;
  occurred_at: string;
  detail_url: string;
};

export type OperationsReviewQueue = {
  queue_type: string;
  label: string;
  count: number;
  detail_url: string;
};

export type OperationsSummary = {
  overall_status: string;
  generated_at: string;
  health: Record<string, OperationsHealthItem>;
  counts: {
    failed_jobs_24h: number;
    pending_reviews: number;
    basis_documents_processing: number;
    judgment_runs_24h: number;
    nara_collection_runs_24h: number;
    nara_notices_processing: number;
    evidence_documents_pending: number;
  };
  recent_failures: OperationsFailure[];
  review_queues: OperationsReviewQueue[];
  last_backup: {
    status: string;
    message: string;
    created_at: string | null;
  };
};

export type OperationRun = {
  id: number;
  operation_type: string;
  target_type: string;
  target_id: number | null;
  status: string;
  requested_by: string;
  request: Record<string, unknown>;
  result: Record<string, unknown>;
  error_message: string;
  error_code: string;
  retry_of_run_id: number | null;
  retry_count: number;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
  updated_at: string;
};

export type BackupValidation = {
  valid: boolean;
  errors: string[];
  warnings: string[];
  manifest: Record<string, unknown>;
  file_path: string;
  file_size_bytes: number;
};

export type BackupRestorePlan = {
  dry_run: boolean;
  can_restore: boolean;
  validation: BackupValidation;
  restore_steps: string[];
  policy: string;
};

export type BackupRun = {
  id: number;
  backup_type: string;
  status: string;
  file_name: string;
  file_path: string;
  file_size_bytes: number;
  manifest: Record<string, unknown>;
  validation: BackupValidation | Record<string, unknown>;
  error_message: string;
  created_at: string;
  completed_at: string | null;
  updated_at: string;
};

export type AiModelSelection = {
  model_provider: string;
  model_name: string;
};

export type AiModelOption = {
  provider: string;
  model: string;
  label: string;
  description: string;
  configured: boolean;
  recommended: boolean;
};

export type AiModelSettings = {
  default_provider: string;
  default_model: string;
  providers: Record<
    string,
    {
      configured: boolean;
      masked_key: string;
      default_model: string;
      secondary_model?: string;
    }
  >;
  options: AiModelOption[];
};

export type Corporation = {
  id: number;
  name: string;
  management_group_name: string;
  business_category: string;
  region: string;
  certifications_json: string;
  company_size_classification: string;
  internal_notes: string;
  business_registration_number: string;
  representative_name: string;
  corporate_registration_number: string;
  business_address: string;
  headquarters_address: string;
  opening_date: string;
  business_type: string;
  business_item: string;
  preference_tags_json: string;
  direct_production_items_json: string;
  license_summary: string;
  procurement_registration_status: string;
  evidence_expiry_summary: string;
  evidence_verification_status: string;
  created_at: string;
  updated_at: string;
  warnings?: string[];
  duplicate_corporations?: CorporationDuplicateSummary[];
};

export type CorporationDuplicateSummary = {
  id: number;
  name: string;
  management_group_name: string;
  business_registration_number: string;
};

export type CorporationProfileUpdateCandidate = {
  id: number;
  evidence_document_id: number;
  corporation_id: number | null;
  field_key: string;
  field_label: string;
  extracted_value: string;
  confidence: number;
  source_text: string;
  status: string;
  applied_at: string | null;
  created_at: string;
  updated_at: string;
};

export type CorporationEvidenceDocument = {
  id: number;
  corporation_id: number | null;
  corporation_name?: string;
  management_group_name: string;
  document_type: string;
  classification_status: string;
  classification_confidence: number;
  original_file_name: string;
  stored_file_path: string;
  mime_type: string;
  file_size: number;
  memo: string;
  extraction_status: string;
  ocr_status: string;
  review_status: string;
  extracted_text: string;
  extracted_text_preview: string;
  extraction_json: string;
  error_message: string;
  created_at: string;
  updated_at: string;
  candidate_count?: number;
  pending_candidate_count?: number;
  approved_candidate_count?: number;
  candidates: CorporationProfileUpdateCandidate[];
};

export type CorporationEvidenceApplyResult = {
  status: string;
  corporation: Corporation;
  evidence: CorporationEvidenceDocument;
  applied_fields: string[];
  warnings?: string[];
};

export type CorporationReadinessCheck = {
  key: string;
  label: string;
  ready: boolean;
};

export type CorporationReadiness = {
  corporation_id: number;
  corporation_name: string;
  management_group_name: string;
  score: number;
  status: string;
  status_label: string;
  ready_count: number;
  total_count: number;
  missing_items: string[];
  checks: CorporationReadinessCheck[];
  evidence_count: number;
  approved_evidence_count: number;
  approved_candidate_count: number;
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

export type BasisDocumentChunk = {
  id: number;
  basis_document_id: number;
  processing_run_id: string;
  chunk_index: number;
  chunk_text: string;
  chunk_text_normalized: string;
  page_start: number | null;
  page_end: number | null;
  section_title: string;
  article_label: string;
  chunk_hash: string;
  token_count: number;
  metadata: Record<string, unknown>;
  vector_id: string;
  vector_status: string;
  embedding_model: string;
  index_error_message: string;
  created_at: string;
  updated_at: string;
};

export type BasisDocument = {
  id: number;
  title: string;
  category: string;
  document_version: string;
  issuing_agency: string;
  effective_date: string;
  source_url: string;
  original_file_name: string;
  stored_file_path: string;
  mime_type: string;
  file_size: number;
  file_hash: string;
  memo: string;
  processing_status: string;
  parse_status: string;
  ocr_status: string;
  chunk_status: string;
  index_status: string;
  page_count: number;
  chunk_count: number;
  vector_count: number;
  extracted_text_preview: string;
  metadata: Record<string, unknown>;
  error_message: string;
  created_at: string;
  updated_at: string;
  processed_at: string | null;
  chunks?: BasisDocumentChunk[];
};

export type BasisRuleCandidate = {
  id: number;
  basis_document_id: number;
  basis_chunk_id: number;
  rule_type: string;
  condition_text: string;
  target_scope: string;
  required_evidence_types: string[];
  related_profile_fields: string[];
  citation_candidate_id: string;
  confidence: number;
  status: string;
  review_note: string;
  reviewed_at: string;
  reviewer_name: string;
  extraction_method: string;
  source_condition_text: string;
  source_required_evidence_types: string[];
  source_related_profile_fields: string[];
  source_confidence: number;
  source_condition_hash: string;
  extraction_key: string;
  created_at: string;
  updated_at: string;
  basis_document?: BasisDocument | null;
  chunk?: BasisDocumentChunk | null;
  expected_citation_candidate_id?: string;
  citation_candidate_valid?: boolean;
  citation_options?: {
    citation_candidate_id: string;
    basis_document_id: number;
    basis_chunk_id: number;
    basis_document_title: string;
    page_start: number | null;
    page_end: number | null;
    section_title: string;
    text_preview: string;
  }[];
};

export type BasisRuleCandidateList = {
  candidate_count: number;
  candidates: BasisRuleCandidate[];
};

export type BasisSearchResult = {
  score: number;
  citation_candidate_id: string;
  chunk: BasisDocumentChunk;
  document: {
    id: number;
    title: string;
    category: string;
    document_version: string;
    issuing_agency: string;
    processing_status: string;
    index_status: string;
  };
  index_source: string;
};

export type BasisSearchResponse = {
  query: string;
  top_k: number;
  result_count: number;
  results: BasisSearchResult[];
  index_source: string;
  note: string;
};

export type BasisIndexStatus = {
  status: string;
  valid: boolean;
  path: string;
  schema_version: string;
  model: string;
  source: string;
  chunk_count: number;
  checksum: string;
  created_at: string;
  updated_at: string;
  db_indexed_chunk_count: number;
  missing_from_index: string[];
  missing_from_db: string[];
  mismatched_chunks: Record<string, unknown>[];
  invalid_index_items: string[];
  rebuild_required: boolean;
  can_search: boolean;
  errors: string[];
  warnings: string[];
  rebuilt_chunk_count?: number;
  archived_path?: string;
};

export type BasisRetrievalEvaluation = {
  id: number;
  name: string;
  query_count: number;
  citation_coverage: number;
  average_top_score: number;
  status: string;
  query_set: {
    queries?: {
      id: string;
      query: string;
      expected_citation_candidate_ids?: string[];
    }[];
    top_k?: number;
    category?: string;
    document_version?: string;
  };
  result: {
    metrics?: {
      result_coverage?: number;
      expected_citation_query_count?: number;
      expected_citation_coverage?: number | null;
      citation_coverage?: number;
      average_top_score?: number;
    };
    query_results?: {
      id: string;
      query: string;
      result_count: number;
      result_hit: boolean;
      top_score: number;
      citation_candidate_ids: string[];
      matched_expected_citation_ids: string[];
      missed_expected_citation_ids: string[];
      expected_citation_hit: boolean | null;
      expected_citation_coverage: number | null;
    }[];
    policy?: string;
  };
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

export type NoticeRequirementCandidate = {
  id: number;
  nara_notice_id: number;
  requirement_type: string;
  requirement_key: string;
  label: string;
  required_value: string;
  normalized_value: string;
  confidence: number;
  source_text: string;
  status: string;
  extraction_method: string;
  created_at: string;
  updated_at: string;
};

export type NoticeRequirementPayload = {
  notice_id: number;
  requirements: NoticeRequirementCandidate[];
  summary: {
    total_count: number;
    type_counts: Record<string, number>;
    status: string;
    note: string;
  };
};

export type CorporationComparisonProfile = {
  corporation_id: number;
  corporation_name: string;
  management_group_name: string;
  regions: string[];
  business_types: string[];
  licenses: string[];
  company_types: string[];
  certifications: string[];
  preference_tags: string[];
  direct_production_items: string[];
  required_documents: string[];
  approved_evidence_count: number;
  approved_evidence_labels: string[];
  profile_note: string;
};

export type NoticeComparisonItem = {
  requirement_candidate_id: number | null;
  requirement_type: string;
  label: string;
  required_value: string;
  normalized_value: string;
  source_text: string;
  confidence: number;
  status: string;
  status_label: string;
  matched_value: string;
  reason: string;
};

export type NoticeCorporationComparison = {
  id: number;
  nara_notice_id: number;
  corporation_id: number;
  status: string;
  summary_json: string;
  result_json: string;
  requirement_count: number;
  prepared_count: number;
  possibly_missing_count: number;
  needs_review_count: number;
  not_found_count: number;
  prompt_version: string;
  created_at: string;
  updated_at: string;
  summary: {
    requirement_count: number;
    prepared_count: number;
    possibly_missing_count: number;
    needs_review_count: number;
    not_found_count: number;
    status: string;
    note: string;
  };
  items: NoticeComparisonItem[];
  profile: CorporationComparisonProfile;
  notice: SavedNaraNotice | null;
  corporation: Corporation | null;
};

export type JudgmentCitationCandidate = {
  citation_candidate_id: string;
  score: number;
  basis_document_id: number | null;
  basis_document_title: string;
  basis_document_version: string;
  chunk_id: number | null;
  page_start: number | null;
  page_end: number | null;
  section_title: string;
  text_preview: string;
  min_score?: number;
  meets_min_score?: boolean;
  source_type?: string;
  basis_rule_candidate_id?: number | null;
  basis_rule_candidate_status?: string;
  basis_rule_candidate_rule_type?: string;
};

export type JudgmentItem = {
  requirement_input_id: string;
  requirement_candidate_id: number | null;
  requirement_type: string;
  label: string;
  required_value: string;
  source_text: string;
  match_status: string;
  status_label: string;
  matched_value: string;
  gap_reason: string;
  recommended_action: string;
  required_evidence_types: string[];
  related_profile_fields: string[];
  citation_status: string;
  citation_candidates: JudgmentCitationCandidate[];
  review_ready_citation_candidates?: JudgmentCitationCandidate[];
  review_evidence_ready: boolean;
  basis_search_fallback_used?: boolean;
  approved_rule_candidate_ids?: number[];
};

export type JudgmentRun = {
  id: number;
  nara_notice_id: number;
  corporation_id: number;
  status: string;
  review_status: string;
  reviewer_note: string;
  matched_count: number;
  missing_count: number;
  uncertain_count: number;
  needs_review_count: number;
  not_applicable_count: number;
  citation_coverage: number;
  rule_version: string;
  created_at: string;
  updated_at: string;
  summary: {
    status: string;
    contract_version: string;
    requirement_count: number;
    matched_count: number;
    missing_count: number;
    uncertain_count: number;
    needs_review_count: number;
    not_applicable_count: number;
    citation_coverage: number;
    note: string;
  };
  result: {
    items: JudgmentItem[];
    preparation_guide: {
      required_documents: string[];
      actions: string[];
      uncertainty_notes: string[];
    };
  };
  input_snapshot: Record<string, unknown>;
  notice: SavedNaraNotice | null;
  corporation: Corporation | null;
};

export type NaraCollectionRun = {
  id: number;
  status: string;
  mode: string;
  keyword: string;
  start_date: string;
  end_date: string;
  searched_count: number;
  saved_count: number;
  skipped_count: number;
  error_message: string;
  criteria: Record<string, unknown>;
  result: {
    items?: Record<string, unknown>[];
    saved_notice_ids?: number[];
    dry_run?: boolean;
    counts?: {
      searched: number;
      saved: number;
      skipped: number;
      save_failures?: number;
    };
    failure_reason?: string;
    retryable?: boolean;
    policy?: string;
  };
  created_at: string;
  updated_at: string;
};
