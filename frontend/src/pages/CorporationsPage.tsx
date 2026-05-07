import { FormEvent, useEffect, useState } from "react";

import { api } from "../app/api";
import type { Corporation } from "../app/types";

const emptyForm = {
  name: "",
  business_category: "",
  region: "",
  certifications_json: "",
  company_size_classification: "",
  internal_notes: "",
};

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
  const [list, setList] = useState<Corporation[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState(emptyForm);

  const refresh = () =>
    api
      .listCorporations()
      .then((data) => {
        setList(data);
        setError("");
      })
      .catch((err) => setError(err instanceof Error ? err.message : "법인 목록을 불러오지 못했습니다."));

  useEffect(() => {
    refresh();
  }, []);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await api.createCorporation({
        ...form,
        certifications_json: serializeCertifications(form.certifications_json),
      });
      setForm(emptyForm);
      setError("");
      refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "법인 등록에 실패했습니다.");
    }
  };

  const startEdit = (item: Corporation) => {
    setEditingId(item.id);
    setEditForm({
      name: item.name,
      business_category: item.business_category,
      region: item.region,
      certifications_json: parseCertifications(item.certifications_json),
      company_size_classification: item.company_size_classification,
      internal_notes: item.internal_notes,
    });
  };

  const onUpdate = async (e: FormEvent) => {
    e.preventDefault();
    if (!editingId) return;

    try {
      await api.updateCorporation(editingId, {
        ...editForm,
        certifications_json: serializeCertifications(editForm.certifications_json),
      });
      setEditingId(null);
      setEditForm(emptyForm);
      setError("");
      refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "법인 수정에 실패했습니다.");
    }
  };

  const onDelete = async (item: Corporation) => {
    if (!window.confirm(`${item.name} 법인을 삭제할까요? 연결된 프로젝트가 있으면 삭제되지 않습니다.`)) return;
    try {
      await api.deleteCorporation(item.id);
      refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "법인 삭제에 실패했습니다.");
    }
  };

  const filtered = list.filter((item) => {
    const keyword = search.trim().toLowerCase();
    if (!keyword) return true;
    return [item.name, item.business_category, item.region].some((value) =>
      value.toLowerCase().includes(keyword),
    );
  });

  return (
    <section className="content-stack">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Corporation Setup</p>
          <h3>법인 정보를 먼저 단정하게 정리</h3>
          <p className="section-copy">
            현재는 단일 관리자 포탈이므로, 실무에서 자주 다시 보게 되는 필드만 빠르게 입력할 수 있게 폼을 확장했습니다.
          </p>
        </div>
      </div>

      <div className="two-column-grid two-column-grid--wide-left">
        <form className="surface-card form-card" onSubmit={onSubmit}>
          <div className="section-heading">
            <div>
              <p className="eyebrow">Quick Add</p>
              <h3>새 법인 등록</h3>
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
            향후 자격 판단과 기준문서 검색은 법인 프로필 품질에 크게 의존합니다. 그래서 초기 화면에서도 문서보다 법인 맥락을 먼저 잡도록 UX를 개선했습니다.
          </p>
          <ul className="feature-list">
            <li>이후 프로젝트 생성 시 바로 연결 가능</li>
            <li>지원 가능성 판단을 위한 기초 데이터 확보</li>
            <li>법인별 문서 이력 정리에 유리</li>
          </ul>
        </aside>
      </div>

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
                  <th>업종/분류</th>
                  <th>지역</th>
                  <th>회사 규모</th>
                  <th>최근 수정</th>
                  <th>액션</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <strong>{item.name}</strong>
                    </td>
                    <td>{item.business_category || "-"}</td>
                    <td>{item.region || "-"}</td>
                    <td>{item.company_size_classification || "-"}</td>
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
                ))}
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
              <span>회사 규모</span>
              <input
                value={editForm.company_size_classification}
                onChange={(e) =>
                  setEditForm((prev) => ({ ...prev, company_size_classification: e.target.value }))
                }
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
    </section>
  );
}
