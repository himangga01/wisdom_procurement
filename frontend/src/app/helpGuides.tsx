import { createContext, type ReactNode, useContext, useEffect, useMemo, useState } from "react";

type HelpGuide = {
  title: string;
  summary: string;
  details: string[];
};

type HelpGuideContextValue = {
  showGuide: (guide: HelpGuide) => void;
};

const HelpGuideContext = createContext<HelpGuideContextValue | null>(null);

const MENU_GUIDES: Record<string, HelpGuide> = {
  "/": {
    title: "대시보드 메뉴",
    summary: "오늘 처리해야 할 조달 업무와 주요 운영 상태를 한 화면에서 확인합니다.",
    details: [
      "최근 저장 공고, 최근 문서, 운영 상태처럼 다음 행동을 정하는 데 필요한 정보를 요약합니다.",
      "상세 작업이 필요한 경우 카드나 링크를 눌러 해당 관리 화면으로 이동합니다.",
      "개별 판단이나 문서 처리는 하지 않고, 전체 흐름을 빠르게 파악하는 시작 화면입니다.",
    ],
  },
  "/operations": {
    title: "운영 대시보드 메뉴",
    summary: "실패 작업, 백업 상태, 외부 연동 상태처럼 관리자가 봐야 할 운영 정보를 확인합니다.",
    details: [
      "나라장터 수집, 문서 분석, 백업 같은 운영성 작업의 최근 상태를 보여줍니다.",
      "문제가 있는 작업은 실패 사유와 재시도 가능 여부를 확인하는 화면으로 이어집니다.",
      "서비스가 로컬에서 안정적으로 동작하는지 점검할 때 먼저 보는 메뉴입니다.",
    ],
  },
  "/operation-runs": {
    title: "작업 이력 메뉴",
    summary: "자동 수집, 분석, 백업 등 백엔드 작업의 실행 결과와 실패 사유를 추적합니다.",
    details: [
      "작업별 시작/종료 시간, 상태, 입력값, 결과 요약을 확인합니다.",
      "실패한 작업은 원인을 확인하고 가능한 경우 재시도할 수 있습니다.",
      "운영 중 문제가 발생했을 때 디버깅 출발점으로 사용하는 메뉴입니다.",
    ],
  },
  "/backups": {
    title: "백업/복원 메뉴",
    summary: "로컬 DB와 저장 파일을 ZIP 백업으로 만들고, 복원 가능성을 검증합니다.",
    details: [
      "백업 생성은 현재 서비스 데이터를 ZIP 파일로 저장합니다.",
      "검증은 백업 파일 구조와 manifest가 정상인지 확인합니다.",
      "복원 dry-run은 실제 복원 전에 어떤 항목이 복원될지 계획만 확인합니다.",
    ],
  },
  "/nara-board": {
    title: "나라장터 공고 검색 메뉴",
    summary: "공공데이터 API를 통해 나라장터 공고를 검색하고 필요한 공고를 저장합니다.",
    details: [
      "검색 조건을 입력해 공고 목록을 조회합니다.",
      "선택한 공고는 로컬 DB에 저장하고 PDF/DOCX 첨부 문서를 다운로드/분석합니다.",
      "HTML 크롤링이 아니라 설정된 나라장터 API 키를 사용하는 화면입니다.",
    ],
  },
  "/nara-saved-notices": {
    title: "저장한 공고 메뉴",
    summary: "저장된 공고와 첨부 문서 처리 상태, 분석 결과를 관리합니다.",
    details: [
      "이미 저장한 공고의 상세 정보와 첨부 파일 목록을 확인합니다.",
      "분석이 실패했거나 오래된 공고는 상세 화면에서 재분석할 수 있습니다.",
      "계약서 생성, 부족조건 비교, 판단 검토 같은 후속 작업의 기준이 됩니다.",
    ],
  },
  "/notice-comparison": {
    title: "부족조건 미리보기 메뉴",
    summary: "공고 요구조건과 법인 준비 상태를 비교해 부족 가능성이 있는 항목을 먼저 확인합니다.",
    details: [
      "저장한 공고와 법인을 선택해 요구조건 추출 결과를 비교합니다.",
      "최종 자격 판정이 아니라 준비 부족 가능성을 확인하는 사전 검토 화면입니다.",
      "부족 서류, 인증, 업종, 직접생산 관련 확인 포인트를 정리하는 데 사용합니다.",
    ],
  },
  "/judgment-runs": {
    title: "판단 검토 메뉴",
    summary: "공고, 법인, 기준문서 근거를 묶어 부족조건 중심 판단 결과를 검토합니다.",
    details: [
      "판단 실행 결과는 관리자 검토가 필요한 초안으로 다룹니다.",
      "기준문서 근거가 부족한 조건은 확정 근거로 사용하지 않는 흐름을 유지합니다.",
      "검토 메모를 남겨 후속 준비 가이드와 운영 이력에 반영할 수 있습니다.",
    ],
  },
  "/contracts": {
    title: "계약서 생성 메뉴",
    summary: "선택한 공고와 법인 정보를 기반으로 검토용 DOCX 계약서 초안을 생성합니다.",
    details: [
      "나라장터 공고 정보와 법인 기본정보를 입력값으로 사용합니다.",
      "생성된 문서는 검토용 초안이며, 실제 제출 전 담당자가 반드시 확인해야 합니다.",
      "기존 생성 이력에서 다운로드하거나 불필요한 초안을 삭제할 수 있습니다.",
    ],
  },
  "/nara-collection-runs": {
    title: "자동 수집 관리 메뉴",
    summary: "나라장터 API 수집 작업을 실행하고, 수집 이력과 실패 사유를 확인합니다.",
    details: [
      "검색 조건을 저장해 반복 수집하거나 즉시 수집 실행을 할 수 있습니다.",
      "각 수집 run의 입력 조건, 저장 건수, 실패 건수를 추적합니다.",
      "실패 원인을 운영 이력과 함께 확인해 재실행 여부를 판단합니다.",
    ],
  },
  "/documents": {
    title: "문서 업로드 메뉴",
    summary: "프로젝트에 속한 일반 PDF/DOCX 문서를 업로드하고 분석합니다.",
    details: [
      "공고 첨부나 사업 문서처럼 프로젝트 단위로 관리할 파일을 등록합니다.",
      "업로드 후 텍스트 추출, OCR 보조, AI 요약 분석 상태를 확인합니다.",
      "기준문서 RAG용 문서와는 분리된 일반 문서 영역입니다.",
    ],
  },
  "/basis-documents": {
    title: "기준문서 관리 메뉴",
    summary: "기준문서 PDF를 업로드하고 텍스트 추출, 청킹, JSON 인덱싱 상태를 관리합니다.",
    details: [
      "기준문서는 프로젝트에 속하지 않는 재사용 지식 자산입니다.",
      "청크 본문은 화면 렉을 줄이기 위해 필요할 때만 따로 불러옵니다.",
      "검색과 판단 근거 품질을 좌우하므로 인덱스 상태와 청크 품질을 함께 확인합니다.",
    ],
  },
  "/basis-rule-candidates": {
    title: "규칙 후보 관리 메뉴",
    summary: "기준문서에서 추출한 조건 후보를 승인, 반려, 수정해 판단 근거로 다듬습니다.",
    details: [
      "자동 추출된 후보는 바로 확정하지 않고 관리자 검토 대상으로 둡니다.",
      "승인된 후보만 판단 엔진의 강한 근거로 사용할 수 있습니다.",
      "후보 문구, 규칙 유형, 근거 연결 상태를 확인하고 보정합니다.",
    ],
  },
  "/basis-retrieval-evaluations": {
    title: "검색 평가 메뉴",
    summary: "기준문서 RAG 검색이 실제 질의에서 적절한 청크와 근거를 찾는지 평가합니다.",
    details: [
      "평가 질의를 실행해 검색 품질과 근거 누락 가능성을 확인합니다.",
      "JSON 기준문서 인덱스를 사용하는 검색 품질 점검 화면입니다.",
      "RAG 개선 전후 결과를 비교하는 운영 QA 용도로 사용합니다.",
    ],
  },
  "/corporations": {
    title: "법인 관리 메뉴",
    summary: "법인 기본정보와 증빙자료를 관리하고, 검토 승인된 값만 프로필에 반영합니다.",
    details: [
      "사업자등록증명, 사업자등록증, 인증서, 면허, 확인서, 특허/저작권 문서 등 법인이 보유한 여러 증빙자료를 업로드해 자동 추출 후보를 만들 수 있습니다.",
      "여러 파일을 한 번에 선택하면 순서대로 분석하고, 증빙자료 관리 탭에서 각 문서의 검토 버튼으로 후보값을 확인합니다.",
      "AI나 OCR 결과는 자동 확정하지 않고 사용자가 승인한 값만 반영합니다.",
      "공고 비교와 판단 실행에서 사용하는 법인 준비 상태의 기준 데이터입니다.",
    ],
  },
  "/projects": {
    title: "프로젝트 관리 메뉴",
    summary: "일반 업로드 문서를 프로젝트 단위로 묶어 업무 흐름을 정리합니다.",
    details: [
      "프로젝트는 일반 문서 업로드와 분석 이력을 관리하는 단위입니다.",
      "법인, 공고, 문서 작업을 업무별로 분리해 추적할 때 사용합니다.",
      "기준문서나 나라장터 저장 공고와는 별도 도메인으로 관리됩니다.",
    ],
  },
  "/settings/integrations/nara": {
    title: "API 설정 메뉴",
    summary: "나라장터 API와 AI 모델 키 설정 상태를 확인하고 연결 테스트를 실행합니다.",
    details: [
      "전체 API 키 값은 화면에 노출하지 않고 설정 여부와 마스킹된 상태만 보여줍니다.",
      "연결 테스트로 현재 환경변수와 외부 API 응답 상태를 확인합니다.",
      "키 값은 백엔드 `.env`에 설정하는 것을 전제로 합니다.",
    ],
  },
  "/settings/external-access": {
    title: "외부 접속 메뉴",
    summary: "ngrok을 통해 로컬 서비스를 외부에서 접속할 수 있는 공개 URL 상태를 확인합니다.",
    details: [
      "프론트엔드와 백엔드 공개 URL을 확인하고 복사할 수 있습니다.",
      "다른 PC나 외부 사용자에게 테스트 URL을 전달할 때 사용합니다.",
      "로컬 단일 PC 운영을 유지하면서 임시 외부 접속만 제공하는 기능입니다.",
    ],
  },
};

