# 격리 macOS JVM 설치

- Goal: DDMD 후속 시험용 macOS ARM64 Java 8을 별도 폴더에 설치한다.
- Boundary: `/private/tmp/hira-jvm-trial`에 공식 TAR.GZ를 풀어 사용한다.
- Done: checksum, java/javac 버전, ARM64 및 합성 stdin/headless 실행 확인.
- Non-goals: 시스템 JVM 등록, PATH/JAVA_HOME 전역 변경, 실제 인증 및 SAM 요청.
- Verification: 2026-09-09 Java/Javac 1.8.0_504 실행 성공. 합성 stdin/headless smoke PASS. `java_home -V`는 계속 시스템 런타임 없음으로 반환.

Java home: `/private/tmp/hira-jvm-trial/zulu8.96.0.205-ca-jdk8.0.504-macosx_aarch64/Contents/Home`

배포: Azul Zulu 8.96.0.205-CA, macOS aarch64 JDK 8u504.
출처: https://cdn.azul.com/zulu/bin/zulu8.96.0.205-ca-jdk8.0.504-macosx_aarch64.tar.gz
공식 metadata UUID: `16811ca3-e48b-459d-abc4-f6b273023a54`
공식 및 다운로드 SHA256 일치: `58bb3c08f2aa63d9743cf31899fa4b8c6c9effefce9479e7288c26621c3bb21b`

설치 방식은 Azul 공식 macOS TAR.GZ 안내를 따른다: https://docs.azul.com/core/install/macos

Wine 폴더와 별개다. 보안 sandbox가 아닌 설치 경로 분리이며, 임시 폴더이므로 OS 정리에 의해 삭제될 수 있다. 인증정보를 사용하지 않았다. DDMD JAR 오프라인/실제 인증 검증은 아직 수행하지 않았다.

## DDMD 인증 검증 계획

- Goal: 네이티브 macOS JVM에서 DDMD 라이브러리로 실제 AuthToken 발급을 확인한다.
- Boundary: 원본 인증용 JAR 14개, 기존 Keychain 인증정보 로더, 인증 전용 CLT_AUTH_REQ 한 건. 기관 번호는 기존 Windows 설정에서 읽기만 한다.
- Done: 오프라인 17개 검사와 Node 교차 복호화, 실제 서버 AuthToken 존재·미만료 확인.
- Non-goals: Wine/GUI 실행, SAM·청구·통보, 비밀정보 파일 저장.
- Verification: 소스·라이브러리 해시 검증, 제한된 결과 로그, 시험 종료 후 임시 payload 확인.

오프라인 검사 17개 및 Node 교차 복호화 통과. 실행부는 Windows 경로를 시험 폴더 경로로 변경하고 기관 번호를 stdin으로 받는다. Wine 전용 입력 래퍼는 제거했다. 실제 개인키·비밀번호는 JVM에 전달하지 않는다.

## 2026-09-09 실제 인증 성공

**03:25:41–03:25:42 KST, macOS ARM64 Zulu Java 8u504에서 실제 HIRA 인증 성공. Wine 및 Windows JVM 없이 실행했다.**

- `CLT_AUTH_REQ` 한 건, 실제 응답 `hira.ddmd.jmc.agent.auth.AuthToken` 수신.
- tokenId 존재, 미만료 확인. 토큰 값·키·인증서 정보는 출력하지 않았다.
- `RESULT GATEWAY_PASS mode=auth headless=true requests=1`, exit 0, stderr 0 bytes.
- 원본 DDMD의 14개 JAR 사용. GUI, 추가 native 로딩, 다른 endpoint 및 프로세스 실행 차단 유지.
- macOS 기본 JRE의 `NetworkInterface` 지연 초기화가 최초 시도의 guard에 걸렸다. 실제 인증정보 없는 SocketProbe로 원인을 재현한 후 guard 설치 전에 기본 JRE 모듈을 초기화해 해결했다. 최초 시도는 send 함수 진입 1회지만 `connectChecks=0`이며 서버에 전달된 인증 요청으로 세지 않는다.
- 최종 실행부 SHA256: `9e2577df5a4c9002ca0fe02479a53fa912ecf4b30e583c025150f5947ab9a966`.
- Java 프로세스 정상 종료. parts/javatmp 파일 0개, crash 파일 0개, 14개 JAR 해시 유지. macos_agent clean 상태 유지.
- 기관 번호는 Windows DDMD 설정에서 SSH로 읽었지만 인증·암호화·HIRA 통신은 전부 Mac에서 실행했다. Windows 연결을 완전히 제거하려면 기관 번호 공급 설정을 Mac 쪽에 마련해야 한다.
- SAM·청구·통보 요청은 하지 않았다. 만료 후 재발급·통보 수신·전체 DDMD 호환성은 이번 검증 범위가 아니다.

