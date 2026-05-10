import { FormEvent, useEffect, useState } from "react";

import { api } from "../app/api";
import type { Corporation, CorporationEvidenceDocument, CorporationReadiness } from "../app/types";
import { useWorkOverlay } from "../app/workOverlay";

const DEFAULT_MANAGEMENT_GROUP_NAME = "기본 관리그룹";

const emptyForm = {
  name: "",
  management_group_name: DEFAULT_MANAGEMENT_GROUP_NAME,
  business_category: "",
  region: "",
  certifications_json: "",
  company_size_classification: "",
  internal_notes: "",
  business_registration_number: "",
  representative_name: "",
  corporate_registration_number: "",
  business_address: "",
  headquarters_address: "",
  opening_date: "",
  business_type: "",
  business_item: "",
  preference_tags_json: "",
  direct_production_items_json: "",
  license_summary: "",
  procurement_registration_status: "",
  evidence_expiry_summary: "",
};

const emptyEvidenceForm = {
  corporation_id: "",
  management_group_name: DEFAULT_MANAGEMENT_GROUP_NAME,
  document_type: "auto",
  memo: "",
};

const evidenceDocumentTypeOptions = [
  { value: "auto", label: "자동 분류" },
  { value: "business_registration_proof", label: "사업자등록증명" },
  { value: "business_registration_certificate", label: "사업자등록증 사본" },
  { value: "small_business_confirmation", label: "중소기업확인서" },
  { value: "women_owned_business_confirmation", label: "여성기업확인서" },
  { value: "disabled_owned_business_confirmation", label: "장애인기업확인서" },
  { value: "direct_production_confirmation", label: "직접생산확인증명서" },
  { value: "procurement_registration_certificate", label: "나라장터 경쟁입찰참가자격 등록증" },
  { value: "license_registration_certificate", label: "면허/등록/허가증" },
  { value: "tax_payment_certificate", label: "국세 납세증명서" },
  { value: "local_tax_payment_certificate", label: "지방세 납세증명서" },
  { value: "insurance_payment_certificate", label: "4대보험 완납증명서" },
  { value: "credit_rating_certificate", label: "기업신용평가등급확인서" },
  { value: "performance_certificate", label: "실적증명서" },
  { value: "financial_statement_certificate", label: "재무/매출 증빙" },
  { value: "unknown", label: "기타/확인 필요" },
];

type CorporationWorkspaceTab = "upload" | "review" | "library" | "directory";

const corporationWorkspaceTabs: Array<{
  id: CorporationWorkspaceTab;
  label: string;
  description: string;
}> = [
  { id: "upload", label: "증빙 업로드", description: "파일을 먼저 올리고 자동 추출을 시작" },
  { id: "review", label: "추출값 검토", description: "기존값과 비교 후 선택 반영" },
  { id: "library", label: "증빙자료 관리", description: "업로드 이력, 상태, 재처리 관리" },
  { id: "directory", label: "법인 목록/준비도", description: "법인 프로필과 준비도 확인" },
];

function parseCertifications(value: string) {
  try {
    const parsed = JSON.parse(value);
    if (Array.isArray(parsed)) {
      return parsed.join(", ");
    }
  } catch {
    return value;
  }
  return value;
}

function serializeCertifications(value: string) {
  return value
    ? JSON.stringify(
        value
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
      )
    : "[]";
}