const ACTION_GUIDES: Array<{ keys: string[]; guide: HelpGuide }> = [
  {
    keys: ["새로고침", "다시 불러오기", "상태 새로고침"],
    guide: {
      title: "새로고침 버튼",
      summary: "현재 화면의 목록이나 상태 정보를 백엔드에서 다시 불러옵니다.",
      details: [
        "입력 중인 새 데이터가 아니라 서버에 저장된 최신 상태를 다시 조회합니다.",
        "외부 API나 비동기 작업이 끝난 뒤 결과를 확인할 때 사용합니다.",
        "저장되지 않은 입력값이 있는 화면에서는 먼저 저장 여부를 확인하는 것이 좋습니다.",
      ],
    },
  },
  {
    keys: ["조회", "검색"],
    guide: {
      title: "조회/검색 버튼",
      summary: "입력한 필터와 검색 조건을 기준으로 목록이나 결과를 다시 조회합니다.",
      details: [
        "검색어, 상태, 날짜, 카테고리 같은 현재 입력값을 요청 조건으로 사용합니다.",
        "결과가 없으면 조건을 넓히거나 필수 API 설정 상태를 확인해야 합니다.",
        "조회 자체는 데이터를 확정하거나 삭제하지 않는 읽기 작업입니다.",
      ],
    },
  },
  {
    keys: ["저장", "수정 저장", "메타데이터 저장"],
    guide: {
      title: "저장 버튼",
      summary: "현재 화면에서 편집한 값을 로컬 DB에 반영합니다.",
      details: [
        "저장 후에는 목록과 상세 화면에서 변경된 값이 기준으로 사용됩니다.",
        "분석 결과나 추출 후보처럼 별도 검토가 필요한 값은 저장 후에도 승인 상태를 확인해야 합니다.",
        "필수 입력값이 빠져 있으면 백엔드 검증 오류가 표시될 수 있습니다.",
      ],
    },
  },
  {
    keys: ["삭제"],
    guide: {
      title: "삭제 버튼",
      summary: "선택한 항목을 로컬 저장소나 DB에서 제거합니다.",
      details: [
        "삭제 전 확인창이 뜨면 대상 항목이 맞는지 다시 확인합니다.",
        "기준문서나 저장 공고처럼 후속 분석에 쓰이는 데이터는 삭제 후 관련 결과가 사라질 수 있습니다.",
        "운영 이력이나 백업 정책에 따라 복구 가능 여부가 달라질 수 있습니다.",
      ],
    },
  },
  {
    keys: ["업로드", "문서 업로드", "기준문서 업로드"],
    guide: {
      title: "업로드 버튼",
      summary: "선택한 파일을 서버 저장소에 등록하고 필요한 분석 파이프라인을 시작합니다.",
      details: [
        "일반 문서는 프로젝트 문서로, 기준문서는 RAG용 기준문서로 분리되어 저장됩니다.",
        "PDF/DOCX 지원 범위와 기준문서 PDF 전용 규칙을 확인해야 합니다.",
        "업로드 후 텍스트 추출, OCR 보조, 청킹, 인덱싱 상태를 화면에서 확인합니다.",
      ],
    },
  },
  {
    keys: ["분석", "재분석", "다시 분석", "보정문 재분석"],
    guide: {
      title: "분석/재분석 버튼",
      summary: "문서나 공고 첨부를 다시 파싱하고 AI 요약 또는 요구조건 추출을 실행합니다.",
      details: [
        "기존 결과가 있더라도 최신 파일/설정 기준으로 새 분석을 시도합니다.",
        "AI 키나 OCR 엔진이 없으면 fallback 또는 설정 필요 상태가 표시될 수 있습니다.",
        "재분석 전 기존 정상 결과 보존 여부와 실패 메시지를 함께 확인하는 것이 좋습니다.",
      ],
    },
  },
  {
    keys: ["재처리"],
    guide: {
      title: "재처리 버튼",
      summary: "기준문서나 증빙자료를 다시 추출/정규화/인덱싱합니다.",
      details: [
        "파일 내용은 그대로 두고 파이프라인 결과를 다시 생성할 때 사용합니다.",
        "기준문서 재처리는 성공 시 새 청크와 인덱스로 교체되는 흐름을 기대합니다.",
        "실패하면 상태와 로그를 확인해 OCR, PDF 추출, JSON 인덱스 문제를 점검합니다.",
      ],
    },
  },
  {
    keys: ["청크 보기", "청크 숨기기"],
    guide: {
      title: "청크 보기 버튼",
      summary: "기준문서에서 생성된 청크 목록을 필요할 때만 불러와 화면에 표시합니다.",
      details: [
        "큰 기준문서는 청크가 많아 페이지 진입 시 자동으로 렌더링하지 않습니다.",
        "청크 보기 버튼을 누르면 전용 API로 청크 목록을 불러옵니다.",
        "본문이 긴 청크는 더보기 버튼으로 개별 확장할 수 있습니다.",
      ],
    },
  },
  {
    keys: ["더보기", "접기"],
    guide: {
      title: "본문 펼침 버튼",
      summary: "긴 텍스트나 청크 본문을 필요한 항목만 펼치거나 다시 접습니다.",
      details: [
        "초기 화면 렉과 가독성 문제를 줄이기 위해 긴 본문은 축약 표시됩니다.",
        "검토가 필요한 항목만 펼쳐 전체 내용을 확인합니다.",
        "접기를 누르면 다시 미리보기 길이로 줄어듭니다.",
      ],
    },
  },
  {
    keys: ["승인", "반영"],
    guide: {
      title: "승인/반영 버튼",
      summary: "검토가 끝난 후보 값을 실제 프로필이나 판단 근거로 사용할 수 있게 확정합니다.",
      details: [
        "AI/OCR이 만든 후보는 자동 확정하지 않고 사용자가 승인해야 반영됩니다.",
        "승인 후에는 공고 비교, 판단 실행, 준비도 계산의 기준 데이터가 될 수 있습니다.",
        "잘못 승인한 값은 수정 화면에서 다시 보정해야 합니다.",
      ],
    },
  },
  {
    keys: ["반려"],
    guide: {
      title: "반려 버튼",
      summary: "부정확하거나 사용할 수 없는 후보를 판단 근거에서 제외합니다.",
      details: [
        "반려된 후보는 자동 판단 근거로 사용하지 않습니다.",
        "오탐, 중복, 근거 연결 불일치가 있는 후보를 정리할 때 사용합니다.",
        "반려 사유가 필요한 경우 운영 메모에 남겨 후속 검토자가 이해할 수 있게 합니다.",
      ],
    },
  },
  {
    keys: ["계약서 생성", "생성"],
    guide: {
      title: "생성 버튼",
      summary: "선택한 입력값을 기반으로 새 결과물이나 실행 이력을 만듭니다.",
      details: [
        "계약서 생성은 공고와 법인 정보를 기반으로 DOCX 초안을 만듭니다.",
        "프로젝트/법인 생성은 입력한 기본정보를 로컬 DB에 저장합니다.",
        "생성 결과는 검토용이며, 실제 제출 전 사람이 최종 확인해야 합니다.",
      ],
    },
  },
  {
    keys: ["다운로드"],
    guide: {
      title: "다운로드 버튼",
      summary: "생성된 파일이나 원본 첨부를 로컬 브라우저로 내려받습니다.",
      details: [
        "계약서 DOCX, 공고 첨부, 백업 ZIP처럼 파일 결과물을 받을 때 사용합니다.",
        "다운로드 전 파일 생성 상태가 completed/generated인지 확인합니다.",
        "민감 파일은 외부 공유 전에 내용과 권한을 확인해야 합니다.",
      ],
    },
  },
  {
    keys: ["복사"],
    guide: {
      title: "복사 버튼",
      summary: "표시된 URL이나 값을 클립보드에 복사합니다.",
      details: [
        "ngrok 공개 URL처럼 외부 사용자에게 전달할 값을 빠르게 복사할 수 있습니다.",
        "복사한 URL은 ngrok 세션이 바뀌면 더 이상 유효하지 않을 수 있습니다.",
        "API 키 전체 값 같은 민감정보는 화면에 노출하거나 복사하지 않는 것을 원칙으로 합니다.",
      ],
    },
  },
  {
    keys: ["백업", "백업 생성", "백업 검증", "복원 계획", "dry-run"],
    guide: {
      title: "백업/복원 버튼",
      summary: "서비스 데이터를 백업하거나 복원 전에 안전성을 검증합니다.",
      details: [
        "백업 생성은 DB 스냅샷과 저장 파일을 ZIP으로 묶습니다.",
        "백업 검증은 파일 구조와 manifest 오류를 확인합니다.",
        "복원 dry-run은 실제 복원 없이 어떤 작업이 수행될지 계획만 보여줍니다.",
      ],
    },
  },
  {
    keys: ["평가 실행"],
    guide: {
      title: "평가 실행 버튼",
      summary: "기준문서 RAG 검색 품질을 평가하기 위한 테스트 질의를 실행합니다.",
      details: [
        "입력한 평가 질의로 JSON 기준문서 인덱스를 검색합니다.",
        "검색 결과의 범위, 근거 후보, 누락 가능성을 확인합니다.",
        "기준문서 추출/청킹 로직 개선 전후 품질 비교에 사용합니다.",
      ],
    },
  },
  {
    keys: ["후보 추출"],
    guide: {
      title: "후보 추출 버튼",
      summary: "기준문서 청크에서 판단 규칙으로 쓸 수 있는 조건 후보를 추출합니다.",
      details: [
        "추출된 후보는 바로 확정되지 않고 검토 필요 상태로 저장됩니다.",
        "관리자가 문구와 근거를 확인한 뒤 승인해야 판단 근거로 사용됩니다.",
        "테이블이 많은 기준문서는 추출 품질을 별도로 확인해야 합니다.",
      ],
    },
  },
  {
    keys: ["요구조건 추출"],
    guide: {
      title: "요구조건 추출 버튼",
      summary: "저장 공고의 본문과 첨부에서 지원 요구조건 후보를 구조화합니다.",
      details: [
        "추출 결과는 부족조건 비교와 판단 실행의 입력값으로 사용됩니다.",
        "첨부가 없거나 지원 형식이 없으면 기존 정상 결과를 보존하는 흐름이 필요합니다.",
        "AI 결과는 운영자가 확인해야 하는 후보 데이터로 보는 것이 안전합니다.",
      ],
    },
  },
  {
    keys: ["비교", "판단 실행"],
    guide: {
      title: "비교/판단 실행 버튼",
      summary: "공고 요구조건과 법인 준비 상태, 기준문서 근거를 연결해 검토 결과를 만듭니다.",
      details: [
        "최종 결론을 단정하기보다 부족 조건과 필요한 준비 항목을 중심으로 보여줍니다.",
        "기준문서 근거가 없는 조건은 확정 근거로 쓰지 않는 것이 원칙입니다.",
        "결과는 관리자가 검토하고 메모를 남겨야 운영 흐름에서 안전하게 사용할 수 있습니다.",
      ],
    },
  },
  {
    keys: ["미리보기"],
    guide: {
      title: "미리보기 버튼",
      summary: "저장하거나 생성하기 전에 입력값으로 만들어질 결과를 먼저 확인합니다.",
      details: [
        "계약서나 비교 결과의 입력값 누락 여부를 사전에 확인할 수 있습니다.",
        "미리보기는 일반적으로 데이터를 확정 저장하지 않는 확인 작업입니다.",
        "내용이 맞으면 생성 또는 저장 버튼으로 실제 결과를 만듭니다.",
      ],
    },
  },
  {
    keys: ["연결 테스트", "테스트"],
    guide: {
      title: "연결 테스트 버튼",
      summary: "외부 API 키와 네트워크 응답 상태를 확인합니다.",
      details: [
        "나라장터 API나 AI 모델 키가 백엔드 환경변수에 제대로 설정되었는지 확인합니다.",
        "키 전체 값은 화면에 노출하지 않고 설정 여부와 테스트 결과만 보여줍니다.",
        "실패하면 `.env`, API 활용 신청 상태, 네트워크 연결을 순서대로 확인합니다.",
      ],
    },
  },
];

