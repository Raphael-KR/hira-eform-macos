# 구형 DDMD 연계 문서와 현재 설치본 대조

> '현재 설치본'은 2026-09 조사 대상이다. 현재 배포본 전체와의 호환성을 보장하지 않는다.
> 실행 준비 상태는 [DDMD README](../README.md), 후속 관측은 [히스토리](HISTORY.md)를 참조한다.

검사일: 2026-09-09. 판정: **문서에 기재된 주요 외부 명령의 구조는 현재도 존재한다. 전체 하위 호환성 및 무인 실행 성공은 미확인이다. DB 직접 연계에는 문서와 실제 스키마의 차이가 있다.**

## 대상과 문서 연도

- 설치본: `/private/tmp/hira-jvm-trial/hira-live-auth-update-gkcc7n7q/candidate` (이전 실제 업데이트 시험 후보).
- `/Users/<owner>/Downloads/download/webapi.exe API사용자 설명서.pdf`: 7쪽, 표지 Version 0.4 / 본문 0.2 혼재. PDF 생성·수정일 2014-08-05. 2014년 경로 예제도 포함.
- `/Users/<owner>/Downloads/download/진료비청구포털_청구SW업체_모듈연계 가이드.pdf`: 12쪽, PDF 생성·수정일 2020-12-28. Creator의 PowerPoint 2013은 소프트웨어 이름이며 개정 연도가 아니다.
- `/Users/<owner>/Downloads/download/웹서비스 API.pdf`: 3쪽, PDF 생성·수정일 2011-06-14.

PDF 메타데이터는 공식 개정일을 입증하지 않는다. 따라서 이번 결과를 정확히 ‘2013년 특정 판본과 대조 완료’라고 부를 수 없다. 제공된 세 파일과 설치본의 대조이다. 모든 문서 텍스트를 읽고, 주요 인자 예제(설명서 4쪽)와 스키마(모듈 가이드 6쪽)는 렌더링하여 직접 확인했다.

## webapi.exe 계약 대조

| 문서 항목 | 현재 구현 | 판정 |
|---|---|---|
| 공통: 명령명, 요양기호, 후속 인자 | WebCommandProcessor 생성자가 첫 두 토큰을 명령·요양기호로 사용 | 유지 |
| 인자 공백 구분, 목록 @@ 구분 | FileCommandParser의 String.split 및 각 명령의 @@ split | 유지 |
| send: 청구구분, 문서ID 목록 | 같은 순서로 SendWebController.send에 전달 | 구조 유지, 전송 미실행 |
| searchNtcList: 시작일, 종료일, 청구구분, 상태, 선택 본지원·보험구분 | 앞 네 인자 유지; 뒤 선택 인자 읽기는 예외를 허용. 추가 후속 인자 자리도 존재 | 기존 형식 수용 구조 확인, 실서버 응답 미검증 |
| receive: ID, 본지원, 청구구분, 상태의 네 목록 | 네 목록 각각 @@ 분리하여 ReceiveWebController.receive에 전달 | 구조 유지, 미실행 |
| deleteNtcList: ID, 청구구분, 본지원 목록 | 동일 순서의 세 목록 전달 | 구조 유지, 삭제 미실행 |
| generateNtc: ID 목록 | 동일 목록 전달, 반환 null은 공통 처리에서 [] | 구조 유지, 이번 미실행 |
| backupDec: 암호화 파일, 출력 경로 | backupFileDec(요양기호, 입력, 출력); 출력 경로 생략도 허용 | 문서 형식 수용 구조 확인 |
| JSON status=ok/result, err/reason, cancel | process에 같은 응답 구성과 취소 분기 존재 | 유지; 모든 값의 JSON 유효성은 별도 검증 필요 |
| 조회 결과 필드 | ntcDocId, ntcTtl, hbrCdName, arivDt, recpEndDt, statTxt, brokerStat, hbrCd, insuTpCd 존재 | 주요 필드 유지; 모든 필드 값·의미 일치 미확인 |

