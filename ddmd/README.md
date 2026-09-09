# DDMD macOS 연구

이 폴더는 DDMD의 Java 인증·통보 처리·업데이트·격리 GUI를 조사한 **별도 연구 영역**이다.
[e-Form 로그인 및 메뉴 막대 앱](../README.md)과 실행 경로·검증 범위가 다르다.
둘의 성공 판정을 서로 대신 사용하지 않는다.

## 현재 상태

2026-09-09 시험 종료 후 외부 JVM과 임시 실행 환경을 제거했다.
**현재 GUI·실서버 업데이트를 바로 실행할 수 있는 배포판이 아니다.**
소스와 비공개 로컬 데이터는 보존했다. 실제 SAM 청구 전송은 시험에서 제외했다.

macOS JVM에서 실제 인증·통보 로컬 처리·업데이트 흐름을 검증한 기록은 있으나,
CA 신뢰/폐지 검증, 원본 DDMD 전체 기능과 실제 청구 접수까지 완료한 것은 아니다.
초기 실패, 후속 수정, 최종 환경 정리를 [실험 히스토리](docs/HISTORY.md)에 함께 기록했다.

## 문서 안내

| 문서 | 역할 |
|---|---|
| [작업 히스토리와 실험](docs/HISTORY.md) | 단계별 결과 요약과 12개 원기록과 폐기 경로 요약 |
| [Windows 설치본 분석](docs/ddmd-integration-analysis.md) | 정적 구조·명령·암호/세션 계약 |
| [구형 API 대조](docs/ddmd-legacy-api-compatibility.md) | 공식 자료와 설치본 스키마 차이 |
| [SAM 시험 경계](docs/ddmd-sam-test-boundary.md) | 사전점검·시험 권한·실제 전송의 구분 |
| [biz 사이트맵](docs/biz-hira-sitemap.md) | 비로그인 메뉴 구조·ID |
| [코드와 진단 도구](gateway_poc/README.md) | 디렉터리별 역할과 과거 실행 경로 주의 |
| [자동 업데이트 실행기](gateway_poc/auto-update/README.md) | 준비 조건·적용 순서·실패/복구 계약 |

과거 보고서에 흩어진 표·실패·수치는 히스토리에서 보존한다.
문서의 evidence 경로는 로컬 자료 위치를 설명할 뿐 공개 파일 링크가 아니다.

## 폴더와 비공개 자료

| 대상 | 위치 | Git |
|---|---|---|
| 개발 소스·어댑터·진단 도구 | `ddmd/gateway_poc/` | 포함 |
| 현재 안내·실험 이력·정적 참고 | `ddmd/docs/` 및 이 README | 포함 |
| 활성 버전·프로그램 파일·기관 설정·DB | 저장소 루트의 `.local/ddmd/` | 제외 |
| 인증서·암호 | 사용자 NPKI·macOS Keychain | 제외 |
| 통보 파일·원본 로그·검증 상세 자료 | 로컬 전용 폴더 | 제외 |
| JVM·제공사 설치본 | 별도 준비 | 제외 |

## 재개 조건과 실행 영향

재개하려면 호환 JVM과 사용 권한이 있는 DDMD 설치본을 준비하고,
`.local/ddmd/config.json`의 `java`와 `source` 절대 경로를 확인한다.
`institution.txt`는 기관번호 한 줄, 권한 0600으로 보관한다.
`active.json`은 활성 실행 대상을 가리킨다. 이 설정·데이터는 Git에 없다.

준비와 실서버/GUI 실행 승인이 끝난 뒤에만 저장소 루트에서
`npm run ddmd:update`를 사용한다. 인증·조회·다운로드·후보 적용·앱 시작·서버 결과 보고를
수행하므로 읽기 전용 검사가 아니다. 최신이면 적용/재시작/보고 없이 종료한다.
원본 GUI 업데이트 버튼·OS 주기 실행에는 연결하지 않았다.
자세한 순서와 실패 처리는 [실행기 가이드](gateway_poc/auto-update/README.md)를 따른다.

## 코드 검증

저장소 루트에서 `npm run test:ddmd`로 업데이트 안전/실패 경로의 합성 검사를,
`npm run check:release`로 공개 후보 검사를 수행한다.
합성 검사 통과는 삭제된 JVM 복구나 실제 SAM·GUI 검증을 뜻하지 않는다.