function normalizeLabel(value: string): string {
  return value.replace(/\s+/g, " ").replace(/[↕↑↓]/g, "").trim();
}

function findSectionTitle(element: HTMLElement): string {
  const card = element.closest(".surface-card, .spotlight-card, .callout-card, .project-card");
  const heading = card?.querySelector(".section-heading h3, h3, h2");
  return normalizeLabel(heading?.textContent || "");
}

function elementText(element: HTMLElement): string {
  return normalizeLabel(element.getAttribute("aria-label") || element.textContent || "");
}

function routeLabel(): string {
  const route = window.location.pathname;
  const guide = Object.entries(MENU_GUIDES)
    .sort((a, b) => b[0].length - a[0].length)
    .find(([path]) => route === path || route.startsWith(`${path}/`));
  return guide?.[1].title.replace(" 메뉴", "") || "현재 화면";
}

function explicitGuideFromElement(element: HTMLElement): HelpGuide | null {
  const title = element.dataset.helpTitle;
  const summary = element.dataset.helpSummary;
  if (!title && !summary) return null;

  const details = (element.dataset.helpDetails || "")
    .split("|")
    .map((item) => item.trim())
    .filter(Boolean);

  return {
    title: title || "도움말",
    summary: summary || "이 항목의 사용 목적을 설명합니다.",
    details: details.length ? details : ["현재 화면의 업무 흐름에 맞춰 이 버튼을 사용합니다."],
  };
}

