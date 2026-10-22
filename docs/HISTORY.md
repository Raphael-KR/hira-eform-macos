# 작업 히스토리와 실험 기록

정리 기준: 2026-09-09. 현재 사용법은 [README](../README.md), 앱 운영은
[메뉴 막대 앱](MENUBAR_APP.md), CLI 수집은 [CLI_COLLECTION](CLI_COLLECTION.md)을 따른다.
이 문서는 과거 관측을 모은 기록이지 서버 재접속·실험 재실행 지시가 아니다.
본문의 날짜·수치·성공 판정은 해당 시험 시점에만 적용된다.

## 현재 결론

| 영역 | 확인한 결과 | 남은 경계 |
|---|---|---|
| e-Form 브라우저 로그인 | 실제 인증서 로그인 사용자 확인 | `ef.hira.or.kr` 한정; 다른 사이트·인증기관 전체 보장 아님 |
| CLI 한방추나 조회 | Keychain 인증과 지정 진료일자 조회·로컬 저장 성공 기록 | 다중 페이지는 합성 시험; 실자료·건수는 비공개 |
| 메뉴 막대 앱 v1.0.0 | 사용자 동작 확인, 빌드·서명 검증, Applications 설치 확인 | 현재 프로젝트·Node 의존; 공증/독립 배포 아님 |

## e-Form 개발 이력

### 2026-10-23: AP-83 비운영 실행환경 점검

- 목표: 기존 Node/Python/Java 참조와 설치 상태를 대조하고 필요한 정비만 수행한다.
- 범위: 저장소 소스, 설치 의존성, 런타임 버전 및 과거 DDMD 경로의 존재 여부.
- 완료 조건: 설치 필요성, 관측 결과, 실행 exit와 미검증 범위를 기록한다.
- 제외: 외부 호출, 인증/Keychain/실데이터, GUI, 앱 실행·배포·재시작, 기존 환경 삭제.
- 검증: 의존성 import와 문법만 검사하며 합성 자료나 DB를 생성하지 않는다.

작업 전 `main...origin/main` working tree는 깨끗했다. 이번 정비는 문서만 변경했다.
Node/Python 재설치, 패키지 변경, Java 설치는 수행하지 않았다.

| 관측·명령 | 결과 | exit |
|---|---|---|
| `node`의 `process.execPath/version/arch` | `/opt/homebrew/Cellar/node/26.12.1/bin/node`, v26.12.1, arm64 | 0 |
| `npm --version` | 11.20.0 | 0 |
| `python3 -B`의 `sys.executable/version` | `/opt/homebrew/opt/python@3.15/bin/python3.15`, 3.15.0 | 0 |
| `npm ls --depth=0 --offline` | acorn 8.18.0, cheerio 1.0.0, iconv-lite 0.7.2, node-forge 1.4.0, tough-cookie 6.0.2, ws 8.21.3 | 0 |
| `node --input-type=module -e`에서 위 6개 의존성 import | 모두 성공; 서버 모듈은 import하지 않음 | 0 |
| Git 추적 Python의 `ast.parse`, JS/MJS/CJS의 `node --check` | Python 17개, JavaScript 40개 문법 통과; Python 파일 실행 없음 | 0 |
| `/usr/libexec/java_home -V` | 등록 Java 없음 | 1 |
| `stat`으로 `.local/ddmd`, `.local/ddmd/config.json`, 아래 과거 Java 경로 확인 | 세 경로 모두 없음 | 1 |
| 프로젝트 아래 java/javac/jdk/jre 이름 검색 | 일치 경로 없음 | 0 |

앞선 점검의 Python 3.14.9와 이번 `python3` 3.15.0 관측은 다르다.
이번 작업에서는 PATH·Python 설치를 변경하지 않았으며 변경 원인은 미확인이다.