증거: `../evidence/macos-offline-probe.txt`, `macos-node-interop.txt`, `macos-live-auth-result.json`, `macos-live-postcheck.json`. 초기 실패는 `macos-live-auth-initialization-failure.json`에 별도 보존한다.

재현 순서: `python3 gateway_poc/macos-jvm/offline.py`, `python3 gateway_poc/macos-jvm/prepare-live.py`, `node gateway_poc/macos-jvm/run-auth.mjs`. 마지막 명령은 실제 인증정보와 인증 서버를 사용하므로 인증 전용 승인 범위 안에서만 실행한다.

## 2026-09-09 SAM 전송 제외 확대 검증

사용자가 실제 SAM 전송 외 검증을 승인했다. 실제 호출 action은 인증 `CLT_AUTH_REQ`, 공개 수신처 인증서 `CLT_CERT_REQ`, 오늘 날짜 통보 목록 `CLT_NTC_LIST_REQ`로 제한했다. 통보 상태 변경 `CLT_NTC_UPT_REQ`, 문서 다운로드·삭제·청구는 호출하지 않았다.

### 실서버 실행 결과

| 항목 | 결과 | 증거 |
|---|---|---|
| 실제 토큰 만료 후 재인증 | 03:28:27–03:33:27 KST, 약 5분 대기 후 만료 관찰, 새 tokenId와 늦어진 만료시각 확인 | `macos-lifecycle-result.json` |
| 공개 수신처 인증서 | 1건, 토큰 헤더/MAC 및 응답 토큰 처리 성공, 첨부 0개 | `macos-recipient-result.json` |
| 통보 목록 | 2026-09-09 당일, 건강보험·실청구 분류의 조회 응답 성공, 0건, 첨부 0개 | `macos-notice-list-result.json` |
| 로컬 오류 처리 | 인증 성공 후 비정상 직렬화 응답과 로컬 연결 차단 예외 처리, 기존 토큰 보존 | `macos-failure-tests-result.json` |

통보 조회 0건은 해당 조건에만 적용되며 전체 기간의 사서함이 비었다는 뜻이 아니다. 실제 통보 다운로드·복호화·수신확인까지 검증한 결과가 아니다. 목록 조회와 상태 변경 action의 분리는 설치본 ReceiveController 바이트코드로 확인했다. 서버 내부 부수 효과는 직접 관측하지 않았다. failure-tests의 requests=2는 send 함수 진입 횟수이며 두 번째는 로컬에서 차단되어 전송되지 않았다. 운영 서버에 잘못된 비밀번호·인증서·변조 토큰을 보내지 않았다.

### 합성 파일·암호 검사

기존 17개에 바이너리 CMS 서명·검증, 파일 암호화·복호화, 변조 검출, 추가 native/GUI/network 없음, DDMD 메시지+첨부 서명 생성을 추가해 **22개 검사 통과**. 65,537바이트 합성 바이너리를 사용했으며 실제 SAM 형식/환자 데이터가 아니다. 원본 JCAOS SignedDataCipher는 서명용 객체와 검증용 객체의 상태가 달라 각각 생성해야 한다.