function actionGuideFromElement(element: HTMLElement): HelpGuide {
  const explicit = explicitGuideFromElement(element);
  if (explicit) return explicit;

  const text = elementText(element);
  const section = findSectionTitle(element);
  const matched = ACTION_GUIDES.find(({ keys }) => keys.some((key) => text.includes(key)));

  if (matched) {
    return {
      ...matched.guide,
      summary: section ? `${section} 영역에서 ${matched.guide.summary}` : matched.guide.summary,
    };
  }

  return {
    title: text ? `${text} 버튼` : "액션 버튼",
    summary: `${routeLabel()} 화면에서 현재 선택값이나 입력값을 기준으로 작업을 실행합니다.`,
    details: [
      section ? `현재 버튼은 "${section}" 영역에 있습니다.` : "현재 화면의 업무 단계에 맞춰 실행되는 버튼입니다.",
      "버튼을 누르기 전 선택한 공고, 법인, 문서, 필터 조건이 맞는지 확인하세요.",
      "실행 후 실패 메시지가 나오면 작업 이력, 백엔드 로그, 해당 화면의 상태 배지를 함께 확인하세요.",
    ],
  };
}

export function getMenuHelpGuide(route: string | undefined, label: string, note: string): HelpGuide {
  if (route && MENU_GUIDES[route]) return MENU_GUIDES[route];
  return {
    title: `${label} 메뉴`,
    summary: note || "이 메뉴의 업무 목적과 사용 흐름을 안내합니다.",
    details: [
      "왼쪽 메뉴에서 선택하면 해당 업무 화면으로 이동합니다.",
      "화면 안의 입력값과 액션 버튼은 로컬 DB와 백엔드 API를 기준으로 동작합니다.",
      "작업 전후 상태 배지와 오류 메시지를 확인하면 다음 액션을 판단하기 쉽습니다.",
    ],
  };
}