DDMD 실행기는 `config.json`의 `java` 절대 경로를 사용하므로 `java_home` 결과만으로
전용 JVM 부재를 판단하지 않았다. 과거 소스의
`/private/tmp/hira-jvm-trial/zulu8.96.0.205-ca-jdk8.0.504-macosx_aarch64/Contents/Home/bin/java`
도 존재하지 않는다. 별도 위치의 JVM 전체 부재를 뜻하지는 않는다.
현재 DDMD는 실행 가능한 배포판이 아니며, 최신 설치본으로 재개하려는 기존 결정에 따라
구형 JVM만 임의 복구하지 않았다. 재개 시 최신 설치본과 호환 JVM·로컬 설정이 필요하다.

Node는 package.json의 `>=20` 범위를 충족하지만 CI 행렬은 20/22/24다.
이번 문법·import 검사는 Node 26의 로그인/전체 기능 호환성을 보증하지 않는다.
앱 빌더는 Node의 realpath를 Runtime.json에 고정한다. 후속 읽기 전용 확인에서
`/Applications/HIRA e-Form.app/Contents/Resources/Runtime.json`을 읽었다(exit 0).
설치 앱의 `nodeExecutable`은 `/opt/homebrew/Cellar/node/26.6.0/bin/node`이며,
`ls -l`은 파일 없음(exit 1), 해당 경로의 `--version`은 파일 없음(exit 127)이었다.
파일이 없으므로 실행 가능하지 않다. 반면 현재 CLI Node 경로는
`/opt/homebrew/Cellar/node/26.12.1/bin/node`, v26.12.1(exit 0)이다.
따라서 설치 앱의 고정 Node 경로는 현재 유효하지 않다. 앱 자체는 실행하지 않았다.
보완 대상은 설치 앱의 Runtime.json의 nodeExecutable 또는 현재 Node로 재빌드한 앱이다.
보완하면 앱이 사용하는 Node 버전이 바뀌므로 별도 배포 범위에서 적용·검증해야 한다.
이번에는 설치 메타정보를 변경하거나 앱을 재빌드·재설치·재시작하지 않았다.
전체 테스트·앱 빌드·DDMD 실행·운영 smoke는 수행하지 않았다.
소스, lockfile, 로컬 자료, 인증 설정과 기존 운영 프로세스는 변경하지 않았다.
공통 정비 PLAN/inventory, MSL·Telegram, Git 원격 상태도 변경하지 않았다.

### 2026-10-23: AP-84 설치 앱 Node 경로 보완

사용자 승인 메시지 `01a16517-6125-76a3-a069-c6e13d2b8849`에 따라
`/Applications/HIRA e-Form.app` 복사본의 Runtime.json에서 nodeExecutable만
26.6.0에서 `/opt/homebrew/Cellar/node/26.12.1/bin/node`로 수정했다.
projectDirectory는 그대로 유지했다. Swift 재컴파일은 하지 않았다.

원본은 저장소의 `.local/app-maintenance/AP84-20261023/HIRA e-Form.original.app`에
이동하여 보존했다. 후보는 같은 폴더의 `HIRA e-Form.candidate.app`이다.
원본 및 후보를 삭제하거나 롤백하지 않았다. 작업 전 `pgrep -x HiraEForm`은
exit 1로 실행 중 앱이 없었으므로 종료도 하지 않았다.

- 원본 `codesign --verify --strict`: 보존 전·후 exit 0.
- 후보 `ditto`, `codesign --force --sign -`, `codesign --verify --strict`: 각각 exit 0.
- 원본 이동 `mv`, 후보의 Applications 설치 `ditto`: 각각 exit 0.
- 설치 앱 `codesign --verify --strict`, `codesign -d --verbose=4 -r-`: 각각 exit 0.
- 후보와 설치 앱 `diff -rq`: exit 0. 원본과 후보는 exit 1이며 변경은
  Runtime.json, CodeResources, 내장 서명이 변경된 Mach-O 실행파일 3개뿐이다.