파일 CMS 및 DDMD 메시지 CMS를 OpenSSL로 독립 검증했다. 파일 CMS의 복원 바이트는 원본과 동일했다. 메시지 CMS의 OpenSSL 성공은 외부 서명의 수학적 검증이며 DDMD 메시지 내부 첨부 참조 규약이나 HIRA 서버 수용까지 증명하지 않는다.

**별도 미해결:** `DdmdMessageSignatureImpl.verify`는 자신이 생성한 서명을 처리할 때 `DdmdContents.getInstance`에서 `IllegalArgumentException: unknown object in getInstance : class [B` → DDMD 8174 오류를 냈다. 이 검증을 통과한 것으로 세지 않는다. 원본 JAR는 수정하지 않았다. 통보 복호화는 합성 파일 왕복 수준까지 검증됐고 실제 통보 payload는 사용하지 않았다.

### 점검 실행 경계

`BoundaryProbe`를 빈 시험 폴더, headless, 네트워크·프로세스 실행 차단 아래 실행했다.

- 원본 SQLite JDBC의 메모리 DB 연결 및 SELECT 성공. 원본 드라이버가 무조건 Windows 전용이라는 가정은 맞지 않았다.
- Launcher 정적 초기화: `HeadlessException`, Launcher.java:112.
- CExamController 초기화: DocCipherController → ClientContext 의존성에서 ApplicationClassLoader의 package signer 불일치 `SecurityException`. 모든 설치 JAR를 평면 classpath로 넣는 방식의 한계이며 점검 알고리즘 자체가 Mac에서 불가능하다는 판정이 아니다.
- CExamChineseSpec091 클래스 초기화 성공. 실제 파일 파싱·검사 성공을 뜻하지 않는다.
- 완전한 SAM+MEDLOG 시험 묶음이 없고 현재 점검 진입부도 막혀 있어 실제 SAM 점검, 등록, 결과 파일 생성은 완료하지 못했다. 운영 SAM/DB를 대신 가져와 사용하지 않았다.

따라서 **Mac 인증·토큰 수명 관리·조회·파일 암호 기반은 실증됐지만 전체 SAM gateway 검증은 미완료**다. 다음 남은 단위는 원본 클래스 로더 구조를 보존한 점검 엔진 분리와 검증 가능한 합성 SAM 묶음 준비, 메시지 검증 파서 호환성 확인이다. 통보 다운로드에는 대상 문서와 수신 상태 변경 계약 확인이 필요하다.

실행: `python3 gateway_poc/macos-jvm/prepare-live.py` 후 `node gateway_poc/macos-jvm/run.mjs lifecycle|recipient|failure-tests|notice-list` 중 하나. 목록 범위는 코드에서 당일로 고정되어 있다. `sam` 등 허용하지 않은 명령은 인증정보 접근 전에 거부한다.

증거는 `gateway_poc/evidence/`의 위 JSON 및 `macos-offline-probe.txt`, `macos-node-interop.txt`, `macos-file-crypto.json`, `macos-boundary.txt`에 보관한다. 실제 개인정보·토큰·키는 출력/저장하지 않았다. 합성 fixture의 테스트 키는 시험 임시 폴더에만 있다.

## 실제 통보 다운로드 계획

사용자가 실제 통보 다운로드를 명시 승인했다. 최근 90일 건강보험 실청구 통보 목록에서 12건을 확인했고, 가장 최근 문서 한 건을 선택한다. 실제 호출은 인증, 목록, `CLT_NTC_REQ`이며 `km_cert`에 사용자 암호화 공개 인증서를 전달한다. 삭제·별도 상태 변경 요청 및 SAM 송신은 포함하지 않는다. 다운로드 자체의 서버 수신 이력 변화는 가능하며 서버 내부 동작은 관측하지 못한다.

파일은 `gateway_poc/private-downloads/notice-*`의 사용자 전용 폴더(0700)에 일반화한 파일명(0600)으로 저장한다. 원문·기관/환자 식별자·토큰·키는 보고서에 남기지 않는다. 완료 조건은 실제 응답 첨부 파일 확보와 크기 확인이며, 복호화·서명 검증 여부는 별도로 명시한다. 기존 메시지 검증 파서 문제를 무시하고 검증 완료로 표시하지 않는다.