function decorateActionButtons(showGuide: (guide: HelpGuide) => void) {
  const targets = document.querySelectorAll<HTMLElement>(
    [
      "button:not(.help-guide-trigger):not(.action-help-trigger):not([data-help-ignore='true'])",
      "a.link-button:not(.help-guide-trigger):not(.action-help-trigger):not([data-help-ignore='true'])",
    ].join(","),
  );

  targets.forEach((target) => {
    if (target.dataset.helpGuideDecorated === "true") return;
    if (target.closest(".help-guide-dialog")) return;
    if (!target.isConnected) return;

    const text = elementText(target);
    if (!text && !target.dataset.helpTitle) return;

    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "action-help-trigger";
    trigger.textContent = "?";
    trigger.setAttribute("aria-label", `${text || "액션"} 도움말 보기`);
    trigger.dataset.autoHelp = "true";
    trigger.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      showGuide(actionGuideFromElement(target));
    });

    target.dataset.helpGuideDecorated = "true";
    target.insertAdjacentElement("afterend", trigger);
  });
}

export function HelpGuideButton({ guide, compact = false }: { guide: HelpGuide; compact?: boolean }) {
  const context = useContext(HelpGuideContext);

  return (
    <button
      type="button"
      className={`help-guide-trigger${compact ? " help-guide-trigger--compact" : ""}`}
      aria-label={`${guide.title} 도움말 보기`}
      onClick={(event) => {
        event.preventDefault();
        event.stopPropagation();
        context?.showGuide(guide);
      }}
    >
      ?
    </button>
  );
}