- 설치 Runtime.json 재조회 exit 0, 지정 Node의 `--version`은 v26.12.1, exit 0.
- 전후 Identifier는 `kr.raphael.hira-eform-macos`, 서명은 ad-hoc, Team ID는 없음.
- 원본 CDHash: `3937f5f2c00ce2b557b179250b93b6703b865e77`.
- 설치 CDHash: `6eed3576fe1f699586b9a6fb46cad5cbc72817f7`.
- 전후 designated requirement는 각각 해당 CDHash를 사용하는 `cdhash H"..."`이다.

설치·서명·Node 실행 경로 확인만 완료했다. 앱 실행, 로그인, 실서버 연결,
Keychain/TCC 조작이나 권한 재승인 관측은 하지 않았다. 신원 변경에 따른 실제
권한 재승인 필요 여부와 인증/업무 성공은 미검증이다. 공통 Node·DDMD·다른 운영 환경,
기존 미커밋 문서는 보존했고 Git push/merge는 하지 않았다.

### 2026-04: Node.js 호환성 PoC

Windows 로컬 에이전트와 사이트 JavaScript의 통신을 관찰하고 Node.js로 재현했다.
검증 전 Rust/Swift로 암호 계층을 다시 작성하지 않고, node-forge와 SEED-CBC를
사용하는 경로를 먼저 검증했다. 아래는 관측과 수정의 대응 관계다.

| 증상·가설 | 확인·수정 | 결과·한계 |
|---|---|---|
| SEED-CBC 미지원 | forge에 SEED 구현 등록, RFC 4269 벡터 대조 | 합성 암호 시험 성공; 그 자체는 서버 로그인 증거 아님 |
| 간헐적 JSON 파싱 오류 | 랜덤 keyId 안의 `{` 검색을 없애고 고정 16바이트 처리 | 평문 프레이밍 안정화 |
| PKI 버전업 안내 | `0open`에 보낸 `{}`를 클라이언트가 설치 응답으로 처리 | hello 무응답으로 수정; 팝업은 반드시 버전 불일치를 뜻하지 않음 |
| PubKey 형식 의심 | Windows와 같은 raw RSAPublicKey DER 사용 | 클라이언트는 SPKI도 파싱 가능; 이것만을 팝업 원인으로 확정하지 않음 |
| SSO 설치 안내 | 별도 39091 HTTPS stub 추가 | `INIT1`, `UPDATE00`이 성공; `UPDATE01`은 업데이트 필요 |
| 인증서 목록 TypeError | `CertList[]`, `CertStatus[]` 응답과 항목별 UTF-8/base64 직렬화 | 인증서 선택 창 진입 |
| 빈 인증서 목록 | 줄바꿈이 들어간 환경변수 대신 표준 NPKI 경로 탐색 | 인증서 로딩 확인 |
| 한글 소유자명 깨짐 | forge DN byte-string을 Unicode로 해석 후 직렬화 | 한글 표시 사용자 확인 |
| 비밀번호 복호화 실패 | `Password` JSON의 `Data`를 추출 | 래퍼 전체를 KDF 입력으로 쓰던 오류 수정 |
| PBES1 복호화/ASN.1 실패 | IV를 SHA1(dk의 마지막 4바이트)의 앞 16바이트로 수정 | 실제 RSA 키 로딩 가능 |
| 서명 후 로그인 오류 `[8]` | signedAttrs 없음, CP949 DN, SHA-256/RSA 형태를 적용 | 실제 로그인 사용자 확인. 세 변경 각각의 필요성을 분리 입증한 것은 아님 |
| 틀린 암호가 버전업/알 수 없는 오류로 표시 | 패딩 실패와 복호화 후 ASN.1 실패를 BadPasswordError로 분류, 암호화된 Status 0x6008 응답 | 사용자 반복 오입력에서 `[24584]` 안내 확인 |
| 서버 재시작 뒤 기존 팝업으로 서명 | 서버의 세션 키가 소실된 상태에서 기존 암호문 도착 | 팝업을 닫고 페이지를 새로 열어 handshake 필요 |

