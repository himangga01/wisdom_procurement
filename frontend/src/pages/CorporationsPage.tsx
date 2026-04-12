import { FormEvent, useEffect, useState } from "react";

import { api } from "../app/api";
import type { Corporation } from "../app/types";

export function CorporationsPage() {
  const [list, setList] = useState<Corporation[]>([]);
  const [search, setSearch] = useState("");
  const [form, setForm] = useState({
    name: "",
    business_category: "",
    region: "",
    certifications_json: "",
    company_size_classification: "",
    internal_notes: "",
  });

  const refresh = () => api.listCorporations().then(setList).catch(console.error);

  useEffect(() => {
    refresh();
  }, []);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    await api.createCorporation({
      ...form,
      certifications_json: form.certifications_json
        ? JSON.stringify(
            form.certifications_json
              .split(",")
              .map((item) => item.trim())
              .filter(Boolean),
          )
        : "[]",
    });
    setForm({
      name: "",
      business_category: "",
      region: "",
      certifications_json: "",
      company_size_classification: "",
      internal_notes: "",
    });
    refresh();
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
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