export function ActionHelpProvider({ children }: { children: ReactNode }) {
  const [activeGuide, setActiveGuide] = useState<HelpGuide | null>(null);
  const contextValue = useMemo(() => ({ showGuide: setActiveGuide }), []);

  useEffect(() => {
    let frame = 0;
    const scheduleDecorate = () => {
      window.cancelAnimationFrame(frame);
      frame = window.requestAnimationFrame(() => decorateActionButtons(setActiveGuide));
    };

    scheduleDecorate();

    const observer = new MutationObserver(scheduleDecorate);
    observer.observe(document.body, { childList: true, subtree: true });

    return () => {
      window.cancelAnimationFrame(frame);
      observer.disconnect();
      document.querySelectorAll(".action-help-trigger[data-auto-help='true']").forEach((trigger) => trigger.remove());
      document.querySelectorAll<HTMLElement>("[data-help-guide-decorated='true']").forEach((target) => {
        delete target.dataset.helpGuideDecorated;
      });
    };
  }, []);

  return (
    <HelpGuideContext.Provider value={contextValue}>
      {children}
      {activeGuide ? (
        <div className="help-guide-backdrop" role="presentation" onClick={() => setActiveGuide(null)}>
          <section
            className="help-guide-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="help-guide-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="section-heading">
              <div>
                <p className="eyebrow">도움말</p>
                <h3 id="help-guide-title">{activeGuide.title}</h3>
              </div>
              <button type="button" className="help-guide-close" onClick={() => setActiveGuide(null)}>
                닫기
              </button>
            </div>
            <p className="help-guide-summary">{activeGuide.summary}</p>
            <ul className="help-guide-detail-list">
              {activeGuide.details.map((detail) => (
                <li key={detail}>{detail}</li>
              ))}
            </ul>
          </section>
        </div>
      ) : null}
    </HelpGuideContext.Provider>
  );
}
