# DDMD macOS 실제 업데이트 시험

2026-09-09 08:37–08:45 KST. macOS ARM64 Zulu Java 8u504.

## 결과

실제 HIRA 인증·업데이트 조회·파일 수신, 원본 Java 업데이트 적용 함수 실행,
macOS 앱 재실행과 서버 재조회까지 성공했다. 적용 후 추가 업데이트는 0개였다.
원본 Windows 자동 재시작과 서버의 업데이트 결과 보고 수락까지 검증한 것은 아니다.

| 단계 | 확인한 결과 |
|---|---|
| 인증·조회 | CLT_AUTH_REQ 후 CLT_MOD_UPT_REQ, 설치 모듈 154개 중 21개 제시 |
| 수신 | CLT_MOD_UPT 응답, 첨부 21개·14,574,849 bytes |
| 무결성 | 21개 모두 SHA-256 값 일치. 원본은 BigInteger.toString(16)으로 선행 0을 생략 |
| 적용 | 원본 UpdController.updateModules(UpdateDialog), 완료 로그 및 반환 확인 |
| 적용 후 검증 | release.xml의 21개 버전·파일 해시 일치, 기준자료 SQLite DB 11개 quick_check=ok |
| 재실행 | 별도 macOS APPL 실행기로 시작, Computer Use에서 본 화면·환경설정·서식 조회 창 확인 |
| 서버 재조회 | 적용 후 실제 파일 해시로 CLT_MOD_UPT_REQ, 추가 모듈 0개 |

## 환경과 보존

후보 경로: `/private/tmp/hira-jvm-trial/hira-live-auth-update-gkcc7n7q/candidate`

기존 성공 GUI 경로 `/private/tmp/hira-ddmd-ui-wtk92jjq`에 업데이트를 적용하지 않았다.
원본 신규 설치본을 별도 복사하고 합성 기관번호 00000000과 후보 전용 경로를 설정했다.
실제 기관번호와 인증서 자료는 기존 인증 도구를 통해 stdin으로만 전달했다.
후보 앱 ID는 `local.hira.ddmd.update-isolated`로 기존 앱과 구분된다.
실제 SAM 청구 및 통보 송수신 action은 수행하지 않았다.

수신 단계는 HIRA endpoint로 제한한 기존 headless 인증 경로를 사용했다.
적용·GUI 단계는 네트워크와 하위 프로세스를 차단하는 기존 Guard를 유지했다.
이는 OS 전체 샌드박스의 증명이 아니다.

## 시험 중 수정한 사항

1. 인증용 역직렬화 허용 목록에 업데이트 첨부 참조 클래스가 없었다.
   원본 AttachmentReference의 String/long 필드를 확인한 뒤 해당 클래스만 추가했다.
2. 이후 2,114,802 bytes에서 누적 스트림 1MB 제한이 확인됐다.
   업데이트 수신에만 256MB 제한을 적용했다. 배열 1MB·깊이 32·참조 10,000 제한은 유지했다.
3. 최초 모듈 목록 생성은 64자리 해시를 사용했으나 원본은 선행 0을 생략했다.
   그 결과 설치본과 동일한 파일 7개도 제시됐다. 모두 원본 숫자 표기로 대조하면
   해시가 일치한다. 후속 조회는 원본 표기로 생성했으며 추가 모듈 0개였다.

시험 초기 오류 증거는 filter-failure 및 size-failure 파일로 남겼다.
21개 수신을 21개 모두 새로운 변경이었다고 해석하지 않는다.
업데이트 대상에는 Windows EXE도 있었다. 복사본에 파일로 적용됐지만 실행하지 않았다.
DB 압축 해제는 원본 Java SevenZip 경로로 수행됐다.

## 남은 범위

- 원본 메뉴→인증→수신→적용→자동 재시작의 무인 단일 흐름은 미검증이다.
  이번에는 headless 조회/수신, 원본 적용 함수, macOS 실행기를 단계별로 연결했다.
- 원본 `ddmd.exe -update=false` 재시작 대신 macOS 앱을 도구로 실행했다.
- 후보 GUI 시작 중 업데이트 결과 보고가 시도됐으나 네트워크 차단 아래
  HttpConnection.open의 NPE가 기록됐다. 서버 보고 수락은 확인하지 못했다.
  서식 조회 인자 NPE 및 JIDE 형변환 오류와는 별개다.
- 후보에는 통보 시험 자료를 복사하지 않았고 서식 버튼들이 비활성 상태다.
  창 표시 성공이 개별 서식 처리 성공을 의미하지 않는다.
- 다음 업데이트에서 GUI·프로토콜·네이티브 의존성이 바뀔 수 있다.
  이번 버전의 성공을 모든 미래 업데이트 호환성으로 일반화하지 않는다.
- 서버 제공 체크섬과의 일치는 확인했으나 별도 코드 서명 신뢰 체인 검증은 수행하지 않았다.

## 근거

- [종합 결과](../gateway_poc/evidence/macos-update-summary.json)
- [최초 조회](../gateway_poc/evidence/macos-update-result.json)
- [수신 성공](../gateway_poc/evidence/macos-update-download-result.json)
- [첨부 검증](../gateway_poc/evidence/macos-update-files.json)
- [적용·DB 검증](../gateway_poc/evidence/macos-update-applied.json)
- [최종 서버 재조회](../gateway_poc/evidence/macos-update-postcheck-result.json)

실행 소스는 `gateway_poc/update/`에 있다. prepared.json과 modules.tsv 및 복사본에
의존하는 이번 시험용 도구이며 배포용 자동 업데이트 서비스가 아니다.

## 자동 실행기 후속 구현

이 문서의 단계별 수동 연결 이후, 한 번의 실행으로 수신·적용·macOS 앱 시작·서버 결과 응답·최종 조회까지 연결한 실행기를 검증했다. [구현 및 검증](ddmd-auto-update-plan.md)을 참조한다. 원본 GUI 버튼 및 OS 스케줄 연동은 여전히 별도 범위다.