### 실제 다운로드 결과 (2026-09-09 03:38–03:39 KST)

**실제 통보 한 건의 암호화 본문과 서명 파일을 Mac에 확보했다.** 최근 90일 조회 결과 12건 중 BrokerRcvDT가 가장 최근인 한 건을 선택했다. 인증→목록→`CLT_NTC_REQ` 각 1회, 총 3회 호출했다. 서버는 `NtcDoc`과 2개 첨부 payload를 반환했다.

JVM 실행은 응답 수신 후 로컬 파일 저장 과정에서 ExceptionInInitializerError/SecurityException으로 종료되어 `macos-download-result.json`의 passed는 false다. 이 실패를 서버 다운로드 실패와 동일시하지 않는다. 수신 registry에 남은 2개 payload를 Python으로 별도 복사했고 바이트 일치·해시·권한을 확인했다. `.ref` 2개는 transport 내부 메타데이터로 분리하고 사용자용 파일에는 포함하지 않았다. 다운로드 재요청은 보내지 않았다. 저장 실패의 구체 원인은 확정하지 않았으며 진단 stage 표기만 세분화했다.

보관 위치: `/Users/<owner>/Playground/HIRA_eform_login/gateway_poc/private-downloads/notice-xcDjRX`

- `encrypted-notice.cms`: 1,213 bytes, CMS envelopedData.
- `signature.cms`: 2,044 bytes, CMS signedData.
- 폴더 권한 0700, 파일 권한 0600. 파일 이름에 문서 식별자·기관 번호를 넣지 않았다.
- **복호화 및 서명 검증은 아직 수행하지 않았다.** 정상 문서 내용 또는 진료비 결과를 확인했다고 해석하지 않는다.
- 서버의 수신 상태 변화는 별도로 조회/검증하지 않았다. 별도 수신확인·삭제·상태변경 action 및 SAM 송신은 호출하지 않았다.

최종 파일 확보 증거: `gateway_poc/evidence/macos-download-recovered.json`. 최초 실행 결과는 `macos-download-result.json`으로 보존한다. 실제 파일과 원본 수신 registry는 비공개 로컬 자료이며 커밋/외부 공유 대상이 아니다.

## 실제 통보 복호화·서명 검증 (2026-09-09)

사용자가 명시 승인한 로컬 파일만 처리했으며 서버 재요청 없이 완료했다.

- 기존 다운로드 SHA256 대조 성공.
- OpenSSL CMS 수학적 서명 검증 성공. `-noverify`는 서명 수학 검증과 서명자 신뢰 체인 검증을 분리하기 위해 사용했다.
- 서명된 DDMD manifest를 ASN.1로 파싱하고 유일한 첨부 SHA-256이 실제 `encrypted-notice.cms`와 일치함을 확인했다. 기존 Java 검증기의 byte[] 파싱 오류를 원본 JAR 변경 없이 별도 검증으로 대체했다.
- 실제 kmCert/kmPri 쌍과 Keychain 비밀번호로 RSA 키 일치 및 CMS 수신자 serial 일치 확인 후 RSA/SEED-CBC 복호화 성공. 비밀번호·개인키는 메모리에만 사용했다.
- 결과는 762바이트 ZIP이며 ZIP CRC/구조 검사 통과. 내용은 출력하지 않았다. `private-downloads/notice-xcDjRX/decrypted-notice.zip`에 0600 권한으로 보관했다.
- 서명자 인증서는 현재 유효기간 내이며 설치본 암호화용 center key와 다르다. 이는 서명과 암호화 인증서가 별개일 수 있어 자체로 위조 판정 근거가 아니다.
- **서명자 신뢰 체인은 미확인:** macOS 로컬 저장소만 사용하는 `security verify-cert -p basic -L`은 `CSSMERR_TP_NOT_TRUSTED`를 반환했다. CA 체인/신뢰앵커 및 폐지 여부를 확인하지 않았으므로 HIRA 발신자 신원까지 검증 완료로 표현하지 않는다.
- 결론: 복호화, CMS 수학적 서명, 서명된 파일 해시, ZIP 무결성은 통과. 발신자 인증서 신뢰 검증은 별도 미완료다.

