import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../app/api";
import type { SavedNaraNotice } from "../app/types";
import { useWorkOverlay } from "../app/workOverlay";

function statusTone(status: string) {
  if (status === "completed" || status === "saved") return "active";
  if (status === "pending" || status === "partial_failed" || status === "saving") return "pending";
  return "muted";
}

export function NaraSavedNoticesPage() {
  const { runWithOverlay } = useWorkOverlay();
  const [items, setItems] = useState<SavedNaraNotice[]>([]);
  const [keyword, setKeyword] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = async () => {
    setLoading(true);
    try {
      const data = await api.listSavedNaraNotices(keyword);
      setItems(data);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "저장한 공고 목록을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const onSearch = async () => {
    await runWithOverlay(
      {
        title: "저장 공고 검색 중",
        steps: ["검색 조건 확인", "저장 공고 조회", "목록 갱신"],
        successMessage: "저장 공고 검색이 완료되었습니다.",
        failureMessage: "저장 공고 검색을 완료하지 못했습니다.",
      },
      async () => {
        await refresh();
      },
    );
  };

  const onDelete = async (item: SavedNaraNotice) => {
    if (!window.confirm(`${item.bid_ntce_nm} 저장 공고를 삭제할까요? 다운로드한 첨부 파일도 함께 정리됩니다.`)) return;
    try {
      await runWithOverlay(
        {
          title: "저장 공고 삭제 중",
          steps: ["삭제 요청 전송", "첨부/분석 이력 정리", "저장 공고 목록 갱신"],
          successMessage: "저장 공고를 삭제했습니다.",
          failureMessage: "저장 공고 삭제를 완료하지 못했습니다.",
        },
        async () => {
          await api.deleteSavedNaraNotice(item.id);
          await refresh();
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "저장 공고 삭제에 실패했습니다.");
    }
  };

  return (
    <section className="content-stack" data-demo-id="demo-saved-notices-page">
      <div className="surface-card form-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">저장한 공고</p>
            <h3>저장한 공고</h3>
            <p className="section-copy">
              `공고 상세 저장`으로 DB에 저장한 공고와 첨부 다운로드/분석 상태를 다시 확인합니다.
            </p>
          </div>
          <Link to="/nara-board" className="link-button">
            공고 검색으로 이동
          </Link>
        </div>

        <div className="toolbar">
          <input
            className="search-input"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="공고명, 기관명, 공고번호 검색"
          />
          <button type="button" className="button-secondary" onClick={onSearch}>
            검색
          </button>
        </div>
      </div>

      {error ? (
        <div className="empty-state empty-state--warning">
          <strong>작업을 완료하지 못했습니다.</strong>
          <p>{error}</p>
        </div>
      ) : null}

      <div className="surface-card" data-demo-id="demo-saved-notice-list">
        {loading ? (
          <div className="empty-state">
            <strong>저장한 공고를 불러오는 중입니다.</strong>
            <p>로컬 DB에 저장된 공고 목록을 확인하고 있습니다.</p>
          </div>
        ) : items.length === 0 ? (
          <div className="empty-state">
            <strong>아직 저장한 공고가 없습니다.</strong>
            <p>나라장터 공고 검색에서 공고 1개를 선택하고 `공고 상세 저장`을 실행해보세요.</p>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>공고명</th>
                  <th>기관</th>
                  <th>마감</th>
                  <th>다운로드</th>
                  <th>분석</th>
                  <th>액션</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id} data-demo-id="demo-saved-notice-row" data-demo-row-id={item.id}>
                    <td>
                      <strong>{item.bid_ntce_nm || "-"}</strong>
                      <div className="table-subcopy">
                        {item.bid_ntce_no}-{item.bid_ntce_ord}
                      </div>
                    </td>
                    <td>
                      {item.ntce_instt_nm || "-"}
                      <div className="table-subcopy">{item.dminstt_nm || "-"}</div>
                    </td>
                    <td>{item.bid_clse_dt || "-"}</td>
                    <td>
                      <span className={`status-badge status-badge--${statusTone(item.download_status)}`}>
                        {item.download_status}
                      </span>
                    </td>
                    <td>
                      <span className={`status-badge status-badge--${statusTone(item.analysis_status)}`}>
                        {item.analysis_status}
                      </span>
                    </td>
                    <td>
                      <div className="row">
                        <Link
                          to={`/nara-saved-notices/${item.id}`}
                          className="link-button link-button--soft"
                          data-demo-id="demo-saved-notice-detail-link"
                        >
                          상세
                        </Link>
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
    </section>
  );
}