Launcher$5는 결과를 UTF-8로 쓰고 .end 파일을 생성한다. webapi.exe 파일은 최초 분석본과 동일 SHA-256이다. 다만 EXE 전체 제어 흐름, 기본 출력파일 선택, 공백 포함 경로 인용, 69/39건 제한, 종료코드, 동시 요청, 타임아웃의 런타임 호환 시험은 이번에 수행하지 않았다.

설명서 자체가 send.txt는 DB 처리 상태이고 SendResult.txt와 목록 재조회를 통해 청구 결과를 확인하라고 설명한다. generateNtc의 ok도 생성 결과 자체를 뜻하지 않는다고 명시한다. 따라서 API의 ok를 심평원 접수 완료로 해석하면 안 된다.

## 모듈과 DB

모듈 가이드의 ddmd, exam, examsnd, examerr, preexam, dmdsndui, log, ntcrcvui, ntcgenui, config, launcher, rcvchk.exe는 모두 현재 bin에 있다. 이는 파일 존재 확인이며 각 모듈 동작·반환 코드 검증은 아니다. 구형 문서의 jre 디렉터리와 달리 현재 배포본은 jre18을 포함한다.

TBJFA106은 읽기 전용 PRAGMA table_info로 조사했다. 데이터 행은 읽지 않았다.

| 항목 | 가이드 6쪽 | 현재 DB |
|---|---|---|
| 오류 일련번호 | ERR_SEQ | ERR_SNO (ERR_SEQ 없음) |
| 청구번호 선언 길이 | DMD_NO 10 | TEXT(12) |
| 주민번호 선언 길이 | PAT_JNO 14 | TEXT(20) |
| 컬럼 수 | 11 | 20 |

추가 컬럼: INSU_TP_CD, DOC_NM, EXM_CD, EXM_DT_CD, EXM_SNO, ERR_CMMT2, DMD_GUID, DMD_REF, DMD_YN. SQLite의 선언 길이가 저장 길이를 강제한다는 뜻은 아니다. ERR_SEQ 차이가 과거 오기인지 후속 변경인지는 과거 DB 없이 확정할 수 없다. 다만 구형 문서 그대로 ERR_SEQ를 SELECT하면 현재 DB에서 실패한다.

F000 SAM 서식의 모든 위치·길이와 현재 생성 결과의 대조, 설정별 실제 동작은 이번 미검증이다.

## 데이터센터 HTTP API

웹서비스 API 문서는 ddmdapi.hira.or.kr의 rct_ntc_reg_dt와 reg_org를 설명한다. 이는 로컬 webapi.exe와 별도 인터페이스이다. 클라이언트 설치본만으로 원격 서버의 현재 지원 여부·동작을 입증할 수 없어 유지 여부는 미확인이다. 이번에 해당 서버를 호출하지 않았다.

## 브로커 판단

공식 배포 문서에 나온 명령을 우선 사용하는 설계는 근거가 있다. 내부 Java 클래스를 임의 호출하는 것보다 문서화된 외부 경계를 중심으로 브로커를 구성할 수 있다. 다만 이번 정적 일치가 향후 호환성 보장이나 Windows 서비스 계정의 완전 headless 동작을 뜻하지 않는다.

DB는 실제 차이가 있으므로 구형 스키마를 그대로 고정하지 않는다. 업데이트 후 문서화된 비전송 명령의 인자·응답·완료파일을 격리 Windows 환경에서 확인하는 회귀 시험이 필요하다. 실청구·삭제 없이 가능한 범위부터 검증하고, 실제 SAM 전송 제외를 유지한다.

증거: `../gateway_poc/evidence/legacy-api-compare/`의 bytecode 출력과 evidence.json. 이번 작업은 파일·바이트코드·DB 스키마 읽기와 보고서 작성만 수행했다. 실행 중 DDMD에 명령 파일을 투입하지 않았고 인증·송신·수신·삭제·업데이트를 실행하지 않았다.