실제 CMS·인증서 정보·암호를 문서에 넣지 않도록 공개용 예시로 치환했다.
암호를 argv로 받던 진단 방식은 폐기했고, CMS dump는 재사용 가능한 민감 인증
산출물로 취급한다. 서버가 실제 재사용 요청을 언제 허용하는지까지 검증했다는 뜻은 아니다.

### 2026-09-08: CLI 로그인과 수집

브라우저 자동화와 별개로 Node HTTP + cookie jar로 e-Form/외부 SSO 폼을 처리했다.
Cheerio는 HTML 폼을 읽고, Acorn은 허용된 리다이렉트 리터럴을 실행 없이 파싱한다.
Nexacro SSV의 구분자·null·성공 응답 생략 규약을 실제 클라이언트와 대조했다.
인증 기관·메뉴 `EF05010002`를 확인하고, 진료일자·페이지·건수·중복을 검증한다.

Keychain 입력 도우미, private pipe, 최소 필드 출력, 사용자 전용 파일 권한,
공개 파일 allowlist와 합성 회귀 검사를 추가했다. 실제 기간·환자·기관·건수는
로컬 결과에만 남긴다. curl 실패와 Node fetch 성공의 차이는 관측했지만
curl 실패 원인을 확정하지 않았다. [HTTP 계약과 검증 범위](CLI_COLLECTION.md).

### 2026-09-09: 메뉴 막대 앱과 v1.0

| 단계 | 결정·결과 |
|---|---|
| 초기 앱 | Swift/AppKit NSStatusItem + 기존 Node 자식 프로세스. 소유한 서버만 제어 |
| 상태 표시 | stdout heartbeat로 두 리스너 준비 확인; 부모 stdin pipe 종료 시 자식 종료 |
| 사용자 시험 | 사용자가 직접 실행 후 정상 동작 확인. AI는 GUI를 직접 시험하지 않음 |
| 메뉴 단순화 | 상태 아이콘 제거, `eF`만 표시. 회색/녹색/빨간색 시스템 색상 적용 |
| 명령 단순화 | 시작·중지 중 하나만 표시, 처리 중 비활성화, 재시작 항목 제거 |
| 아이콘 | 문서+자물쇠 초안에서 파란 문서와 `e-form` 독자 디자인으로 교체 |
| 버전·설치 | package와 앱 버전 1.0.0, `/Applications/HIRA e-Form.app` 설치·서명·경로 확인 |

합성 TLS/임시 포트로 시작·EOF 종료·다시 시작·기존 포트 충돌 보존·TLS 부재를
시험했다. Swift 빌드와 ad-hoc 서명은 확인했으나 다른 macOS 버전·VoiceOver·공증은
미검증이다. `iconutil`은 샌드박스에서 Invalid Iconset, 허용된 로컬 실행에서 성공했다.
기존 브라우저 에이전트의 암호 처리를 Swift로 포팅하지 않았다.

## 문서 정리 (2026-09-09)

이 문서는 e-Form 로그인·CLI 수집·메뉴 막대 앱의 작업 이력만 다룬다.
DDMD 연구는 [별도 폴더의 README](../ddmd/README.md)와
[DDMD 실험 히스토리](../ddmd/docs/HISTORY.md)로 분리했다.

공개용 CMS 예시는 [SIGN_FLOW](SIGN_FLOW.md#cms-example)로 합치고
중복 파일 `docs/reference-cms.txt`를 제거했다. 실제 구현에 맞춰 PubKey DER 형식,
요청/응답 프레이밍, SSO stub의 역할을 수정했다. CMS 예시의 잘못된 한글 바이트와
OID 수용 범위에 대한 미입증 단정도 제거했다.

현재 사용법은 README와 앱·CLI 가이드가 맡고, 공개 검토 절차는 RELEASE에 둔다.
기존 문서 전체 사본과 SHA-256 목록은 Git에서 제외되는 로컬 `tmp/`에 보관했다.
실제 인증서·암호·조회 결과·캡처, 실행 코드와 설치된 앱은 이 정리에서 변경하지 않았다.