export function CorporationsPage() {
  const { runWithOverlay } = useWorkOverlay();
  const [list, setList] = useState<Corporation[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState(emptyForm);
  const [evidenceForm, setEvidenceForm] = useState(emptyEvidenceForm);
  const [evidenceFile, setEvidenceFile] = useState<File | null>(null);
  const [evidenceDocuments, setEvidenceDocuments] = useState<CorporationEvidenceDocument[]>([]);
  const [readinessList, setReadinessList] = useState<CorporationReadiness[]>([]);
  const [latestEvidence, setLatestEvidence] = useState<CorporationEvidenceDocument | null>(null);
  const [evidenceEditForm, setEvidenceEditForm] = useState(emptyEvidenceForm);
  const [correctedEvidenceText, setCorrectedEvidenceText] = useState("");
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<Record<number, boolean>>({});
  const [candidateDraftValues, setCandidateDraftValues] = useState<Record<number, string>>({});
  const [evidenceBusy, setEvidenceBusy] = useState(false);
  const [workspaceTab, setWorkspaceTab] = useState<CorporationWorkspaceTab>("upload");

  const refresh = () =>
    api
      .listCorporations()
      .then((data) => {
        setList(data);
        setError("");
      })
      .catch((err) => setError(err instanceof Error ? err.message : "법인 목록을 불러오지 못했습니다."));

  const refreshEvidenceDocuments = () =>
    api
      .listAllCorporationEvidenceDocuments()
      .then((data) => setEvidenceDocuments(data))
      .catch((err) => setError(err instanceof Error ? err.message : "증빙자료 목록을 불러오지 못했습니다."));

  const refreshReadiness = () =>
    api
      .listCorporationReadiness()
      .then((data) => setReadinessList(data))
      .catch((err) => setError(err instanceof Error ? err.message : "법인 준비도를 불러오지 못했습니다."));

  const reloadEvidenceDocuments = async () => {
    await runWithOverlay(
      {
        title: "증빙자료 목록 새로고침 중",
        steps: ["증빙 목록 조회", "상태값 정리", "화면 갱신"],
        successMessage: "증빙자료 목록을 새로고침했습니다.",
        failureMessage: "증빙자료 목록 새로고침을 완료하지 못했습니다.",
      },
      async () => {
        await refreshEvidenceDocuments();
      },
    );
  };

  const reloadReadiness = async () => {
    await runWithOverlay(
      {
        title: "법인 준비도 새로고침 중",
        steps: ["법인 프로필 조회", "증빙 반영 상태 확인", "준비도 카드 갱신"],
        successMessage: "법인 준비도를 새로고침했습니다.",
        failureMessage: "법인 준비도 새로고침을 완료하지 못했습니다.",
      },
      async () => {
        await refreshReadiness();
      },
    );
  };

  useEffect(() => {
    refresh();
    refreshEvidenceDocuments();
    refreshReadiness();
  }, []);

  useEffect(() => {
    if (!latestEvidence) {
      setSelectedCandidateIds({});
      setCandidateDraftValues({});
      setEvidenceEditForm(emptyEvidenceForm);
      setCorrectedEvidenceText("");
      return;
    }

    const nextSelected: Record<number, boolean> = {};
    const nextDrafts: Record<number, string> = {};
    latestEvidence.candidates.forEach((candidate) => {
      nextSelected[candidate.id] = candidate.status === "pending";
      nextDrafts[candidate.id] = candidate.extracted_value;
    });
    setSelectedCandidateIds(nextSelected);
    setCandidateDraftValues(nextDrafts);
    setEvidenceEditForm({
      corporation_id: latestEvidence.corporation_id ? String(latestEvidence.corporation_id) : "",
      management_group_name: latestEvidence.management_group_name || DEFAULT_MANAGEMENT_GROUP_NAME,
      document_type: latestEvidence.document_type || "auto",
      memo: latestEvidence.memo || "",
    });
    setCorrectedEvidenceText(latestEvidence.extracted_text || latestEvidence.extracted_text_preview || "");
  }, [latestEvidence]);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await runWithOverlay(
        {
          title: "법인 등록 중",
          steps: ["입력값 확인", "법인 프로필 저장", "준비도 갱신"],
          successMessage: "법인 프로필을 등록했습니다.",
          failureMessage: "법인 등록을 완료하지 못했습니다.",
        },
        async () => {
          const created = await api.createCorporation({
            ...form,
            certifications_json: serializeCertifications(form.certifications_json),
          });
          setForm(emptyForm);
          setError("");
          setNotice(created.warnings?.join(" ") || "");
          await Promise.all([refresh(), refreshReadiness()]);
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "법인 등록에 실패했습니다.");
    }
  };

  const onEvidenceUpload = async (e: FormEvent) => {
    e.preventDefault();
    if (!evidenceFile) {
      setError("먼저 사업자등록증명, 사업자등록증 또는 증빙자료 파일을 선택하세요.");
      return;
    }

    const formData = new FormData();
    formData.append("file", evidenceFile);
    formData.append("document_type", evidenceForm.document_type);
    formData.append("management_group_name", evidenceForm.management_group_name);
    formData.append("memo", evidenceForm.memo);
    if (evidenceForm.corporation_id) {
      formData.append("corporation_id", evidenceForm.corporation_id);
    }

    try {
      setEvidenceBusy(true);
      await runWithOverlay(
        {
          title: "증빙자료 OCR 분석 중",
          description: "파일을 업로드한 뒤 OCR, 문서 분류, AI 정리, 후보값 생성을 진행합니다.",
          steps: ["증빙자료 업로드", "OCR/텍스트 추출", "문서 유형 분류", "AI 후보값 정리", "검토 화면 준비"],
          successMessage: "증빙자료 분석이 완료되었습니다. 추출값을 검토해 주세요.",
          failureMessage: "증빙자료 분석을 완료하지 못했습니다.",
          minVisibleMs: 700,
        },
        async () => {
          const evidence = await api.uploadCorporationEvidenceDocument(formData);
          setLatestEvidence(evidence);
          setWorkspaceTab("review");
          setError("");
          setNotice("");
          await Promise.all([refresh(), refreshEvidenceDocuments(), refreshReadiness()]);
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "증빙자료 업로드/추출에 실패했습니다.");
    } finally {
      setEvidenceBusy(false);
    }
  };

  const approveEvidence = async () => {
    if (!latestEvidence) return;
    const selectedIds = latestEvidence.candidates
      .filter((candidate) => candidate.status === "pending" && selectedCandidateIds[candidate.id])
      .map((candidate) => candidate.id);

    if (selectedIds.length === 0) {
      setError("반영할 후보값을 하나 이상 선택하세요.");
      return;
    }

    const fieldValues = latestEvidence.candidates
      .filter((candidate) => selectedIds.includes(candidate.id))
      .reduce<Record<string, string>>((acc, candidate) => {
        acc[candidate.field_key] = candidateDraftValues[candidate.id] ?? candidate.extracted_value;
        return acc;
      }, {});

    try {
      setEvidenceBusy(true);
      await runWithOverlay(
        {
          title: "추출값 반영 중",
          description: "선택한 후보값만 법인 프로필에 반영하고 준비도를 다시 계산합니다.",
          steps: ["선택 후보 확인", "법인 프로필 업데이트", "증빙자료 상태 저장", "준비도 갱신"],
          successMessage: "선택한 추출값을 법인 프로필에 반영했습니다.",
          failureMessage: "추출값 반영을 완료하지 못했습니다.",
        },
        async () => {
          const result = await api.approveCorporationEvidenceDocument(latestEvidence.id, {
            candidate_ids: selectedIds,
            field_values: fieldValues,
          });
          setLatestEvidence(result.evidence);
          setEvidenceFile(null);
          setEvidenceForm(emptyEvidenceForm);
          setError("");
          setNotice(result.warnings?.join(" ") || "");
          await Promise.all([refresh(), refreshEvidenceDocuments(), refreshReadiness()]);
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "추출값 승인/반영에 실패했습니다.");
    } finally {
      setEvidenceBusy(false);
    }
  };

  const openEvidenceDetail = async (id: number) => {
    try {
      setEvidenceBusy(true);
      await runWithOverlay(
        {
          title: "증빙자료 상세 불러오는 중",
          steps: ["상세 데이터 조회", "추출 후보 불러오기", "검토 화면 이동"],
          successMessage: "증빙자료 상세를 불러왔습니다.",
          failureMessage: "증빙자료 상세를 불러오지 못했습니다.",
        },
        async () => {
          const evidence = await api.getCorporationEvidenceDocument(id);
          setLatestEvidence(evidence);
          setWorkspaceTab("review");
          setError("");
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "증빙자료 상세를 불러오지 못했습니다.");
    } finally {
      setEvidenceBusy(false);
    }
  };

  const saveEvidenceMetadata = async () => {
    if (!latestEvidence) return;
    try {
      setEvidenceBusy(true);
      await runWithOverlay(
        {
          title: "증빙자료 메타데이터 저장 중",
          steps: ["수정 내용 확인", "메타데이터 저장", "증빙 목록 갱신"],
          successMessage: "증빙자료 메타데이터를 저장했습니다.",
          failureMessage: "증빙자료 메타데이터 저장을 완료하지 못했습니다.",
        },
        async () => {
      const updated = await api.updateCorporationEvidenceDocument(latestEvidence.id, {
        corporation_id: evidenceEditForm.corporation_id || null,
        management_group_name: evidenceEditForm.management_group_name,
        document_type: evidenceEditForm.document_type,
        memo: evidenceEditForm.memo,
      });
      setLatestEvidence(updated);
      setWorkspaceTab("review");
      setNotice("증빙자료 메타데이터를 저장했습니다.");
      setError("");
      refreshEvidenceDocuments();
      refreshReadiness();
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "증빙자료 메타데이터 저장에 실패했습니다.");
    } finally {
      setEvidenceBusy(false);
    }
  };

  const reprocessEvidence = async (id = latestEvidence?.id) => {
    if (!id) return;
    try {
      setEvidenceBusy(true);
      await runWithOverlay(
        {
          title: "증빙자료 재처리 중",
          description: "기존 파일로 OCR/텍스트 추출과 후보값 분석을 다시 실행합니다.",
          steps: ["재처리 요청", "OCR/텍스트 추출", "AI 후보값 정리", "검토 화면 갱신"],
          successMessage: "증빙자료 재처리가 완료되었습니다.",
          failureMessage: "증빙자료 재처리를 완료하지 못했습니다.",
          minVisibleMs: 700,
        },
        async () => {
      const documentType = latestEvidence?.id === id ? evidenceEditForm.document_type : "auto";
      const updated = await api.reprocessCorporationEvidenceDocument(id, { document_type: documentType });
      setLatestEvidence(updated);
      setWorkspaceTab("review");
      setNotice("증빙자료를 다시 추출했습니다. 후보값을 확인해 주세요.");
      setError("");
      refreshEvidenceDocuments();
      refreshReadiness();
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "증빙자료 재처리에 실패했습니다.");
    } finally {
      setEvidenceBusy(false);
    }
  };

  const reanalyzeCorrectedEvidenceText = async () => {
    if (!latestEvidence) return;
    if (!correctedEvidenceText.trim()) {
      setError("보정할 추출 텍스트를 입력하세요.");
      return;
    }

    try {
      setEvidenceBusy(true);
      await runWithOverlay(
        {
          title: "보정 텍스트 재분석 중",
          description: "사용자가 보정한 OCR 텍스트를 기준으로 후보값을 다시 정리합니다.",
          steps: ["보정 텍스트 전송", "AI 후보값 재정리", "검토 화면 갱신"],
          successMessage: "보정 텍스트 재분석이 완료되었습니다.",
          failureMessage: "보정 텍스트 재분석을 완료하지 못했습니다.",
          minVisibleMs: 650,
        },
        async () => {
      const updated = await api.reanalyzeCorporationEvidenceText(latestEvidence.id, {
        document_type: evidenceEditForm.document_type,
        extracted_text: correctedEvidenceText,
      });
      setLatestEvidence(updated);
      setWorkspaceTab("review");
      setNotice("보정 텍스트 기준으로 다시 분석했습니다. 후보값을 확인해 주세요.");
      setError("");
      refreshEvidenceDocuments();
      refreshReadiness();
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "보정 텍스트 재분석에 실패했습니다.");
    } finally {
      setEvidenceBusy(false);
    }
  };

  const deleteEvidence = async (item: CorporationEvidenceDocument) => {
    if (!window.confirm(`${item.original_file_name} 증빙자료를 삭제할까요?`)) return;
    try {
      setEvidenceBusy(true);
      await runWithOverlay(
        {
          title: "증빙자료 삭제 중",
          steps: ["삭제 요청 전송", "검토 화면 정리", "증빙 목록 갱신"],
          successMessage: "증빙자료를 삭제했습니다.",
          failureMessage: "증빙자료 삭제를 완료하지 못했습니다.",
        },
        async () => {
      await api.deleteCorporationEvidenceDocument(item.id);
      if (latestEvidence?.id === item.id) {
        setLatestEvidence(null);
      }
      setNotice("증빙자료를 삭제했습니다.");
      setError("");
      refreshEvidenceDocuments();
      refreshReadiness();
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "증빙자료 삭제에 실패했습니다.");
    } finally {
      setEvidenceBusy(false);
    }
  };

  const toggleAllCandidates = (checked: boolean) => {
    if (!latestEvidence) return;
    setSelectedCandidateIds(
      latestEvidence.candidates.reduce<Record<number, boolean>>((acc, candidate) => {
        acc[candidate.id] = candidate.status === "pending" ? checked : false;
        return acc;
      }, {}),
    );
  };

  const startEdit = (item: Corporation) => {
    setEditingId(item.id);
    setEditForm({
      name: item.name,
      management_group_name: item.management_group_name || DEFAULT_MANAGEMENT_GROUP_NAME,
      business_category: item.business_category,
      region: item.region,
      certifications_json: parseCertifications(item.certifications_json),
      company_size_classification: item.company_size_classification,
      internal_notes: item.internal_notes,
      business_registration_number: item.business_registration_number || "",
      representative_name: item.representative_name || "",
      corporate_registration_number: item.corporate_registration_number || "",
      business_address: item.business_address || "",
      headquarters_address: item.headquarters_address || "",
      opening_date: item.opening_date || "",
      business_type: item.business_type || "",
      business_item: item.business_item || "",
      preference_tags_json: parseCertifications(item.preference_tags_json || "[]"),
      direct_production_items_json: parseCertifications(item.direct_production_items_json || "[]"),
      license_summary: item.license_summary || "",
      procurement_registration_status: item.procurement_registration_status || "",
      evidence_expiry_summary: item.evidence_expiry_summary || "",
    });
  };

  const onUpdate = async (e: FormEvent) => {
    e.preventDefault();
    if (!editingId) return;

    try {
      await runWithOverlay(
        {
          title: "법인 정보 수정 중",
          steps: ["수정 내용 확인", "법인 프로필 저장", "준비도 갱신"],
          successMessage: "법인 정보를 저장했습니다.",
          failureMessage: "법인 정보 수정을 완료하지 못했습니다.",
        },
        async () => {
          const updated = await api.updateCorporation(editingId, {
            ...editForm,
            certifications_json: serializeCertifications(editForm.certifications_json),
            preference_tags_json: serializeCertifications(editForm.preference_tags_json),
            direct_production_items_json: serializeCertifications(editForm.direct_production_items_json),
          });
          setEditingId(null);
          setEditForm(emptyForm);
          setError("");
          setNotice(updated.warnings?.join(" ") || "");
          await Promise.all([refresh(), refreshReadiness()]);
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "법인 수정에 실패했습니다.");
    }
  };

  const onDelete = async (item: Corporation) => {
    if (!window.confirm(`${item.name} 법인을 삭제할까요? 연결된 프로젝트가 있으면 삭제되지 않습니다.`)) return;
    try {
      await runWithOverlay(
        {
          title: "법인 삭제 중",
          steps: ["삭제 가능 여부 확인", "법인 삭제", "관련 목록 갱신"],
          successMessage: "법인을 삭제했습니다.",
          failureMessage: "법인 삭제를 완료하지 못했습니다.",
        },
        async () => {
          await api.deleteCorporation(item.id);
          await Promise.all([refresh(), refreshEvidenceDocuments(), refreshReadiness()]);
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "법인 삭제에 실패했습니다.");
    }
  };

  const filtered = list.filter((item) => {
    const keyword = search.trim().toLowerCase();
    if (!keyword) return true;
    return [
      item.name,
      item.management_group_name,
      item.business_category,
      item.region,
      item.business_registration_number,
      item.representative_name,
      item.license_summary,
      parseCertifications(item.preference_tags_json || "[]"),
      parseCertifications(item.direct_production_items_json || "[]"),
    ].some((value) =>
      value.toLowerCase().includes(keyword),
    );
  });

  const groupOptions = Array.from(
    new Set(
      [DEFAULT_MANAGEMENT_GROUP_NAME, ...list.map((item) => item.management_group_name || DEFAULT_MANAGEMENT_GROUP_NAME)]
        .map((value) => value.trim())
        .filter(Boolean),
    ),
  );
  const pendingCandidates = latestEvidence?.candidates.filter((candidate) => candidate.status === "pending") ?? [];
  const selectedCandidateCount = pendingCandidates.filter((candidate) => selectedCandidateIds[candidate.id]).length;
  const readinessByCorporationId = new Map(readinessList.map((item) => [item.corporation_id, item]));
  const latestEvidenceCorporation = latestEvidence?.corporation_id
    ? list.find((item) => item.id === latestEvidence.corporation_id)
    : null;

  const profileValueForField = (fieldKey: string) => {
    if (!latestEvidenceCorporation) {
      return latestEvidence?.corporation_id ? "기존 프로필을 찾을 수 없음" : "신규 법인 생성 예정";
    }

    const value = latestEvidenceCorporation[fieldKey as keyof Corporation];
    if (typeof value !== "string" || !value.trim()) {
      return "기존값 없음";
    }

    if (fieldKey.endsWith("_json")) {
      return parseCertifications(value) || "기존값 없음";
    }

    return value;
  };

  return (
    <section className="content-stack">
      <datalist id="management-group-options">
        {groupOptions.map((groupName) => (
          <option key={groupName} value={groupName} />
        ))}
      </datalist>

      <div className="section-heading">
        <div>
          <p className="eyebrow">Corporation Setup</p>
          <h3>증빙자료로 법인 정보를 먼저 정리</h3>
          <p className="section-copy">
            Phase 1.6A/B부터는 법인명을 먼저 타이핑하기보다 사업자등록증명/사업자등록증과 주요 증빙서류를 올리고, 자동 추출값을 확인한 뒤 법인 프로필에 반영합니다.
          </p>
        </div>
      </div>

      <div className="workspace-tabs" role="tablist" aria-label="법인 관리 작업 단계">
        {corporationWorkspaceTabs.map((tab) => (
          <button
            type="button"
            key={tab.id}
            className={`workspace-tab ${workspaceTab === tab.id ? "workspace-tab--active" : ""}`}
            onClick={() => setWorkspaceTab(tab.id)}
            role="tab"
            aria-selected={workspaceTab === tab.id}
          >
            <strong>{tab.label}</strong>
            <span>{tab.description}</span>
          </button>
        ))}
      </div>

      {workspaceTab === "upload" || workspaceTab === "review" ? (
      <form className="surface-card form-card evidence-uploader" onSubmit={onEvidenceUpload}>
        {workspaceTab === "upload" ? (
        <>
        <div className="section-heading">
          <div>
            <p className="eyebrow">Evidence First</p>
            <h3>사업자등록증명 또는 사업자등록증 업로드</h3>
            <p className="section-copy">
              PDF/DOCX/JPG/PNG 파일을 올리면 법인명, 사업자등록번호, 대표자, 주소, 업태/종목 후보를 자동으로 추출합니다.
            </p>
          </div>
          <span className="status-badge status-badge--pending">Phase 1.6A/B</span>
        </div>

        <div className="form-grid">
          <label className="field">
            <span>기존 법인에 연결</span>
            <select
              value={evidenceForm.corporation_id}
              onChange={(e) => {
                const selectedCorporation = list.find((item) => String(item.id) === e.target.value);
                setEvidenceForm((prev) => ({
                  ...prev,
                  corporation_id: e.target.value,
                  management_group_name:
                    selectedCorporation?.management_group_name || prev.management_group_name || DEFAULT_MANAGEMENT_GROUP_NAME,
                }));
              }}
            >
              <option value="">새 법인으로 생성 예정</option>
              {list.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>관리 법인그룹</span>
            <input
              value={evidenceForm.management_group_name}
              list="management-group-options"
              disabled={Boolean(evidenceForm.corporation_id)}
              onChange={(e) =>
                setEvidenceForm((prev) => ({ ...prev, management_group_name: e.target.value }))
              }
              placeholder="예: 기본 관리그룹"
            />
          </label>

          <label className="field">
            <span>증빙서류 유형</span>
            <select
              value={evidenceForm.document_type}
              onChange={(e) => setEvidenceForm((prev) => ({ ...prev, document_type: e.target.value }))}
            >
              {evidenceDocumentTypeOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="field field--full">
            <span>파일 업로드</span>
            <input
              type="file"
              accept=".pdf,.docx,.jpg,.jpeg,.png"
              onChange={(e) => setEvidenceFile(e.target.files?.[0] ?? null)}
            />
          </label>

          <label className="field field--full">
            <span>메모</span>
            <textarea
              value={evidenceForm.memo}
              onChange={(e) => setEvidenceForm((prev) => ({ ...prev, memo: e.target.value }))}
              placeholder="예: 온세이엔씨 사업자등록증 2022년 발급본"
              rows={3}
            />
          </label>
        </div>

        <div className="form-actions">
          <button type="submit" disabled={evidenceBusy}>
            {evidenceBusy ? "처리 중..." : "증빙자료 업로드 및 추출"}
          </button>
        </div>
        </>
        ) : null}

        {workspaceTab === "review" && latestEvidence ? (
          <div className="evidence-result">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Extraction Review</p>
                <h3>자동 추출 후보 확인</h3>
                <p className="section-copy">
                  아래 후보값은 아직 확정값이 아닙니다. 반영할 항목만 선택하고, 틀린 값은 수정한 뒤 승인하세요.
                </p>
              </div>
              <div className="row">
                <button type="button" className="button-secondary" onClick={() => toggleAllCandidates(true)} disabled={pendingCandidates.length === 0}>
                  전체 선택
                </button>
                <button type="button" className="button-secondary" onClick={() => toggleAllCandidates(false)} disabled={pendingCandidates.length === 0}>
                  선택 해제
                </button>
                <button type="button" onClick={approveEvidence} disabled={evidenceBusy || selectedCandidateCount === 0}>
                  {selectedCandidateCount}개 선택 반영
                </button>
              </div>
            </div>

            <dl className="detail-list">
              <div>
                <dt>파일명</dt>
                <dd>{latestEvidence.original_file_name}</dd>
              </div>
              <div>
                <dt>분류</dt>
                <dd>
                  {latestEvidence.document_type} / {latestEvidence.classification_status}
                </dd>
              </div>
              <div>
                <dt>처리 상태</dt>
                <dd>
                  추출 {latestEvidence.extraction_status}, OCR {latestEvidence.ocr_status}, 검토 {latestEvidence.review_status}
                </dd>
              </div>
            </dl>

            <div className="action-help-grid">
              <article>
                <strong>재처리</strong>
                <span>원본 파일을 다시 읽어 OCR/파싱/후보 생성을 새로 실행합니다.</span>
              </article>
              <article>
                <strong>보정 텍스트 재분석</strong>
                <span>OCR 결과를 사람이 고친 뒤, 그 텍스트 기준으로 후보값을 다시 뽑습니다.</span>
              </article>
              <article>
                <strong>선택 반영</strong>
                <span>체크한 후보만 법인 프로필에 반영하므로 불확실한 값은 제외할 수 있습니다.</span>
              </article>
            </div>

            <div className="evidence-metadata-editor">
              <label className="field">
                <span>연결 법인</span>
                <select
                  value={evidenceEditForm.corporation_id}
                  onChange={(e) => {
                    const selectedCorporation = list.find((item) => String(item.id) === e.target.value);
                    setEvidenceEditForm((prev) => ({
                      ...prev,
                      corporation_id: e.target.value,
                      management_group_name:
                        selectedCorporation?.management_group_name || prev.management_group_name || DEFAULT_MANAGEMENT_GROUP_NAME,
                    }));
                  }}
                >
                  <option value="">새 법인/미연결</option>
                  {list.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>증빙서류 유형</span>
                <select
                  value={evidenceEditForm.document_type}
                  onChange={(e) => setEvidenceEditForm((prev) => ({ ...prev, document_type: e.target.value }))}
                >
                  {evidenceDocumentTypeOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>관리 법인그룹</span>
                <input
                  value={evidenceEditForm.management_group_name}
                  list="management-group-options"
                  disabled={Boolean(evidenceEditForm.corporation_id)}
                  onChange={(e) =>
                    setEvidenceEditForm((prev) => ({ ...prev, management_group_name: e.target.value }))
                  }
                />
              </label>
              <label className="field field--full">
                <span>증빙 메모</span>
                <textarea
                  value={evidenceEditForm.memo}
                  onChange={(e) => setEvidenceEditForm((prev) => ({ ...prev, memo: e.target.value }))}
                  rows={2}
                />
              </label>
              <div className="form-actions">
                <button type="button" className="button-secondary" onClick={saveEvidenceMetadata} disabled={evidenceBusy}>
                  메타데이터 저장
                </button>
                <button type="button" className="button-secondary" onClick={() => reprocessEvidence()} disabled={evidenceBusy}>
                  재처리
                </button>
              </div>
            </div>

            <div className="evidence-text-editor">
              <div>
                <p className="eyebrow">OCR Correction</p>
                <h4>OCR/파싱 텍스트 보정</h4>
                <p className="section-copy">
                  스캔본 OCR이 틀렸거나 표 형식이 어긋나면 아래 텍스트를 직접 고친 뒤 다시 분석하세요.
                </p>
              </div>
              <textarea
                value={correctedEvidenceText}
                onChange={(e) => setCorrectedEvidenceText(e.target.value)}
                rows={7}
                placeholder="OCR 또는 파일 파싱으로 추출된 텍스트가 여기에 표시됩니다."
              />
              <div className="form-actions">
                <button type="button" onClick={reanalyzeCorrectedEvidenceText} disabled={evidenceBusy}>
                  보정 텍스트로 다시 분석
                </button>
              </div>
            </div>

            {latestEvidence.candidates.length ? (
              <div className="candidate-review-list">
                {latestEvidence.candidates.map((candidate) => (
                  <article
                    className={`candidate-review-card ${
                      selectedCandidateIds[candidate.id] ? "candidate-review-card--selected" : ""
                    }`}
                    key={candidate.id}
                  >
                    <label className="candidate-check">
                      <input
                        type="checkbox"
                        checked={Boolean(selectedCandidateIds[candidate.id])}
                        disabled={candidate.status !== "pending"}
                        onChange={(e) =>
                          setSelectedCandidateIds((prev) => ({
                            ...prev,
                            [candidate.id]: e.target.checked,
                          }))
                        }
                      />
                      <span>
                        <strong>{candidate.field_label}</strong>
                        <small>{candidate.field_key}</small>
                      </span>
                    </label>
                    <div className="candidate-comparison">
                      <span>기존값</span>
                      <strong>{profileValueForField(candidate.field_key)}</strong>
                      <span>추출값</span>
                      <strong>{candidate.extracted_value || "-"}</strong>
                    </div>
                    <input
                      value={candidateDraftValues[candidate.id] ?? candidate.extracted_value}
                      disabled={candidate.status !== "pending" || !selectedCandidateIds[candidate.id]}
                      onChange={(e) =>
                        setCandidateDraftValues((prev) => ({
                          ...prev,
                          [candidate.id]: e.target.value,
                        }))
                      }
                      aria-label={`${candidate.field_label} 후보값 수정`}
                    />
                    <div className="candidate-meta">
                      <span>신뢰도 {Math.round(candidate.confidence * 100)}%</span>
                      <span className={`status-badge status-badge--${candidate.status === "approved" ? "active" : "pending"}`}>
                        {candidate.status}
                      </span>
                    </div>
                    {candidate.source_text ? <p>{candidate.source_text}</p> : null}
                  </article>
                ))}
              </div>
            ) : (
              <div className="empty-state empty-state--warning">
                <strong>자동 추출 후보가 없습니다.</strong>
                <p>문서 유형을 수동으로 지정하거나 원본 품질을 확인하세요.</p>
              </div>
            )}
          </div>
        ) : workspaceTab === "review" ? (
          <div className="empty-state">
            <strong>검토할 증빙자료가 아직 선택되지 않았습니다.</strong>
            <p>증빙자료를 업로드하거나, 증빙자료 관리 탭에서 기존 파일의 검토 버튼을 눌러 주세요.</p>
            <div className="form-actions">
              <button type="button" onClick={() => setWorkspaceTab("upload")}>
                증빙 업로드로 이동
              </button>
              <button type="button" className="button-secondary" onClick={() => setWorkspaceTab("library")}>
                증빙자료 관리로 이동
              </button>
            </div>
          </div>
        ) : null}
      </form>
      ) : null}

      {workspaceTab === "library" ? (
      <div className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Evidence Library</p>
            <h3>증빙자료 관리</h3>
            <p className="section-copy">
              업로드한 증빙자료를 법인그룹/법인 기준으로 확인하고, 상세 검토/재처리/삭제를 진행합니다.
            </p>
          </div>
          <button type="button" className="button-secondary" onClick={reloadEvidenceDocuments} disabled={evidenceBusy}>
            새로고침
          </button>
        </div>

        {evidenceDocuments.length === 0 ? (
          <div className="empty-state">
            <strong>아직 업로드된 증빙자료가 없습니다.</strong>
            <p>사업자등록증명 또는 추가 증빙자료를 먼저 업로드하면 이곳에서 계속 관리할 수 있습니다.</p>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>파일</th>
                  <th>연결 법인/그룹</th>
                  <th>유형</th>
                  <th>후보</th>
                  <th>처리</th>
                  <th>최근 수정</th>
                  <th>액션</th>
                </tr>
              </thead>
              <tbody>
                {evidenceDocuments.map((item) => (
                  <tr key={item.id} className={latestEvidence?.id === item.id ? "table-row--selected" : ""}>
                    <td>
                      <strong>{item.original_file_name}</strong>
                      {item.memo ? <small>{item.memo}</small> : null}
                    </td>
                    <td>
                      {item.corporation_name || item.management_group_name || "-"}
                    </td>
                    <td>{item.document_type}</td>
                    <td>
                      <span className="status-badge status-badge--pending">
                        대기 {item.pending_candidate_count ?? 0}
                      </span>
                      <span className="status-badge status-badge--active">
                        승인 {item.approved_candidate_count ?? 0}
                      </span>
                    </td>
                    <td>
                      <span className={`status-badge ${item.review_status === "approved" ? "status-badge--active" : "status-badge--muted"}`}>
                        {item.review_status}
                      </span>
                      <small>
                        추출 {item.extraction_status} / OCR {item.ocr_status}
                      </small>
                    </td>
                    <td>{new Date(item.updated_at).toLocaleString("ko-KR")}</td>
                    <td>
                      <div className="row">
                        <button type="button" className="button-secondary" onClick={() => openEvidenceDetail(item.id)} disabled={evidenceBusy}>
                          검토
                        </button>
                        <button type="button" className="button-secondary" onClick={() => reprocessEvidence(item.id)} disabled={evidenceBusy}>
                          재처리
                        </button>
                        <button type="button" className="button-danger" onClick={() => deleteEvidence(item)} disabled={evidenceBusy}>
                          삭제
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      ) : null}

      {workspaceTab === "directory" ? (
      <>
      <div className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Profile Readiness</p>
            <h3>법인 프로필 준비도</h3>
            <p className="section-copy">
              적격/부적격 판정이 아니라, 향후 공고 요구조건 비교를 위해 법인 정보와 증빙이 어느 정도 준비됐는지 보여줍니다.
            </p>
          </div>
          <button type="button" className="button-secondary" onClick={reloadReadiness}>
            준비도 새로고침
          </button>
        </div>

        {readinessList.length === 0 ? (
          <div className="empty-state">
            <strong>준비도를 계산할 법인이 없습니다.</strong>
            <p>증빙자료를 업로드해 법인을 생성하거나 직접 법인을 등록하면 준비도 카드가 표시됩니다.</p>
          </div>
        ) : (
          <div className="readiness-grid">
            {readinessList.map((item) => (
              <article className="readiness-card" key={item.corporation_id}>
                <div className="readiness-card__header">
                  <div>
                    <strong>{item.corporation_name}</strong>
                    <small>{item.management_group_name}</small>
                  </div>
                  <span className={`status-badge ${item.score >= 80 ? "status-badge--active" : item.score >= 50 ? "status-badge--pending" : "status-badge--muted"}`}>
                    {item.status_label}
                  </span>
                </div>
                <div className="readiness-score">
                  <span>{item.score}%</span>
                  <div className="readiness-meter" aria-label={`${item.corporation_name} 준비도 ${item.score}%`}>
                    <i style={{ width: `${item.score}%` }} />
                  </div>
                </div>
                <p>
                  준비 {item.ready_count}/{item.total_count} · 증빙 {item.evidence_count}건 · 승인 후보 {item.approved_candidate_count}개
                </p>
                {item.missing_items.length ? (
                  <div className="readiness-missing">
                    {item.missing_items.slice(0, 4).map((label) => (
                      <span key={label}>{label}</span>
                    ))}
                    {item.missing_items.length > 4 ? <span>+{item.missing_items.length - 4}</span> : null}
                  </div>
                ) : (
                  <div className="readiness-missing readiness-missing--ok">
                    <span>기초 입력 항목 완료</span>
                  </div>
                )}
              </article>
            ))}
          </div>
        )}
      </div>

      <div className="two-column-grid two-column-grid--wide-left">
        <form className="surface-card form-card" onSubmit={onSubmit}>
          <div className="section-heading">
            <div>
              <p className="eyebrow">Manual Fallback</p>
              <h3>증빙자료가 없을 때만 직접 등록</h3>
            </div>
          </div>

          <div className="form-grid">
            <label className="field">
              <span>법인명</span>
              <input
                value={form.name}
                onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
                placeholder="예: 주식회사 벚꽃정보"
                required
              />
            </label>

            <label className="field">
              <span>관리 법인그룹</span>
              <input
                value={form.management_group_name}
                list="management-group-options"
                onChange={(e) => setForm((prev) => ({ ...prev, management_group_name: e.target.value }))}
                placeholder="예: 기본 관리그룹"
              />
            </label>

            <label className="field">
              <span>업종/분류</span>
              <input
                value={form.business_category}
                onChange={(e) => setForm((prev) => ({ ...prev, business_category: e.target.value }))}
                placeholder="예: IT 서비스 / 공공 SI"
              />
            </label>

            <label className="field">
              <span>지역</span>
              <input
                value={form.region}
                onChange={(e) => setForm((prev) => ({ ...prev, region: e.target.value }))}
                placeholder="예: 서울"
              />
            </label>

            <label className="field">
              <span>사업자등록번호</span>
              <input
                value={form.business_registration_number}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, business_registration_number: e.target.value }))
                }
                placeholder="예: 123-45-67890"
              />
            </label>

            <label className="field">
              <span>대표자</span>
              <input
                value={form.representative_name}
                onChange={(e) => setForm((prev) => ({ ...prev, representative_name: e.target.value }))}
                placeholder="예: 홍길동"
              />
            </label>

            <label className="field">
              <span>회사 규모</span>
              <input
                value={form.company_size_classification}
                onChange={(e) => setForm((prev) => ({ ...prev, company_size_classification: e.target.value }))}
                placeholder="예: 중소기업"
              />
            </label>

            <label className="field field--full">
              <span>인증/면허</span>
              <input
                value={form.certifications_json}
                onChange={(e) => setForm((prev) => ({ ...prev, certifications_json: e.target.value }))}
                placeholder="쉼표로 구분해 입력하세요. 예: ISO9001, 직접생산확인"
              />
            </label>

            <label className="field field--full">
              <span>내부 메모</span>
              <textarea
                value={form.internal_notes}
                onChange={(e) => setForm((prev) => ({ ...prev, internal_notes: e.target.value }))}
                placeholder="향후 판단 시 참고할 내부 메모를 남길 수 있습니다."
                rows={4}
              />
            </label>
          </div>

          <div className="form-actions">
            <button type="submit">법인 등록</button>
          </div>
        </form>

        <aside className="surface-card accent-card">
          <p className="eyebrow">Why It Matters</p>
          <h3>왜 법인 정보부터 정리하나</h3>
          <p className="section-copy">
            직접 입력은 빠르지만 오타와 누락이 생기기 쉽습니다. 가능하면 증빙자료를 먼저 올리고, 사용자는 틀린 값만 수정하는 방식으로 운영합니다.
          </p>
          <ul className="feature-list">
            <li>사업자등록번호/대표자/주소 자동 추출</li>
            <li>승인된 후보값만 법인 프로필에 반영</li>
            <li>향후 부족 조건 판단을 위한 증빙 이력 확보</li>
          </ul>
        </aside>
      </div>

      {notice ? (
        <div className="empty-state empty-state--info">
          <strong>확인 안내</strong>
          <p>{notice}</p>
        </div>
      ) : null}

      {error ? (
        <div className="empty-state empty-state--warning">
          <strong>작업을 완료하지 못했습니다.</strong>
          <p>{error}</p>
        </div>
      ) : null}

      <div className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Directory</p>
            <h3>등록된 법인 목록</h3>
          </div>
          <input
            className="search-input"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="법인명, 업종, 지역 검색"
          />
        </div>

        {filtered.length === 0 ? (
          <div className="empty-state">
            <strong>아직 등록된 법인이 없습니다.</strong>
            <p>오른쪽이 아닌 위 폼에서 먼저 기본 법인 정보를 등록해보세요.</p>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>법인명</th>
                  <th>관리그룹</th>
                  <th>사업자등록번호</th>
                  <th>대표자</th>
                  <th>업종/분류</th>
                  <th>우대/면허</th>
                  <th>지역</th>
                  <th>검증</th>
                  <th>준비도</th>
                  <th>최근 수정</th>
                  <th>액션</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((item) => {
                  const readiness = readinessByCorporationId.get(item.id);
                  return (
                    <tr key={item.id}>
                      <td>
                        <strong>{item.name}</strong>
                      </td>
                      <td>{item.management_group_name || DEFAULT_MANAGEMENT_GROUP_NAME}</td>
                      <td>{item.business_registration_number || "-"}</td>
                      <td>{item.representative_name || "-"}</td>
                      <td>{item.business_category || "-"}</td>
                      <td>{parseCertifications(item.preference_tags_json || "[]") || item.license_summary || "-"}</td>
                      <td>{item.region || "-"}</td>
                      <td>
                        <span className={`status-badge ${item.evidence_verification_status === "evidence_reviewed" ? "status-badge--active" : "status-badge--muted"}`}>
                          {item.evidence_verification_status === "evidence_reviewed" ? "증빙 확인" : "미검증"}
                        </span>
                      </td>
                      <td>{readiness ? `${readiness.score}%` : "-"}</td>
                      <td>{new Date(item.updated_at).toLocaleString("ko-KR")}</td>
                      <td>
                        <div className="row">
                          <button type="button" className="button-secondary" onClick={() => startEdit(item)}>
                            편집
                          </button>
                          <button type="button" className="button-danger" onClick={() => onDelete(item)}>
                            삭제
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {editingId ? (
        <form className="surface-card form-card inline-editor" onSubmit={onUpdate}>
          <div className="section-heading">
            <div>
              <p className="eyebrow">Edit Corporation</p>
              <h3>법인 정보 편집</h3>
              <p className="section-copy">선택한 법인의 기본 정보를 바로 수정합니다.</p>
            </div>
            <button type="button" className="button-secondary" onClick={() => setEditingId(null)}>
              취소
            </button>
          </div>

          <div className="form-grid">
            <label className="field">
              <span>법인명</span>
              <input
                value={editForm.name}
                onChange={(e) => setEditForm((prev) => ({ ...prev, name: e.target.value }))}
                required
              />
            </label>

            <label className="field">
              <span>관리 법인그룹</span>
              <input
                value={editForm.management_group_name}
                list="management-group-options"
                onChange={(e) => setEditForm((prev) => ({ ...prev, management_group_name: e.target.value }))}
              />
            </label>

            <label className="field">
              <span>업종/분류</span>
              <input
                value={editForm.business_category}
                onChange={(e) => setEditForm((prev) => ({ ...prev, business_category: e.target.value }))}
              />
            </label>

            <label className="field">
              <span>지역</span>
              <input
                value={editForm.region}
                onChange={(e) => setEditForm((prev) => ({ ...prev, region: e.target.value }))}
              />
            </label>

            <label className="field">
              <span>사업자등록번호</span>
              <input
                value={editForm.business_registration_number}
                onChange={(e) =>
                  setEditForm((prev) => ({ ...prev, business_registration_number: e.target.value }))
                }
              />
            </label>

            <label className="field">
              <span>대표자</span>
              <input
                value={editForm.representative_name}
                onChange={(e) => setEditForm((prev) => ({ ...prev, representative_name: e.target.value }))}
              />
            </label>

            <label className="field">
              <span>회사 규모</span>
              <input
                value={editForm.company_size_classification}
                onChange={(e) =>
                  setEditForm((prev) => ({ ...prev, company_size_classification: e.target.value }))
                }
              />
            </label>

            <label className="field field--full">
              <span>사업장 주소</span>
              <input
                value={editForm.business_address}
                onChange={(e) => setEditForm((prev) => ({ ...prev, business_address: e.target.value }))}
              />
            </label>

            <label className="field field--full">
              <span>인증/면허</span>
              <input
                value={editForm.certifications_json}
                onChange={(e) => setEditForm((prev) => ({ ...prev, certifications_json: e.target.value }))}
                placeholder="쉼표로 구분해 입력하세요."
              />
            </label>

            <label className="field">
              <span>우대/제한 태그</span>
              <input
                value={editForm.preference_tags_json}
                onChange={(e) => setEditForm((prev) => ({ ...prev, preference_tags_json: e.target.value }))}
                placeholder="예: 중소기업, 여성기업"
              />
            </label>

            <label className="field">
              <span>직접생산 품목</span>
              <input
                value={editForm.direct_production_items_json}
                onChange={(e) =>
                  setEditForm((prev) => ({ ...prev, direct_production_items_json: e.target.value }))
                }
                placeholder="예: 전산업무 개발, 시스템관리"
              />
            </label>

            <label className="field field--full">
              <span>면허/등록 요약</span>
              <input
                value={editForm.license_summary}
                onChange={(e) => setEditForm((prev) => ({ ...prev, license_summary: e.target.value }))}
                placeholder="예: 전기공사업 등록"
              />
            </label>

            <label className="field field--full">
              <span>내부 메모</span>
              <textarea
                value={editForm.internal_notes}
                onChange={(e) => setEditForm((prev) => ({ ...prev, internal_notes: e.target.value }))}
                rows={4}
              />
            </label>
          </div>

          <div className="form-actions">
            <button type="submit">수정 저장</button>
          </div>
        </form>
      ) : null}
      </>
      ) : null}
    </section>
  );
}