실행부: `verify-notice.mjs`. 증거: `gateway_poc/evidence/macos-notice-verification.json`. 실행부는 덮어쓰기 방지를 위해 신규 출력만 허용한다. 최종 배포 파일은 형식 확인 후 `.zip` 확장자로 변경했다.

## 복호화 ZIP의 DDMD 처리 호환성

실제 ZIP에는 `.1`, `.2`, `.3` 파일 3개(각 3,528 / 68 / 0 bytes)가 있다. 식별자가 포함될 수 있는 원본 파일명과 내용은 보고서에 출력하지 않았다.

원본 `ReceiveController.doOnSucceeded`는 복호화 결과를 문서별 `zip` 경로에 저장하고 `ResultDocument`를 구성한다. 자동 생성 설정에 따라 `zipReleaseCont`가 `Commons.decompress(File, File)`를 호출해 통보 파일을 생성한다. 이후 백업과 `ResultDocumentDAO.updateResultDocumentTransState`를 수행한다. 즉 압축 해제 자체와 UI/DB 등록은 별도 단계다.

`NoticeZipProbe.java`에서 원본 DDMD `Commons.decompress`를 네이티브 macOS JVM으로 실행했다. 전용 비공개 폴더에 **3개 파일, 총 3,596 bytes 생성 성공**했고, 각 파일을 ZIP 원본 entry와 byte-for-byte 대조해 일치 확인했다. 파일 권한은 0600이다. 실제 Windows DB 및 sam/out은 수정하지 않았다.

결론: 이 ZIP은 DDMD 통보 생성 경로의 원본 압축 해제 함수가 실제 처리할 수 있는 형식이다. 다만 DDMD GUI 목록에 등록하거나 화면에서 내용을 여는 것은 검증하지 않았다. ZIP을 sam/out에 복사하기만 하면 목록에 표시된다고 보장하지 않는다. 정식 UI 경로에는 NtcDoc/ResultDocument 문서 식별정보, 문서별 파일 배치 및 DB 상태 연결이 필요하다.

증거: `gateway_poc/evidence/macos-ddmd-zip-compatibility.json` (생성 경로 포함). 생성 파일은 기존 비공개 통보 폴더 아래 `ddmd-generated-*`에 보관한다.

### 설정·DB·GUI 격리 시험 (2026-09-09)
원본 DAO로 합성 통보 등록·조회·상태 변경, 원본 Commons로 실제 로컬 ZIP 3개 파일 생성 및 바이트 비교는 통과했다. 원본 GUI 프로세스는 시작됐으나 Guard의 VACUUM 파일 권한 차단과 뒤이은 DB 잠금, Windows 명령 의존성, CUA 앱 선택 실패로 화면과 전체 GUI 흐름은 미검증이다. 상세: ../isolated-ui/README.md 및 ../evidence/isolated-ui-result.json. 운영 DB와 실제 SAM 송신은 이번 시험 대상이 아니다.

후속 4단계 시험에서 VACUUM의 /var/tmp 권한 확인 실패를 재현하고, 메모리 임시 저장을 지정하는 시험 JDBC 어댑터로 GUI 로그의 DB 잠금 오류를 해결했다. 원본 설정 저장/별도 JVM 재로딩과 원본 통보 컨트롤러의 생성·백업·DB 갱신 흐름까지 통과했다. 실제 화면은 잠금 해제 후에도 CUA의 Java 앱 선택 실패로 미검증이다. 최신 판정은 ../isolated-ui/README.md의 '4단계 추가 시험' 및 ../evidence/isolated-four-stage-result.json 참조.
