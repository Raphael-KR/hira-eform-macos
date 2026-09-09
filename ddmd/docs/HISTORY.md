# DDMD 작업 히스토리와 실험 기록

정리 기준: 2026-09-09. [DDMD README](../README.md)는 현재 준비 상태와 문서의 진입점이다.
e-Form 로그인·CLI 수집·메뉴 막대 앱의 이력은 [별도 문서](../../docs/HISTORY.md)에 있다.

**최종 상태:** 시험용 JVM과 임시 실행 환경을 제거했다. 아래 성공 기록은
해당 실험 시점의 증거이며, 현재 실행 가능 상태나 실제 SAM 청구 성공을 뜻하지 않는다.
실제 SAM 청구 전송은 시험에서 제외했다. 실서버·GUI 재실행에는 별도 준비와 승인이 필요하다.

## DDMD 실험 요약

아래 상세 원기록은 당시 내용을 보존한다. 이전 절의 ‘현재’, ‘다음’, 실행 경로와
상주 PID는 당시 표현이며 최신 운영 상태로 읽지 않는다. 각 기록의 후속 절이
초기 판정을 갱신하며, 최종적으로 시험 환경은 정리됐다.

| 순서 | 실험 | 결과와 후속 판정 |
|---|---|---|
| 1 | Windows 설치본 정적 조사 | 명령 파일·Java 객체/암호 계층 식별. API ok는 청구 접수 완료가 아님 |
| 2 | Windows Session 0 합성 PoC | 17검사와 Node 교차 복호화 성공; 합성 peer와 실서버 구분 |
| 3 | Windows 실제 인증·수명 | 최초 토큰, 만료 대기 후 재인증, 별도 프로세스 복구·수신처 조회 성공 |
| 5 | macOS ARM64 Java 8 | 인증·수명·조회, 합성 암호 22검사 성공. Launcher headless와 SAM 엔진 전체는 미완료 |
| 6 | 통보 다운로드 | 서버 첨부 수신 후 저장부 실패, 기존 payload 복구. 재다운로드 없이 파일 확보 |
| 7 | 통보 로컬 처리 | 복호화·CMS 수학 검증·해시·ZIP·생성/백업/DB 시험 성공. CA 신뢰·폐지는 미완료 |
| 8 | 격리 GUI | JDBC 임시 저장 수정, showpanel과 APPL 실행기로 본 화면 확인. 도구 접근 실패와 화면 실패 구분 |
| 9 | GUI 12경로 | 최초 7표시·4JIDE 실패·1SAM 부재 안내. JIDE/인자 보정 후 네 실패 화면 재진입 성공 |
| 10 | 단계별 업데이트 | 21첨부 수신·적용·검증 후 추가 0개. 동일 파일 재제시 7개를 신규 변경으로 세지 않음 |
| 11 | 자동 업데이트 | 별도 시험에서 13모듈 적용·앱 시작·정상 null 보고 응답·추가 0개. 재실행 무변경 |

상세 정적 계약은 [설치 분석](ddmd-integration-analysis.md),
[구형 API 대조](ddmd-legacy-api-compatibility.md),
[SAM 시험 경계](ddmd-sam-test-boundary.md)를 참조한다.
이들은 중복 진행 보고가 아니라 명령·스키마·시험 권한의 별도 참고 자료라 유지한다.
비로그인 [biz 사이트맵](biz-hira-sitemap.md)도 메뉴 순서와 ID를 보존한다.


## 폐기한 대안

Wine 경로는 JVM 충돌과 입력 오류로 중단했다. 이후 네이티브 macOS JVM으로 필요한
기능을 검증해 Wine 의존성을 제거했다. 전용 도구와 상세 보고는 삭제했고, macOS
진단 도구의 설치본 경로는 `DDMD_SOURCE_DIR`로 명시하도록 변경했다.
삭제 전 소스·문서는 Git 제외 `tmp/`에 백업했다. 로컬 원본 evidence는 건드리지 않았다.

## 기록 보존 방식

계획·단계별 시험·오류 수정·종료 보고를 통합했다. 후속 정리에서 폐기한 대안의
상세 보고 1개를 제거하고, 나머지 12개 원기록은 제목 계층과 상대 링크를 변환해 보존했다.
공개하지 않는 evidence 파일은 클릭 링크 대신 로컬 경로로 표기한다.
기존 사본과 SHA-256 목록은 Git 제외 `tmp/`의 문서 정리 백업에 보관한다.

아래 각 절의 '현재', '다음', 임시 실행 경로와 PID는 당시 표현이다.
원기록의 초기 미검증 판정과 후속 성공·정리 기록을 함께 읽어야 한다.
코드·진단 도구는 [도구 색인](../gateway_poc/README.md)에 남겨 두었으며,
과거 명령을 현재 운영 명령으로 간주하지 않는다.

## 상세 원기록

- [DDMD headless 인증 경계 PoC](#ddmd-offline)
- [실제 DDMD 인증 한정 검증](#ddmd-live)
- [SAM 제외 headless gateway 검증](#ddmd-gateway)
- [격리 macOS JVM 설치](#ddmd-macos)
- [DDMD 설정·DB·GUI 격리 검증](#ddmd-isolated)
- [DDMD Computer Use용 격리 앱 실행기](#ddmd-launcher)
- [HIRA DDMD의 macOS headless 실행 및 GUI 검증 종합](#ddmd-summary)
- [DDMD macOS Computer Use 직접 GUI 시험](#ddmd-gui)
- [macOS DDMD 환경설정 오류 수정](#ddmd-jide)
- [DDMD macOS 실제 업데이트 시험](#ddmd-update)
- [macOS DDMD 자동 업데이트 구현 계획](#ddmd-auto-update)
- [DDMD 시험 환경 정리](#ddmd-cleanup)

<a id="ddmd-offline"></a>

<details>
<summary>DDMD headless 인증 경계 PoC</summary>

Source: `ddmd/gateway_poc/README.md` (historical)

### DDMD headless 인증 경계 PoC

최신 추가 검증: **2026-09-09 Windows headless 실제 HIRA 인증과 AuthToken 발급·미만료 검사를 통과했다.** [실제 인증 검증](#ddmd-live)을 참조한다. 아래 내용은 앞서 수행한 합성·오프라인 시험의 범위와 증거다.

목표: 기존 Node 키 복호화·서명 구현과 DDMD Java 데이터·암호 라이브러리를 합성 입력으로 연결한다.

범위: 합성 인증서만 사용한다. 기존 DDMD 설치 파일은 읽기 전용이며 HIRA 서버, 실제 인증서, SAM, 기관 DB, Keychain은 사용하지 않는다. 기존 Launcher와 GUI 컨트롤러를 실행하지 않는다.

완료 조건:

1. Node의 기존 `loadEncryptedKeyDer`·`signDn`으로 합성 키와 CMS를 생성한다.
2. Windows의 기존 Java 8에서 `java.awt.headless=true`로 독립 Java PoC를 실행한다.
3. DDMD의 실제 `KeyInfoSet`, `Credentials`, `AuthToken` 클래스를 사용한다.
4. 실제 DDMD 암호 라이브러리로 인증 요청 직렬화·봉투 암호화와 합성 응답 복호화·토큰 복원을 검증한다.
5. 실패·만료·갱신 및 GUI·네트워크·네이티브 호출 차단을 검증한다.

이 PoC는 서버 구현을 흉내 낸 로컬 왕복 시험이다. 실제 HIRA 인증·토큰 발급·재발급 성공, 전체 DDMD headless 실행을 입증하지 않는다. 원본 Java `MessageCipherAgent`는 ClientContext를 참조하므로 직접 실행하지 않고, 분석한 처리 순서를 독립 실행부에 명시적으로 구성한다.

단계: 코드·호출 경로 확인 → 합성 fixture 생성 → 임시 Windows 디렉터리에 PoC와 필요한 JAR 복사 → 컴파일 → 차단된 환경에서 실행 → 증거 기록.

프로그램 JAR·컴파일러·합성 비밀은 이 폴더에 포함하지 않는다. 실행 방법과 결과는 검증 후 아래에 기록한다.

#### 실행 방법

Mac의 기존 `macos_agent/node_modules`, Node·Python·OpenSSL과 SSH 접근이 필요하다. 컴파일러는 [Maven Central의 Eclipse ECJ 3.26.0](https://repo.maven.apache.org/maven2/org/eclipse/jdt/ecj/3.26.0/)을 `/private/tmp/hira-ddmd-inspect/ecj-3.26.0.jar`에 두며, runner가 게시 SHA-1 `4837be609a3368a0f7e7cf0dc1bdbc7fe94993de`와 대조한다. 시스템에 JDK를 설치하지 않는다.

프로젝트 루트에서:

```sh
python3 gateway_poc/scripts/run-windows-probe.py
```

이 명령은 Mac 임시 디렉터리에 합성 fixture를 만들고, Windows의 `C:\Users\user\AppData\Local\Temp\hira-headless-poc-*`에 필요한 JAR·컴파일러·PoC를 복사하여 실행한다. 실제 DDMD JRE는 실행 런타임으로만 사용한다. 합성 키와 암호문은 임시 디렉터리에 남으며, 정확한 최신 위치는 `evidence/run.json`에 기록한다. 기존 설치 폴더를 청구 작업 디렉터리로 사용하지 않는다.

#### 2026-09-09 검증 결과

**Windows Session 0, Java 8, `java.awt.headless=true`에서 17개 검사 통과.**

- 기존 DDMD의 `MagicLineKeyInfo`, `KeyInfoSet`, `Credentials`, `AuthToken` 사용.
- 실제 `JCAOSSecurityProvider`와 SEED EnvelopedData 요청 왕복 성공.
- 합성 서버 응답의 대칭 암호화·복호화, 토큰 복원·만료 감지·만료 시각 연장 성공.
- 토큰 verifier가 독립 계산 `Base64(SHA256(nonce || Base64Decode(previousVerifier)))`와 일치.
- 잘못된 봉투 데이터는 예외로 반환되고 UI를 요구하지 않음.
- 기존 Node 코드로 복호화한 합성 개인키를 Java에 공급했고, 기존 `signDn`의 한글 CP949 CMS는 OpenSSL로 검증.
- Java가 만든 실제 DDMD SEED 봉투를 기존 Node `seed.js`로 복호화하여 원본 직렬화 바이트와 일치 확인.
- guard 자체의 4개 의도된 거부 시험 외에는 네트워크·프로세스·네이티브 로딩·AWT 권한 차단 이벤트가 없었음.

증거: `evidence/windows-probe.txt`, `node-interop.txt`, `node-fixture.txt`, `run.json`.

JRE 기본 난수와 암호 공급자(SunEC/SunMSCAPI 포함)는 guard 설치 전에 초기화한다. 이는 OS/JRE 네이티브 코드 자체가 없다는 시험이 아니다. DDMD/KSign 코드 실행 이후에는 추가 네이티브 로딩을 금지하며, HIRA 인증 DLL이나 PKCS11 함수를 호출하지 않았다. Launcher와 DDMD 클라이언트 컨트롤러 JAR는 classpath에서 제외했다. SecurityManager는 이 Java 8 PoC의 검증 수단이며 향후 운영 격리 구현으로 확정한 것은 아니다.

초기 시험에서는 JRE의 지연 초기화가 guard에 걸렸고, 독립 verifier 기대값의 연결 순서를 잘못 가정해 한 번 실패했다. 바이트코드의 `nonce` 우선 순서에 맞춰 기대값을 수정하고 전체 시험을 다시 통과했다. 이전 실패는 `evidence/earlier-verifier-diagnostic.txt`에 보관하며 최신 결과와 구분한다.

#### 판정 한계

이 결과는 **인증 객체·키 공급·암호처리를 GUI 없이 기존 라이브러리로 수행할 수 있다는 실행 증거**다. `CLT_AUTH_REQ` 본문인 Credentials의 처리를 시험했으며 실제 transport action/header를 서버에 전달하지 않았다. 합성 peer는 실제 HIRA 서버가 아니다.

실제 서버의 인증 수용·tokenId 발급·토큰 만료 후 재인증, NPKI 부가 속성 호환성, 청구 파일 서명과 통보 복호화, SAM 점검의 headless 분리, Windows 서비스 설치는 미검증이다. Node CMS와 Java 서명 알고리즘 전체의 호환성도 이번 시험만으로 확정하지 않는다. 실행 순서상 키 선택 창이 필수라는 기존 우려는 좁혀졌지만, 완전한 HIRA gateway 완료로 보고하지 않는다.

</details>

<a id="ddmd-live"></a>

<details>
<summary>실제 DDMD 인증 한정 검증</summary>

Source: `ddmd/gateway_poc/live/README.md` (historical)

### 실제 DDMD 인증 한정 검증

승인: 사용자가 headless 경로의 실제 인증 서버 연결, 지정 macOS NPKI 인증서 및 macOS 암호 저장소 사용을 요청했다.

목표: Windows Session 0에서 `CLT_AUTH_REQ` 한 번을 전송하여 실제 AuthToken 발급 여부를 확인한다. 청구·통보·조회·업데이트 action은 실행하지 않는다. 비밀번호·개인키는 Mac 밖으로 보내지 않는다. 공개 인증서와 인증에 필요한 키 속성 값은 SSH 표준입력으로만 전달하고 파일·argv·로그에 저장하지 않는다. tokenId와 verifier도 출력·저장하지 않는다.

검증: 인증서/키/비밀번호·유효기간 로컬 검사 → 설치된 본원 공개 인증서 및 endpoint 확인 → 라이브러리와 독립 실행부 격리 → `java.awt.headless=true`에서 인증 → 토큰 타입·존재·만료시각만 출력. 자동 재시도는 하지 않는다. 오류시 코드와 예외 클래스만 기록한다.

기존 PoC와 차이: 실제 서버가 응답하며 합성 토큰을 만들지 않는다. 고정 서버/포트로만 연결을 허용하고, 외부 프로세스·추가 네이티브 로딩·GUI 권한은 차단한다. 기존 DDMD 및 macos_agent 실행 코드는 변경하지 않는다.

#### 2026-09-09 실제 인증 성공

**01:00:03 KST에 headless 실제 인증 성공을 확인했다.** `CLT_AUTH_REQ` → 설치된 본원 인증서로 봉투 암호화 → 원본 MSI 전송 → 응답 복호화 → 실제 `AuthToken` 복원 → tokenId 존재·미만료 검사까지 통과했다. 서버가 반환한 만료 시각은 **01:05:03.671 KST**였다. 이 실행에서 약 5분의 유효기간을 관찰한 것이며 일반 정책을 단정하지 않는다. 토큰은 프로세스 메모리에서만 사용하고 종료했다.

macOS의 지정 KICA 인증서 한 쌍을 찾았고, 기존 Keychain 함수로 얻은 비밀번호로 개인키를 복호화하여 공개키 일치·인증서 유효기간을 검사했다. 실제 개인키 속성 `1.2.410.200004.10.1.1.3`의 20바이트 VID random을 사용했다. 비밀번호와 개인키는 Windows로 복사하지 않았으며, 공개 인증서와 VID random만 SSH stdin으로 전달했다.

실행은 Windows SSH의 Session 0, 원본 Java 8, `java.awt.headless=true` 조건이다. Launcher와 ClientContext를 로드하지 않았다. GUI·추가 네이티브 로딩·프로세스 실행·서버 listen은 차단했다. HTTP 클라이언트의 `Socket.bind(0)`만 임시 포트 할당 목적으로 허용했다. JRE 기본 암호 공급자는 guard 전에 초기화하므로 OS 네이티브 코드가 전혀 없다는 뜻은 아니다.

##### 진단 및 실행 횟수

- 최초 실행은 guard가 outbound bind까지 막아 연결 전에 실패했다. 네트워크 차단 사전검사에서 `connectChecks=0`과 동일 stack을 재현했다. 구형 HttpClient가 원인 예외를 숨겨 `NullPointerException`/`9902`가 된 것이다.
- bind 수정 후 사전검사는 실제 연결 직전 차단 지점에 도달했다. 사전검사는 서버로 전송하지 않았다.
- 이후 실제 인증 실행은 총 3회다. 첫 두 실행은 응답 객체의 클래스 필터 진단이었다. 실제 토큰 속성에 포함된 표준 `javax.crypto.spec.SecretKeySpec` 한 클래스를 허용한 마지막 실행이 성공했다. 비밀번호 변경·추측, 자동 재시도, 청구·통보 action은 없었다.
- `requests=1`은 각 프로세스의 `agent.send` 호출 횟수다. 초기 실패 기록의 이 값만으로 서버 도착을 주장하지 않는다.

##### 재현과 증거

```sh
python3 gateway_poc/live/prepare.py
node gateway_poc/live/run-live.mjs
python3 gateway_poc/live/verify-remote.py
```

두 번째 명령은 실제 인증을 수행한다. `--preflight`를 붙이면 네트워크 연결 직전에 차단한다. 실행별 진단 기록은 시간별 JSON으로 보존한다. 비밀 값이나 응답 payload를 저장하지 않는다.

- 최종 실제 인증 결과: `ddmd/gateway_poc/evidence/live-result.json` (local only)
- 준비된 실행 명령과 소스 식별: `ddmd/gateway_poc/evidence/live-prepared.json` (local only)
- Windows 환경과 라이브러리 대조: `ddmd/gateway_poc/evidence/live-environment.json` (local only)
- 초기 연결 전 실패: `ddmd/gateway_poc/evidence/live-initial-diagnostic.json` (local only)

결론: **Windows에서 GUI 없는 실제 DDMD 최초 인증 경로가 성립한다.** 아직 만료 후 재발급·서버 연장, 후속 인증된 업무 요청, SAM 점검·청구 전송·통보 수신, 상시 서비스는 검증하지 않았다. 따라서 전체 headless gateway 완료로 판단하지 않는다.

#### 후속 SAM 검증 범위 — 사용자 정정 반영

실제 한의원 인증서를 이용한 인증 성공은 SAM 본청구 전송 승인이 아니다. 운영 본청구 및 운영 통보 수신은 이번 검증에서 실행하지 않으며, 다음 단계를 일반적인 “SAM 청구 시험”으로 묶어 진행하지 않는다.

심평원 [2023 요양급여비용 청구길라잡이](https://www.hira.or.kr/ebooksc/2023/07/BZ202307058814745.pdf)의 인쇄 206–207쪽은 청구오류 사전점검이 진료비 지급과 무관하며, 점검 후 별도로 실청구해야 한다고 설명한다. 사전점검 메뉴로 파일을 송신하고 업무포털에서 결과를 확인하는 절차다. 이는 기관 업무용 사전점검 서비스의 근거이며, 합성 환자 자료를 자유롭게 넣는 개발자 sandbox 또는 본청구·심사결과 통보 전체를 모사하는 환경이라는 근거가 아니다.

현재 미확인: 개발용 SAM 시험 환경의 현재 주소·신청 절차·인증서/기관기호 요건·허용 시험 데이터·시험 통보 지원 범위, 설치 DDMD의 사전점검/본청구 구분 코드 및 라우팅. 이 사항을 공식 안내와 원본 코드로 확인하기 전 SAM을 전송하지 않는다. 동일 호스트를 사용할 수도 있으므로 테스트 여부는 주소만으로 판단하지 않는다. 합성 SAM의 로컬 파싱·암복호화 시험은 서버 전송 없이 분리할 수 있다.

</details>

<a id="ddmd-gateway"></a>

<details>
<summary>SAM 제외 headless gateway 검증</summary>

Source: `ddmd/gateway_poc/gateway/README.md` (historical)

### SAM 제외 headless gateway 검증

- 목표: 실제 인증의 수명·복구와 비청구성 조회를 Windows headless 경로로 검증한다.
- 범위: 별도 임시 Java 실행부, 기존 macOS 키 공급 코드, 실제 인증 및 읽기 전용 공개 인증서/수신처 메타데이터 조회 후보.
- 완료: 실제 만료 관찰 후 새 토큰 발급, 독립 프로세스에서 인증 복구, 토큰 사용 조회, 통신·인증 오류의 안전한 처리와 근거 기록.
- 제외: SAM 송신·사전점검·청구, 운영 통보 조회/수신, DDMD 설치본·기관 DB 수정, 서비스 설치, 잘못된 인증서·비밀번호를 운영 서버에 보내는 시험.
- 검증: 원본 코드와 조회 의미를 먼저 확인한다. 실제 인증 만료는 시계를 조작하지 않고 기다린다. 네트워크 차단·비정상 인증 응답은 로컬 fault injection으로 검증하여 실제 서버 장애·잘못된 자격증명 거절 검증과 구분한다.

비밀번호·개인키는 Mac 밖으로 보내지 않는다. 토큰과 인증 키는 메모리에만 보관한다. 단일 실행부가 지원하는 고정 명령만 사용하며 임의 action은 지원하지 않는다. 기존 `live/LiveAuth.java`와 이전 성공 기록은 보존한다.

#### 2026-09-09 결과

| 항목 | 실행 결과 | 증거 |
|---|---|---|
| 실제 만료 후 재인증 | 02:43:22–02:48:25 KST. 발급된 약 5분 만료시각까지 실제 대기했고, 새 tokenId와 더 늦은 만료시각을 받은 것을 메모리에서 비교 | lifecycle: `ddmd/gateway_poc/evidence/gateway-lifecycle-result.json` (local only) |
| 토큰 사용 조회 | `CLT_CERT_REQ`로 현재 기관의 수신처 공개 인증서 1건 조회. 토큰 식별자·verifier·timestamp·MAC 헤더를 사용했고 응답의 AuthToken·RecpHbrRes를 복원. 첨부파일 없음 | recipient: `ddmd/gateway_poc/evidence/gateway-recipient-result.json` (local only) |
| 프로세스 종료 후 인증 복구 | lifecycle 프로세스 종료 후 02:49:28–02:49:32 KST에 별도 SSH/JVM에서 인증 성공. 이전 토큰 파일이나 GUI 로그인 상태를 사용하지 않음 | auth: `ddmd/gateway_poc/evidence/gateway-auth-result.json` (local only) |
| 인증 응답 오류 | 잘못된 직렬화 헤더를 로컬에서 주입하여 거부됨을 확인 | failure-tests: `ddmd/gateway_poc/evidence/gateway-failure-tests-result.json` (local only) |
| 네트워크 오류 | 정상 인증 후 연결 직전 강제 차단. DDMD 예외로 반환하며 프로세스가 계속 동작하고 기존 미만료 토큰을 보존 | failure-tests: `ddmd/gateway_poc/evidence/gateway-failure-tests-result.json` (local only) |
| SAM 명령 제외 | Node CLI에서 `sam`을 exit 2로 거부. 이 검사는 Keychain 조회·SSH 시작 전 수행 | summary: `ddmd/gateway_poc/evidence/gateway-summary.json` (local only) |

네트워크 오류 시험의 `requests=2`는 정상 인증 1회와 연결 전에 차단된 send 호출 1회의 합이다. 잘못된 자격증명을 실제 HIRA 서버에 보낸 것은 아니다. 만료된 토큰을 서버에 제출해 거절시키지도 않았으며, 서버가 준 만료시각을 기준으로 재인증한 것이다. 서버 측 장애·계정 잠금·비밀번호 오류 응답의 실환경 검증으로 확대 해석하지 않는다.

조회는 원본 DDMD `SendController`의 `RecpHbrReq`를 이용하는 읽기 전용 인증서 조회다. `ClientConstants`에서 건강보험 코드 `Y`를 확인했고, 현재 날짜를 수신처 적용일 조회 조건으로 사용했다. 환자·SAM·청구문서 ID를 넣지 않았다. 원본 일반 조회는 MXS를 사용하지만, 이번 독립 실행부는 기존 MSI transport에서 같은 action·암호화 DTO 및 원본 MXS의 토큰 MAC 헤더 방식을 사용해 실제 서버 수용을 검증했다. 따라서 MXS/ebMS 전체를 검증했다는 뜻은 아니다.

첫 조회 실행은 응답의 공개 인증서가 Java `CertificateRep.readResolve`를 거쳐 복원되는 과정에서 클래스 필터에 걸렸다. 표준 구현 `sun.security.x509.X509CertImpl`만 추가한 뒤 재실행에 성공했다. 최초 실패는 시간별 JSON에 보존했다. 토큰·인증서 내용·응답 payload는 저장하지 않았다.

`RecipientProbe`는 응답 토큰의 만료 갱신과 verifier 갱신 코드를 포함한다. 이번 조회 한 번의 성공만으로 장시간 연속 요청·동시성·무중단 갱신까지 검증한 것은 아니다.

#### 실행

```sh
python3 gateway_poc/gateway/prepare.py
node gateway_poc/gateway/run.mjs auth
node gateway_poc/gateway/run.mjs lifecycle
node gateway_poc/gateway/run.mjs recipient
node gateway_poc/gateway/run.mjs failure-tests
python3 gateway_poc/gateway/verify-remote.py
```

`auth`는 새 프로세스에서 인증하고 종료한다. `lifecycle`은 실제 만료 후 재인증까지 약 5분 걸린다. `recipient`는 인증과 공개 수신처 인증서 조회만 수행한다. `failure-tests`도 정상 인증 1회는 실제 서버에서 수행하고, 그 뒤 오류를 로컬에서 주입한다. 자동 재시도·토큰 영구 저장·상시 서비스 등록은 구현하지 않았다.

실행 식별은 prepared: `ddmd/gateway_poc/evidence/gateway-prepared.json` (local only), 환경 검증은 environment: `ddmd/gateway_poc/evidence/gateway-environment.json` (local only), 종합 판정은 summary: `ddmd/gateway_poc/evidence/gateway-summary.json` (local only)에 기록한다. 각 실행의 소스 해시와 시각을 별도로 보존한다. 초기 lifecycle은 조회 클래스 추가 전 준비된 폴더에서 실행했으며 HeadlessGateway 소스 해시는 최종본과 같다.

사후 확인에서 SSH는 Session 0이고 14개 라이브러리는 설치본과 일치했으며 시험 폴더에 payload 파일은 없었다. 기존 DDMD `javaw` GUI 프로세스는 이 사후 확인 시점에 관찰되지 않았다. 이번 실행부는 프로세스 실행을 차단하며 DDMD 종료·재시작 명령을 수행하지 않았다. 기존 GUI의 종료 시점·원인은 확인하지 않았다. `macos_agent`는 `main...origin/main`의 clean 상태를 유지했다.

#### 판정

**SAM을 제외한 최소 인증·조회 CLI와 요청된 수명·재시작 검증을 완료했다.** 오류 처리는 로컬 주입 범위에서 확인했다. 이 구현은 macOS가 인증 재료를 공급하고 Windows 원본 Java 라이브러리가 실행하는 구조다. Windows 단독 비밀 공급, macOS/Linux 단독 실행, 운영 상시 서비스, SAM 및 통보 처리는 이번 완료 범위에 포함하지 않는다.

</details>

<a id="ddmd-macos"></a>

<details>
<summary>격리 macOS JVM 설치</summary>

Source: `ddmd/gateway_poc/macos-jvm/README.md` (historical)

### 격리 macOS JVM 설치

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

보안 sandbox가 아닌 설치 경로 분리이며, 임시 폴더이므로 OS 정리에 의해 삭제될 수 있다. 인증정보를 사용하지 않았다. DDMD JAR 오프라인/실제 인증 검증은 아직 수행하지 않았다.

#### DDMD 인증 검증 계획

- Goal: 네이티브 macOS JVM에서 DDMD 라이브러리로 실제 AuthToken 발급을 확인한다.
- Boundary: 원본 인증용 JAR 14개, 기존 Keychain 인증정보 로더, 인증 전용 CLT_AUTH_REQ 한 건. 기관 번호는 기존 Windows 설정에서 읽기만 한다.
- Done: 오프라인 17개 검사와 Node 교차 복호화, 실제 서버 AuthToken 존재·미만료 확인.
- Non-goals: GUI 실행, SAM·청구·통보, 비밀정보 파일 저장.
- Verification: 소스·라이브러리 해시 검증, 제한된 결과 로그, 시험 종료 후 임시 payload 확인.

오프라인 검사 17개 및 Node 교차 복호화 통과. 실행부는 Windows 경로를 시험 폴더 경로로 변경하고 기관 번호를 stdin으로 받는다. 실제 개인키·비밀번호는 JVM에 전달하지 않는다.

#### 2026-09-09 실제 인증 성공

**03:25:41–03:25:42 KST, macOS ARM64 Zulu Java 8u504에서 실제 HIRA 인증 성공. Windows JVM 없이 실행했다.**

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

#### 2026-09-09 SAM 전송 제외 확대 검증

사용자가 실제 SAM 전송 외 검증을 승인했다. 실제 호출 action은 인증 `CLT_AUTH_REQ`, 공개 수신처 인증서 `CLT_CERT_REQ`, 오늘 날짜 통보 목록 `CLT_NTC_LIST_REQ`로 제한했다. 통보 상태 변경 `CLT_NTC_UPT_REQ`, 문서 다운로드·삭제·청구는 호출하지 않았다.

##### 실서버 실행 결과

| 항목 | 결과 | 증거 |
|---|---|---|
| 실제 토큰 만료 후 재인증 | 03:28:27–03:33:27 KST, 약 5분 대기 후 만료 관찰, 새 tokenId와 늦어진 만료시각 확인 | `macos-lifecycle-result.json` |
| 공개 수신처 인증서 | 1건, 토큰 헤더/MAC 및 응답 토큰 처리 성공, 첨부 0개 | `macos-recipient-result.json` |
| 통보 목록 | 2026-09-09 당일, 건강보험·실청구 분류의 조회 응답 성공, 0건, 첨부 0개 | `macos-notice-list-result.json` |
| 로컬 오류 처리 | 인증 성공 후 비정상 직렬화 응답과 로컬 연결 차단 예외 처리, 기존 토큰 보존 | `macos-failure-tests-result.json` |

통보 조회 0건은 해당 조건에만 적용되며 전체 기간의 사서함이 비었다는 뜻이 아니다. 실제 통보 다운로드·복호화·수신확인까지 검증한 결과가 아니다. 목록 조회와 상태 변경 action의 분리는 설치본 ReceiveController 바이트코드로 확인했다. 서버 내부 부수 효과는 직접 관측하지 않았다. failure-tests의 requests=2는 send 함수 진입 횟수이며 두 번째는 로컬에서 차단되어 전송되지 않았다. 운영 서버에 잘못된 비밀번호·인증서·변조 토큰을 보내지 않았다.

##### 합성 파일·암호 검사

기존 17개에 바이너리 CMS 서명·검증, 파일 암호화·복호화, 변조 검출, 추가 native/GUI/network 없음, DDMD 메시지+첨부 서명 생성을 추가해 **22개 검사 통과**. 65,537바이트 합성 바이너리를 사용했으며 실제 SAM 형식/환자 데이터가 아니다. 원본 JCAOS SignedDataCipher는 서명용 객체와 검증용 객체의 상태가 달라 각각 생성해야 한다.

파일 CMS 및 DDMD 메시지 CMS를 OpenSSL로 독립 검증했다. 파일 CMS의 복원 바이트는 원본과 동일했다. 메시지 CMS의 OpenSSL 성공은 외부 서명의 수학적 검증이며 DDMD 메시지 내부 첨부 참조 규약이나 HIRA 서버 수용까지 증명하지 않는다.

**별도 미해결:** `DdmdMessageSignatureImpl.verify`는 자신이 생성한 서명을 처리할 때 `DdmdContents.getInstance`에서 `IllegalArgumentException: unknown object in getInstance : class [B` → DDMD 8174 오류를 냈다. 이 검증을 통과한 것으로 세지 않는다. 원본 JAR는 수정하지 않았다. 통보 복호화는 합성 파일 왕복 수준까지 검증됐고 실제 통보 payload는 사용하지 않았다.

##### 점검 실행 경계

`BoundaryProbe`를 빈 시험 폴더, headless, 네트워크·프로세스 실행 차단 아래 실행했다.

- 원본 SQLite JDBC의 메모리 DB 연결 및 SELECT 성공. 원본 드라이버가 무조건 Windows 전용이라는 가정은 맞지 않았다.
- Launcher 정적 초기화: `HeadlessException`, Launcher.java:112.
- CExamController 초기화: DocCipherController → ClientContext 의존성에서 ApplicationClassLoader의 package signer 불일치 `SecurityException`. 모든 설치 JAR를 평면 classpath로 넣는 방식의 한계이며 점검 알고리즘 자체가 Mac에서 불가능하다는 판정이 아니다.
- CExamChineseSpec091 클래스 초기화 성공. 실제 파일 파싱·검사 성공을 뜻하지 않는다.
- 완전한 SAM+MEDLOG 시험 묶음이 없고 현재 점검 진입부도 막혀 있어 실제 SAM 점검, 등록, 결과 파일 생성은 완료하지 못했다. 운영 SAM/DB를 대신 가져와 사용하지 않았다.

따라서 **Mac 인증·토큰 수명 관리·조회·파일 암호 기반은 실증됐지만 전체 SAM gateway 검증은 미완료**다. 다음 남은 단위는 원본 클래스 로더 구조를 보존한 점검 엔진 분리와 검증 가능한 합성 SAM 묶음 준비, 메시지 검증 파서 호환성 확인이다. 통보 다운로드에는 대상 문서와 수신 상태 변경 계약 확인이 필요하다.

실행: `python3 gateway_poc/macos-jvm/prepare-live.py` 후 `node gateway_poc/macos-jvm/run.mjs lifecycle|recipient|failure-tests|notice-list` 중 하나. 목록 범위는 코드에서 당일로 고정되어 있다. `sam` 등 허용하지 않은 명령은 인증정보 접근 전에 거부한다.

증거는 `gateway_poc/evidence/`의 위 JSON 및 `macos-offline-probe.txt`, `macos-node-interop.txt`, `macos-file-crypto.json`, `macos-boundary.txt`에 보관한다. 실제 개인정보·토큰·키는 출력/저장하지 않았다. 합성 fixture의 테스트 키는 시험 임시 폴더에만 있다.

#### 실제 통보 다운로드 계획

사용자가 실제 통보 다운로드를 명시 승인했다. 최근 90일 건강보험 실청구 통보 목록에서 12건을 확인했고, 가장 최근 문서 한 건을 선택한다. 실제 호출은 인증, 목록, `CLT_NTC_REQ`이며 `km_cert`에 사용자 암호화 공개 인증서를 전달한다. 삭제·별도 상태 변경 요청 및 SAM 송신은 포함하지 않는다. 다운로드 자체의 서버 수신 이력 변화는 가능하며 서버 내부 동작은 관측하지 못한다.

파일은 `gateway_poc/private-downloads/notice-*`의 사용자 전용 폴더(0700)에 일반화한 파일명(0600)으로 저장한다. 원문·기관/환자 식별자·토큰·키는 보고서에 남기지 않는다. 완료 조건은 실제 응답 첨부 파일 확보와 크기 확인이며, 복호화·서명 검증 여부는 별도로 명시한다. 기존 메시지 검증 파서 문제를 무시하고 검증 완료로 표시하지 않는다.

##### 실제 다운로드 결과 (2026-09-09 03:38–03:39 KST)

**실제 통보 한 건의 암호화 본문과 서명 파일을 Mac에 확보했다.** 최근 90일 조회 결과 12건 중 BrokerRcvDT가 가장 최근인 한 건을 선택했다. 인증→목록→`CLT_NTC_REQ` 각 1회, 총 3회 호출했다. 서버는 `NtcDoc`과 2개 첨부 payload를 반환했다.

JVM 실행은 응답 수신 후 로컬 파일 저장 과정에서 ExceptionInInitializerError/SecurityException으로 종료되어 `macos-download-result.json`의 passed는 false다. 이 실패를 서버 다운로드 실패와 동일시하지 않는다. 수신 registry에 남은 2개 payload를 Python으로 별도 복사했고 바이트 일치·해시·권한을 확인했다. `.ref` 2개는 transport 내부 메타데이터로 분리하고 사용자용 파일에는 포함하지 않았다. 다운로드 재요청은 보내지 않았다. 저장 실패의 구체 원인은 확정하지 않았으며 진단 stage 표기만 세분화했다.

보관 위치: `/Users/<owner>/Playground/HIRA_eform_login/gateway_poc/private-downloads/notice-xcDjRX`

- `encrypted-notice.cms`: 1,213 bytes, CMS envelopedData.
- `signature.cms`: 2,044 bytes, CMS signedData.
- 폴더 권한 0700, 파일 권한 0600. 파일 이름에 문서 식별자·기관 번호를 넣지 않았다.
- **복호화 및 서명 검증은 아직 수행하지 않았다.** 정상 문서 내용 또는 진료비 결과를 확인했다고 해석하지 않는다.
- 서버의 수신 상태 변화는 별도로 조회/검증하지 않았다. 별도 수신확인·삭제·상태변경 action 및 SAM 송신은 호출하지 않았다.

최종 파일 확보 증거: `gateway_poc/evidence/macos-download-recovered.json`. 최초 실행 결과는 `macos-download-result.json`으로 보존한다. 실제 파일과 원본 수신 registry는 비공개 로컬 자료이며 커밋/외부 공유 대상이 아니다.

#### 실제 통보 복호화·서명 검증 (2026-09-09)

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

#### 복호화 ZIP의 DDMD 처리 호환성

실제 ZIP에는 `.1`, `.2`, `.3` 파일 3개(각 3,528 / 68 / 0 bytes)가 있다. 식별자가 포함될 수 있는 원본 파일명과 내용은 보고서에 출력하지 않았다.

원본 `ReceiveController.doOnSucceeded`는 복호화 결과를 문서별 `zip` 경로에 저장하고 `ResultDocument`를 구성한다. 자동 생성 설정에 따라 `zipReleaseCont`가 `Commons.decompress(File, File)`를 호출해 통보 파일을 생성한다. 이후 백업과 `ResultDocumentDAO.updateResultDocumentTransState`를 수행한다. 즉 압축 해제 자체와 UI/DB 등록은 별도 단계다.

`NoticeZipProbe.java`에서 원본 DDMD `Commons.decompress`를 네이티브 macOS JVM으로 실행했다. 전용 비공개 폴더에 **3개 파일, 총 3,596 bytes 생성 성공**했고, 각 파일을 ZIP 원본 entry와 byte-for-byte 대조해 일치 확인했다. 파일 권한은 0600이다. 실제 Windows DB 및 sam/out은 수정하지 않았다.

결론: 이 ZIP은 DDMD 통보 생성 경로의 원본 압축 해제 함수가 실제 처리할 수 있는 형식이다. 다만 DDMD GUI 목록에 등록하거나 화면에서 내용을 여는 것은 검증하지 않았다. ZIP을 sam/out에 복사하기만 하면 목록에 표시된다고 보장하지 않는다. 정식 UI 경로에는 NtcDoc/ResultDocument 문서 식별정보, 문서별 파일 배치 및 DB 상태 연결이 필요하다.

증거: `gateway_poc/evidence/macos-ddmd-zip-compatibility.json` (생성 경로 포함). 생성 파일은 기존 비공개 통보 폴더 아래 `ddmd-generated-*`에 보관한다.

##### 설정·DB·GUI 격리 시험 (2026-09-09)
원본 DAO로 합성 통보 등록·조회·상태 변경, 원본 Commons로 실제 로컬 ZIP 3개 파일 생성 및 바이트 비교는 통과했다. 원본 GUI 프로세스는 시작됐으나 Guard의 VACUUM 파일 권한 차단과 뒤이은 DB 잠금, Windows 명령 의존성, CUA 앱 선택 실패로 화면과 전체 GUI 흐름은 미검증이다. 상세: ../isolated-ui/README.md 및 ../evidence/isolated-ui-result.json. 운영 DB와 실제 SAM 송신은 이번 시험 대상이 아니다.

후속 4단계 시험에서 VACUUM의 /var/tmp 권한 확인 실패를 재현하고, 메모리 임시 저장을 지정하는 시험 JDBC 어댑터로 GUI 로그의 DB 잠금 오류를 해결했다. 원본 설정 저장/별도 JVM 재로딩과 원본 통보 컨트롤러의 생성·백업·DB 갱신 흐름까지 통과했다. 실제 화면은 잠금 해제 후에도 CUA의 Java 앱 선택 실패로 미검증이다. 최신 판정은 ../isolated-ui/README.md의 '4단계 추가 시험' 및 ../evidence/isolated-four-stage-result.json 참조.

</details>

<a id="ddmd-isolated"></a>

<details>
<summary>DDMD 설정·DB·GUI 격리 검증</summary>

Source: `ddmd/gateway_poc/isolated-ui/README.md` (historical)

### DDMD 설정·DB·GUI 격리 검증

- Goal: 복호화된 실제 통보 ZIP을 시험 DB 레코드와 연결하고 원본 DDMD UI 경로를 검증한다.
- Boundary: 새 설치본의 프로그램/기본 DB를 복제한 전용 폴더, 합성 문서 메타데이터와 기존 로컬 통보 ZIP 사본. 원본 Windows 운영 상태는 보존한다.
- Done: 원본 DAO 등록·조회·파일 연결 검증과 원본 GUI 실행 결과를 구분해 기록한다.
- Non-goals: 서버 인증/조회/수신/송신, 실제 수신 상태 변경, 전역 설정 변경, 원본 운영 DB 쓰기.
- Verification: 복사 전후 해시, 원본 SQL/DAO 사용, 실행 네트워크·프로세스 차단, GUI 승인 범위 내 직접 확인.

#### 2026-09-09 실행 결과

macOS ARM64의 격리 Zulu Java 8에서 원본 DDMD DAO와 SQLite 매핑으로 합성 통보 1건을 등록·조회하고 생성 상태로 변경했다. 종료 후 SQLite integrity_check는 ok이고, 복제 원본 DB의 SHA-256은 준비 시점과 일치한다. 운영 Windows에는 접근하지 않았다.

기존 실제 복호화 ZIP 사본을 시험 문서의 로컬 경로에 배치하고 원본 Commons.decompress로 3개 파일(총 3,596바이트)을 생성했다. 생성 파일은 ZIP 엔트리와 바이트 단위로 모두 일치했다. DAO 상태 변경과 파일 생성은 분리된 시험이다. GUI 버튼을 통한 일괄 처리를 입증한 것은 아니다.

원본 ApplicationBootstrap 및 원본 클래스 로더로 GUI 프로세스가 시작되고 Launcher의 설정/DB 초기화 경로까지 실행됐다. 그러나 격리 Guard가 VACUUM 중 파일 쓰기 가능 여부 확인을 차단했고 이후 SQLITE_BUSY가 관측됐다. 이 결과만으로 macOS의 DB 호환성 결함이라고 판단할 수 없다. launcher.exe, tasklist, reg 등 Windows 전용 프로세스 호출도 관측되었고 Guard가 실행을 차단했다.

CUA 앱 목록에는 GuiBootstrap이 표시되었지만 앱 이름, bundle ID, 실행 경로 선택은 Invalid app으로 실패했다. 따라서 실제 창 표시, 수신함 행 표시, 설정 저장/재로딩, GUI를 통한 통보 생성은 미확인이다. 시험 Java PID 84665에 TERM을 보내 종료했다. GUI 통과로 간주하지 않는다.

격리는 전용 폴더와 Java SecurityManager 기반이며 OS 수준의 완전한 샌드박스 증명은 아니다. 네트워크 연결과 하위 프로세스 실행을 차단하고 시험 폴더 밖 Java 쓰기를 제한했다. 인증서와 운영 기관 설정을 복사하지 않았다. 보호 설정을 해제해 GUI 성공을 강제하지 않았다.

판정: 설정·DB·통보 파일 처리의 분리 재사용은 부분 실증되었다. 원본 GUI 전체 흐름은 검증 미완료다. 다음 시험은 복제 환경에서 VACUUM의 임시 경로 요구를 정확히 식별하고, GUI 도구가 해당 Java 앱을 선택할 수 있는 실행 방식을 확보한 뒤 수행해야 한다.

증거: ../evidence/isolated-db.txt, ../evidence/isolated-ui-result.json. 실행 준비 스크립트 run-local.py는 같은 시험 DB에 재실행하면 중복 키가 발생하므로 새 복제 DB에서만 실행한다.

#### 4단계 추가 시험 — 2026-09-09 04:22 KST

이 절이 앞선 미완료 항목의 최신 판정이다. 사용자는 실패한 단계가 있어도 후속 시험을 계속하고 필요하면 서버 연결을 허용했다. 이번 후속 시험에는 서버 연결이 필요하지 않았다.

| 단계 | 실제 시험 및 판정 |
|---|---|
| 1. DB 임시 경로 | 원본 sqlite-jdbc 3.7.2의 VACUUM이 /var/tmp에서 File.canWrite를 호출하다 Guard에 막히는 것을 재현했다. PRAGMA temp_store=MEMORY로 같은 동작이 통과했다. URL 쿼리 매개변수 방식은 효과가 없었다. |
| 2. Windows 의존성 | 복제 설치에 IsolatedJdbc 시험 드라이버를 추가하고 원본이 지원하는 driver.class.name/url 설정으로 연결마다 PRAGMA를 실행했다. GUI 로그의 기존 SQLITE_BUSY가 사라졌다. launcher.exe/tasklist/reg 실패는 남지만 이후 Launcher 초기화와 수신함 SQL 실행이 이어졌다. 화면 정상 동작까지 입증하지는 않는다. |
| 3. 실제 화면 | Mac 잠금으로 차단되어 사용자 잠금 해제 후 재시도했다. 실행 중인 GuiBootstrap은 앱 목록에 있으나 ID 선택은 Invalid app, JDK 번들 경로는 running application not found, 시험용 번들 설명 파일 경로는 Exec format error였다. CUA 화면/버튼 검증은 미확인이다. |
| 4. 설정·통보 흐름 | 원본 SystemInfoController.saveProperties로 시험 기관 00000000, 입출력 경로, 백업 3개월, 보안 사용을 저장하고 별도 JVM에서 재로딩해 일치했다. 원본 ApplicationBootstrap의 클래스 로더를 사용해 ReceiveController.zipReleaseCont를 직접 호출했고 true 반환, DB 상태 1을 확인했다. 생성 3파일·backup·월별 SAMbackup 모두 원본 ZIP 바이트와 일치했다. GUI 클릭 시험과는 다르다. |

통보 컨트롤러 시험은 원본 private 메서드를 reflection으로 호출했으며 NtcFrm/진행창을 null로 두었다. 따라서 GUI 연결부를 검증했다고 볼 수 없다. 합성 문서 ID도 원본 DocumentUtils.asFileName으로 변환해야 했으며 초기 파일명 불일치 실패를 기록 후 수정했다. 단순 평면 classpath는 서명된 패키지 충돌로 실패하여 원본 클래스 로더를 재사용했다.

원본 배포 JAR는 수정하지 않았다. 추가한 시험 드라이버·하네스와 복제 환경의 설정 변경이 있으므로 '원본을 아무 조정 없이 macOS에서 정상 실행'한 결과는 아니다. 배포 원본 DB 해시 유지, 원본 JAR와 복사본의 바이트 일치, 시험 DB integrity_check=ok를 확인했다. 마지막 GUI PID 88511은 TERM으로 종료했다.

현재 결론: GUI 아래의 설정 저장/재로딩과 로컬 통보 생성·백업·DB 갱신은 macOS JVM에서 실증됐다. 전체 화면 정상 여부는 GUI 도구의 Java 앱 접근이 해결되어야 판정할 수 있다. 서버 연결로 해결할 종류의 실패는 관측되지 않았다.

최신 증거: ../evidence/isolated-four-stage-result.json, isolated-vacuum-{baseline,memory,url}.txt, isolated-settings-{save,reload}.txt, isolated-controller-original-loader.txt. GUI 로그는 시험 폴더 gui-unlocked.log에 보존했다. 개인 통보 파일 이름/내용은 결과 문서에 싣지 않는다.

</details>

<a id="ddmd-launcher"></a>

<details>
<summary>DDMD Computer Use용 격리 앱 실행기</summary>

Source: `ddmd/gateway_poc/isolated-ui/app-launcher/README.md` (historical)

### DDMD Computer Use용 격리 앱 실행기

#### 목적과 판정

2026-09-09, 직접 Java 실행에서는 Computer Use 앱 목록에 GuiBootstrap/com.azul.zulu.java가 나오지만 getApp 선택은 Invalid app이었다. 기존 JDK Info.plist는 com.azul.zulu.jdk, BNDL, libjli.dylib이며 실행용 APPL 번들이 아니었다. 이전 임시 앱은 이 메타데이터를 재사용해 Exec format error가 발생했다.

이를 해결하려고 APPL 번들, 실제 Mach-O 실행 파일, 고유 ID local.hira.ddmd.isolated를 만들었다. 실행기는 자식 java 프로세스로 교체하지 않고 같은 프로세스에서 기존 Zulu libjli의 JLI_Launch로 JVM을 시작한다. 원본 JAR·JVM 및 기존 GuiBootstrap 격리 Guard를 그대로 사용한다. 앱 실행기만 로컬 ad-hoc 서명했으며 TCC/접근성 권한이나 전역 보안 설정을 변경하지 않았다.

Computer Use 내부 구현을 열람한 것은 아니므로 resolver의 정확한 내부 분기는 미확인이다. 다만 기존 직접 실행의 선택 실패와 새 APPL 실행의 선택·조회·클릭 성공을 대조하여 이 앱 식별/실행 구조 조정이 유효함을 확인했다.

#### 실행

- 빌드: 프로젝트 루트에서 `python3 gateway_poc/isolated-ui/app-launcher/build.py`
- 결과 앱: `/private/tmp/hira-ddmd-ui-wtk92jjq/DDMD Computer Use.app`
- Computer Use 최초 선택: `cua.getApp('/private/tmp/hira-ddmd-ui-wtk92jjq/DDMD Computer Use.app')`
- 후속 연결: `cua.getApp('local.hira.ddmd.isolated')`
- 상태 읽기 후 창의 Raise를 수행하면 전면 조작이 가능했다. 이후 메뉴 클릭과 최신 상태 읽기를 반복한다. 접근성 인덱스는 매 상태에서 새로 얻는다.

기존 격리 Java가 실행 중이면 같은 DB를 중복으로 사용하지 않도록 그 프로세스만 먼저 종료한다. 재빌드는 앱을 종료한 상태에서 한다. 고정된 시험 경로와 준비된 원본 라이브러리·컴파일 산출물에 의존하므로 배포용 패키지가 아니다. 시작 후 앱을 열어두며 자동 종료시키지 않는다.

#### 본 화면 표시

원본 start는 본 화면을 자동 표시하지 않는다. 초기화 중 미리 만든 work/in 명령 파일도 정리되었다. 실행기의 제한된 대기 스레드는 이번 실행 로그에서 Application started를 최대 약 30초 동안 기다린 뒤 원본 showpanel standalone 명령을 넣는다. 이 스레드는 메뉴 클릭이나 테스트를 수행하지 않는다. 실제 시험 조작은 Computer Use로만 수행했다.

#### 직접 검증

1. 앱 경로 선택 후 Splash의 접근성 progress indicator 읽기 성공.
2. 본 화면의 스크린샷·메뉴·창 제목 읽기 성공.
3. 고유 앱 ID 재연결 및 창 Raise 성공.
4. 관리 메뉴 클릭 후 AX 메뉴 Value=1 확인.
5. 환경설정 클릭 후 오류 창과 `[1908] 'systemInfo' 패널을 가져오는 도중 오류가 발생하였습니다.` 텍스트 확인.
6. 확인 버튼 클릭 후 본 화면 복귀 확인.

경로 연결 직후 일부 동작은 user changed 보호로 취소됐다. 상태를 다시 읽고 고유 ID로 재연결·Raise한 뒤 위 동작이 성공했다. 이를 UI 성공으로 허위 처리하거나 보호를 우회하지 않았다.

따라서 Computer Use 연결·실제 조작은 해결됐다. JIDE HashMap→RenderingHints 초기화 오류는 재현됐으며 이 실행기에서 수정하지 않았다. 청구·SAM 송신 및 서버 연결은 수행하지 않았다.

구현 참고: OpenJDK JavaAppLauncher가 앱 번들 안에서 JVM을 구동하는 구조를 확인했다. [OpenJDK 8 JavaAppLauncher main.m](https://code.googlesource.com/edge/openjdk/+/jdk8u111-b09/jdk/src/macosx/bundle/JavaAppLauncher/src/main.m). 시험 실행기는 기존 소스를 복사하지 않고 별도로 작성했다.

</details>

<a id="ddmd-summary"></a>

<details>
<summary>HIRA DDMD의 macOS headless 실행 및 GUI 검증 종합</summary>

Source: `ddmd/docs/ddmd-macos-headless-validation-summary.md` (historical)

### HIRA DDMD의 macOS headless 실행 및 GUI 검증 종합

작성일: 2026-09-09 KST
대상 프로젝트: `/Users/<owner>/Playground/HIRA_eform_login`
기준: 2026-09-09까지의 로컬 시험 기록과 증거 파일. 이 문서는 누적 README의 중간 판정을 종합한 최신 요약이며, 신규 서버 요청이나 실행 시험을 수행한 보고서는 아니다.

#### 1. 핵심 결론

**DDMD의 인증·통신·암호·로컬 통보 처리에는 macOS JVM에서 재사용 가능한 Java 구현이 있다.** 네이티브 macOS Java로 실제 HIRA 인증, 토큰 재발급, 통보 조회·다운로드, 로컬 복호화와 통보 생성까지 검증했다.

다만 DDMD 전체를 순수 Java 프로그램이라고 단정할 수는 없다. 배포본에는 Windows 실행기, 레지스트리·프로세스 조회, 보안 연동 및 GUI 결합 부분이 남아 있다. 원본 GUI의 화면과 버튼 동작, 실제 SAM 점검 엔진 전체, 청구 송신은 검증되지 않았다.

현재 판정은 **“macOS headless gateway의 주요 기능은 실증됐으나, 완전한 gateway 및 운영 사용 가능 판정은 미완료”**다. Linux 실행은 직접 시험하지 않았으므로 macOS 결과를 Linux의 검증 완료로 확대하지 않는다.

#### 2. 시작 목적과 승인 범위

진료비청구 프로그램에서 생성하는 SAM 파일과 심평원 송수신 기능을 macOS에서 연계할 수 있는지 확인하는 것이 출발점이었다. 사용자가 macOS 포털 로그인 가능 및 SAM 업로드 기능 부재를 관찰했으나, 이 시험은 포털 전체 기능의 존재·부재를 별도로 증명하지 않는다. 기존 사이트맵도 로그인 후 기능 부재를 입증하는 자료는 아니다.

검증 순서는 Windows CLI 경로 확인, 네이티브 macOS JVM 시험, 실제 인증·통보 처리, GUI·설정·DB 결합 시험이었다. Windows CLI 가능 여부는 사용자가 확인된 것으로 받아들이고 이후 macOS 검증으로 진행했다.

| 구분 | 범위 |
|---|---|
| 실제 서버 | 승인된 인증, 만료 후 재인증, 수신처 인증서 조회, 통보 목록 및 실제 통보 1건 다운로드 |
| 실제 통보 로컬 처리 | 확보한 파일의 복호화, 서명·해시 검증, 원본 코드로 생성 및 백업 |
| GUI·DB 시험 | 설치본 복제, 합성 문서 메타데이터, 기존 실제 통보 ZIP 사본 사용 |
| 지속 제외 | 실제 SAM 청구 송신. SAM 테스트 서버 송신도 이번 검증에 포함하지 않음 |
| 운영 상태 | GUI·DB 시험에서 Windows 운영 DB와 실제 수신 이력을 시험 데이터로 수정하지 않음 |

후속 GUI 시험 중 필요한 서버 연결도 추가로 허용됐지만, 해당 단계는 로컬 문제여서 서버 연결을 사용하지 않았다. 실제 다운로드의 서버 내부 수신 이력 변화는 직접 검증하지 않았다.

#### 3. 시험 환경과 격리 방식

| 환경 | 구성 및 결과 |
|---|---|
| Windows 기준 설치 | `C:\hira\DDMD`, 포함 Java 8u171 32비트 |
| Windows SAM 경로 | 청구 `C:\hira\DDMD\sam\in`, 통보 `C:\hira\DDMD\sam\out` |
| 네이티브 JVM | Azul Zulu 8u504, macOS ARM64, `/private/tmp/hira-jvm-trial/zulu8.96.0.205-ca-jdk8.0.504-macosx_aarch64/Contents/Home` |
| GUI·DB 시험 복제본 | `/private/tmp/hira-ddmd-ui-wtk92jjq` |
| 설치 파일 | 사용자 제공 `/Users/<owner>/Downloads/hira_ddmd_setup.exe` |

JVM은 별도 디렉터리에 설치했고 시스템 JVM 등록이나 전역 PATH/JAVA_HOME 변경을 하지 않았다. GUI 시험에는 전용 폴더와 Java SecurityManager를 사용해 네트워크·하위 프로세스 및 외부 Java 쓰기를 제한했다.

이는 **설치 경로 분리와 실행 제한이며, OS 수준의 완전한 샌드박스를 입증한 것은 아니다.** 임시 경로는 OS 정리로 사라질 수 있다. 실행 스크립트 일부는 해당 시험 경로와 선행 컴파일 산출물에 의존하므로 배포용 실행기나 깨끗한 환경의 원클릭 재현 도구가 아니다.

#### 4. 기능별 최신 판정

| 기능 | 판정 | 확인한 범위와 한계 |
|---|---|---|
| macOS 실제 인증 | 성공 | 원본 인증 관련 JAR 14개로 `CLT_AUTH_REQ`, 유효한 AuthToken 응답 |
| 토큰 수명 관리 | 성공 | 실제 만료 관찰 후 재인증, 새 토큰과 갱신된 만료시각 확인 |
| 수신처 인증서 | 성공 | 실제 조회 응답 1건 |
| 통보 목록 | 성공 | 당일 조건 0건, 이후 최근 90일 조건 12건. 각 조회 당시 결과 |
| 실제 통보 다운로드 | 파일 확보 성공 | 응답 저장부 실패 후 수신 registry의 2개 payload를 복구. 재다운로드 없음 |
| 실제 통보 복호화 | 성공 | RSA/SEED-CBC 복호화, ZIP 구조·CRC 확인 |
| 서명 수학·첨부 무결성 | 성공 | CMS 서명과 서명된 첨부 SHA-256 일치 |
| 서명자 신뢰·폐지 확인 | 미완료 | 로컬 신뢰 검증 실패, CA 체인·신뢰앵커·폐지 상태 미확인 |
| 원본 DAO | 성공 | 합성 통보 등록·조회·상태 변경, SQLite 무결성 확인 |
| 원본 설정 함수 | 성공 | 저장 후 별도 JVM 재로딩 시 시험 설정 일치 |
| 원본 통보 생성 컨트롤러 | 성공 | 로컬 ZIP→파일 생성→백업→DB 상태 변경. GUI 클릭은 아님 |
| 원본 GUI 화면·버튼 | 미확인 | 프로세스·초기화 로그는 확인, 화면 도구의 Java 앱 접근 실패 |
| 실제 SAM 점검 엔진 전체 | 미검증 | 클래스 초기화 수준과 실제 SAM+MEDLOG 처리 성공은 구분 필요 |
| 실제 SAM 청구 송신 | 실행하지 않음 | 사용자 제외 범위 유지 |
| Linux 실행 | 미검증 | 직접 실행 증거 없음 |

#### 5. 실제 인증과 기존 HIRA_eform_login 코드의 역할

기존 macOS 인증서·Keychain 접근 코드와 암호 처리 코드를 활용했다. 인증 경로에서는 필요한 공개 인증서와 VID 관련 입력을 준비해 Java에 전달했고, 실제 개인키·비밀번호 자체를 인증용 JVM에 전달하지 않았다. 실제 통보 복호화에서는 macOS 코드가 개인키를 메모리에서 사용했다.

DDMD 원본 Java 라이브러리는 인증 메시지 구성과 HIRA 통신, 토큰 처리를 수행했다. 따라서 기존 로그인 코드만으로 DDMD 보안 기능 전체를 구현했다고 표현하는 것은 정확하지 않다. **기존 macOS 인증정보 처리 코드와 DDMD 원본 Java 코드를 조합한 경로가 실증된 것**이다.

초기 실제 인증 준비에서는 기관 번호를 Windows 설정에서 읽었다. Windows 의존성을 완전히 제거한 실행기로 만들려면 기관 번호 등 필수 설정을 Mac에서 공급해야 한다.

합성 암호 시험 22개는 통과했지만, 원본 `DdmdMessageSignatureImpl.verify`에는 `DdmdContents.getInstance`의 byte[] 처리 오류가 남았다. 실제 통보는 별도 ASN.1 파싱과 OpenSSL 검증으로 확인했으며 원본 JAR를 수정하거나 해당 검증기를 통과한 것으로 처리하지 않았다.

#### 6. 실제 통보 다운로드·복호화·서명 검증

최근 90일 목록 중 선택한 통보 1건에 대해 인증→목록→`CLT_NTC_REQ`를 호출했다. 서버는 `NtcDoc`과 첨부 2개를 반환했다.

Java의 로컬 파일 저장 단계가 실패했으므로 최초 실행 결과의 `passed=false`는 보존했다. 이후 이미 수신된 registry payload를 Python으로 복사해 파일을 확보했다. 전송부터 최종 저장까지의 실행기가 한 번에 정상 완료된 것으로 해석하면 안 된다.

| 산출물 | 크기·검증 |
|---|---|
| 암호화 통보 CMS | 1,213바이트 |
| 서명 CMS | 2,044바이트 |
| 복호화 ZIP | 762바이트, 구조·CRC 검사 통과 |
| 생성 통보 파일 | 3개, 총 3,596바이트. ZIP 엔트리와 바이트 일치 |

CMS 수학적 서명, 서명된 manifest의 첨부 해시, 복호화 결과의 ZIP 무결성은 확인했다. 그러나 macOS 로컬 신뢰 저장소 검사는 `CSSMERR_TP_NOT_TRUSTED`였고 인증서 폐지 확인도 하지 않았다. **수학적으로 맞는 서명과 HIRA 발신자 신뢰 검증 완료는 별개**다.

실제 파일은 `gateway_poc/private-downloads/` 아래 비공개 로컬 자료로 보관했다. 인증 비밀, 환자·기관 식별자 및 통보 원문은 이 문서에 포함하지 않는다. 다운로드 시 서버 내부에서 수신 이력이 바뀌었는지는 미확인이며 별도 상태 변경 action은 호출하지 않았다.

#### 7. GUI·설정·DB 네 단계 시험

##### 7.1 DB 임시 경로 문제

원본 SQLite JDBC 3.7.2의 `VACUUM`이 `/var/tmp`에 대해 `File.canWrite`를 호출하다 격리 Guard에 차단되는 것을 재현했다. 이후 GUI에서 DB 잠금 오류가 이어졌다.

같은 드라이버에 `PRAGMA temp_store=MEMORY`를 실행하니 VACUUM이 통과했다. JDBC URL 쿼리 매개변수 방식은 효과가 없었다. 시험용 `IsolatedJdbc`를 추가해 연결 직후 PRAGMA를 실행하고 원본 설정의 `driver.class.name`과 `url`로 선택했다. 적용 후 GUI 로그에서는 기존 `SQLITE_BUSY`가 관측되지 않았다.

원본 배포 JAR는 바꾸지 않았지만 시험 드라이버와 설정 조정은 추가됐다. 따라서 아무 조정 없는 원본 실행과 구분한다.

##### 7.2 Windows 전용 기능

`launcher.exe`, `tasklist`, `reg` 호출 실패가 남았다. 실행 제한 아래에서도 이후 Launcher 초기화와 수신함 SQL 실행은 이어졌다. 이 관찰만으로 모든 Windows 의존성이 무해하거나 제거 가능하다고 단정하지 않는다.

##### 7.3 실제 창 접근

실행 중인 `GuiBootstrap`은 앱 목록에 나타났다. 처음에는 Mac 잠금에 막혔고, 사용자 잠금 해제 후에도 앱 ID 선택은 `Invalid app`, JDK 번들 경로는 실행 앱 찾기 실패, 시험용 번들 경로는 `Exec format error`를 반환했다.

이는 도구가 화면 검증을 수행하지 못했다는 증거다. DDMD 창이 정상 표시됐거나 표시 자체가 불가능하다는 증거로 사용할 수 없다. 화면 표시, 수신함 행, 설정 버튼, 통보 생성 버튼 동작은 여전히 미확인이다.

##### 7.4 설정·통보 처리 흐름

원본 `SystemInfoController.saveProperties`로 합성 기관 번호, 입출력 경로, 백업 기간, 보안 옵션을 저장했다. 새 JVM에서 읽은 값이 모두 일치했다.

통보 생성 시험은 원본 `ApplicationBootstrap`의 클래스 로더를 사용하고 `ReceiveController.zipReleaseCont`를 reflection으로 직접 호출했다. 원본 `DocumentUtils.asFileName` 규칙으로 입력 ZIP을 배치했다. 반환값 true, DB 상태 `1`, 파일 생성·일반 백업·월별 백업의 바이트 일치를 확인했다.

이 시험에서 화면 객체와 진행창은 null이었다. 실제 ZIP과 합성 메타데이터를 사용했으며 운영 수신 이력을 복원한 것이 아니다. **원본 컨트롤러의 로컬 흐름은 검증됐지만 GUI 이벤트 연결은 검증되지 않았다.**

#### 8. 변경 및 종료 상태

- 원본 배포 JAR와 복제본의 원본 JAR 바이트 일치 확인.
- 복제 원본 DB의 준비 시점 SHA-256 유지 확인.
- 시험 DB `integrity_check=ok` 확인.
- 마지막 격리 GUI 프로세스 종료 확인.
- GUI·DB 후속 시험의 서버 연결 0회, 실제 SAM 청구 송신 없음.
- 이번 문서 작성은 기존 증거 정리만 수행하며 인증정보 접근이나 서버 재시험을 포함하지 않음.

#### 9. 다음 검증 과제

1. **GUI 관측 경로 확보:** 실행 중인 Java 창을 도구가 선택할 수 있는 방식 또는 사용자 직접 관측으로 화면 존재부터 확인한다. 접근 실패를 화면 정상 판정으로 대체하지 않는다.
2. **GUI 사용자 흐름:** 설정 저장→종료·재실행→설정 유지→시험 통보 표시→생성 버튼→파일·DB 일치를 같은 복제 환경에서 검증한다.
3. **실행기 안정화:** 다운로드 후 로컬 저장 실패를 해결하고, 설정·원본 클래스 로더·시험 JDBC 적용을 재현 가능한 실행기로 정리한다.
4. **신뢰 검증:** 실제 서명자의 CA 체인·신뢰앵커·폐지 확인과 원본 메시지 검증 파서 호환성을 검증한다.
5. **SAM 점검:** 검증 가능한 비운영 SAM+MEDLOG 묶음으로 파싱·점검·결과 생성을 시험한다. 서버 송신은 기존 제외 범위와 별도로 결정한다.
6. **Linux:** 별도 환경에서 인증·암호·SQLite·파일 처리 경로를 실행해 판단한다.

#### 10. 근거 문서와 증거

아래 링크는 이 문서 위치를 기준으로 한 프로젝트 내 상대 경로다. 증거 JSON의 조회 건수·유효기간·파일 상태는 각 시험 시점의 관측이다.

| 내용 | 근거 |
|---|---|
| Windows 설치본 정적 조사 | [초기 분석](ddmd-integration-analysis.md) |
| SAM 테스트 경계 | [송신 시험 경계](ddmd-sam-test-boundary.md) |
| macOS JVM 누적 기록 | [JVM 기록](#ddmd-macos) |
| GUI·DB 상세 | [격리 시험 기록](#ddmd-isolated) |
| 실제 인증 | 인증 결과: `ddmd/gateway_poc/evidence/macos-live-auth-result.json` (local only) |
| 토큰 재발급 | 수명 관리 결과: `ddmd/gateway_poc/evidence/macos-lifecycle-result.json` (local only) |
| 다운로드 복구 | 파일 확보 결과: `ddmd/gateway_poc/evidence/macos-download-recovered.json` (local only) |
| 복호화·서명 | 검증 결과: `ddmd/gateway_poc/evidence/macos-notice-verification.json` (local only) |
| 네 단계 종합 | 최신 결과: `ddmd/gateway_poc/evidence/isolated-four-stage-result.json` (local only) |

누적 README에는 당시의 “아직 미검증” 문장이 이력으로 남아 있다. 최신 기능별 판정은 이 문서와 각 문서의 마지막 후속 시험 결과를 함께 기준으로 삼는다.

#### 11. 시작 화면만 보였던 원인 — 2026-09-09 07:52 KST 후속 확인

사용자 캡처로 macOS에서 LauncherSplash가 실제 표시됨을 확인했다. 원본 바이트코드에서 Launcher.doLoad는 StandaloneFrame을 생성·캐시하지만, ClientContext.openFrame 자체는 표시하지 않는 것을 확인했다. 별도 `showpanel standalone` 명령의 Launcher$4.run이 Frame.showFrame을 호출한다. 기존 시험은 bootstrap start만 반복했고 이 표시 명령을 보내지 않았다.

실행 중인 격리 복제본의 work/in에 원본 FileCommandParser 형식으로 `command = showpanel`, `arguments = standalone` 및 완료 마커를 넣었다. 07:52:33 KST 로그에서 원본 watcher→dispatcher→showpanel standalone 처리를 확인했다. update 인자는 사용하지 않았으며 네트워크 차단은 유지했다. 이후 AWT 이벤트 큐의 처리 로그도 이어졌다. 실제 본 화면 표시와 버튼 동작은 사용자 캡처로 추가 확인해야 한다. 따라서 앞선 화면 도구 접근 실패만을 본 화면 미표시의 원인으로 해석하지 않는다.

#### 12. 사용자 화면 및 클릭 증거 — 2026-09-09 07:53 KST

사용자 제공 07:52:47 캡처에서 macOS 창 장식, 진료비청구 프로그램 제목, 메뉴·아이콘·한글이 있는 본 화면을 확인했다. 본 화면 표시 판정은 미확인에서 확인으로 갱신한다.

이어 환경설정 클릭 후 07:53:31 캡처에서 `[1908] 'systemInfo' 패널을 가져오는 도중 오류가 발생하였습니다` 대화상자를 확인했다. 07:53:24 실행 로그에 TopIconMouseListener.mouseReleased → FrameActions.showPanel → MDIPanelManager.showPanel → systemInfo 리소스 생성 경로가 기록됐다. 따라서 클릭 이벤트 전달 자체는 확인됐고, 환경설정 패널 생성은 실패했다.

최초 원인은 JideSwingUtilities 정적 초기화의 `ClassCastException: java.util.HashMap cannot be cast to java.awt.RenderingHints`다. SystemInfoFrm.createFolderChooser → JIDE FolderChooser 경로에서 발생했다. 뒤의 NoClassDefFoundError는 이 초기화 실패에 따른 후속 오류이며 JAR 누락으로 단정하지 않는다. 같은 원인으로 백업 관련 패널 초기화도 실패한 로그가 있다. 앞서 관측한 Windows reg 호출 실패나 DB 잠금과는 별개의 GUI 라이브러리 오류다. 원본 설정 함수의 CLI 저장 성공은 이 패널의 성공을 의미하지 않는다.

최신 판정: 본 화면 표시 확인, 환경설정 클릭 이벤트 연결 확인, 환경설정 패널 생성 실패. 다음 조사 대상은 JIDE가 RenderingHints로 변환하는 값의 출처와 macOS JVM에서의 호환 처리다.

#### 13. Computer Use 앱 선택 해결 및 직접 클릭 검증

2026-09-09 후속 시험에서 고유 앱 ID `local.hira.ddmd.isolated`와 실제 Mach-O 실행 파일을 가진 격리 APPL 번들을 만들었다. 실행기가 동일 프로세스 안에서 기존 JVM을 구동하도록 하여 Computer Use가 앱 경로와 고유 ID 양쪽으로 선택할 수 있게 됐다. 원본 JAR와 기존 Guard는 유지했다.

Computer Use로 본 화면 스크린샷·접근성 트리를 읽고 창을 전면으로 가져온 뒤 관리→환경설정을 직접 클릭했다. `[1908] systemInfo` 오류를 확인하고 확인 버튼으로 닫아 본 화면으로 복귀했다. 따라서 앱 선택·화면 읽기·클릭·오류 대화상자 조작은 직접 검증됐다. 이전 절의 Computer Use 미접근 상태를 갱신한다. JIDE 초기화 오류는 해결하지 않았다.

실행 방법: [앱 실행기 설명](#ddmd-launcher). 증거: Computer Use 결과: `ddmd/gateway_poc/evidence/computer-use-app-result.json` (local only). 앱은 후속 시험을 위해 실행 상태로 남겼으며 서버 연결·청구 송신은 하지 않았다.

#### 14. Computer Use 직접 GUI 범위 확대

2026-09-09 08:04–08:12 KST에 12개 주요 메뉴·진입 경로를 직접 시험했다. 화면 7개 표시 성공, JIDE 관련 화면 4개 실패, SAM 부재 안내 1개를 확인했다. 통보 생성 화면에서 시험 문서 목록·상세는 표시됐지만 생성 대상 선택이 처리되지 않아 GUI 생성 완료는 미확인이다. [직접 GUI 시험 보고서](#ddmd-gui)에 항목별 결과와 입력·접근성 한계를 기록했다. 실제 SAM 송신은 하지 않았다.

#### 실제 업데이트 추가 시험 (2026-09-09)

별도 후보에서 실제 업데이트 21개 수신(14,574,849 bytes), 원본 UpdController 적용, 21개 해시·버전 및 기준자료 DB 11개 검증, macOS 앱 재실행을 확인했다. 적용 후 서버 재조회는 추가 0개였다. 원본 Windows 자동 재시작과 업데이트 결과 보고 수락은 미검증이다. [상세 업데이트 시험](#ddmd-update)을 참조한다.

</details>

<a id="ddmd-gui"></a>

<details>
<summary>DDMD macOS Computer Use 직접 GUI 시험</summary>

Source: `ddmd/docs/ddmd-computer-use-test-report.md` (historical)

### DDMD macOS Computer Use 직접 GUI 시험

시험일: 2026-09-09, 08:04–08:12 KST
대상 앱: `local.hira.ddmd.isolated` / DDMD Computer Use.app
목적: 원본 화면·메뉴·클릭 동작을 직접 시험하고 성공, 실패, 미확인을 구분한다.

#### 결론

후속 상태: 환경설정 및 나머지 3개 화면의 JIDE 초기화 오류는 수정 후 재시험에서 재현되지 않았다. 아래 최초 결과는 역사적 기록이며, 현재 결과는 문서 마지막의 후속 시험을 참조한다.

Computer Use로 **12개 주요 메뉴·진입 경로**를 시험했다. 7개 화면이 열렸고, 4개 화면이 실패했으며, 청구파일점검에서는 SAM 부재 안내를 확인했다. 이는 화면 진입의 분류이며 해당 업무 전체의 성공률을 뜻하지 않는다.

통보 생성 화면에는 합성 통보 1건과 상세정보가 실제 표시됐다. 생성 버튼도 반응했지만 대상 선택이 처리되지 않아 GUI 생성 완료는 확인하지 못했다. 기존 CLI 컨트롤러 시험의 생성 성공과 구분한다.

#### 시험 조건

- 원본 JAR, macOS ARM64 Zulu 8u504, 기존 격리 DB와 합성 메타데이터 사용.
- 실제 다운로드 통보 ZIP 사본은 기존 로컬 자료이며 새로 다운로드하지 않음.
- 네트워크·하위 프로세스 실행 차단 유지, 실제 SAM 청구 송신 제외.
- GUI 조작은 Computer Use로 수행. 로그·DB·문서 확인만 CLI 사용.
- 프로그램 정보→로그→통보 생성→점검→서식→관리→통보 수신→사전점검→청구 목록 순으로 진행. 중간 실패 후에도 독립된 다음 시험을 계속함.

#### 메뉴별 결과

| 번호 | 항목 | 직접 확인한 결과 | 한계 |
|---|---|---|---|
| 1 | 프로그램 정보 | 정보 패널, 모듈·버전·업데이트 표 표시 | 개별 버전 정보의 정확성은 대조하지 않음 |
| 2 | 로그 조회 | 시스템 로그 표시, 수신 로그 라디오 전환과 내용 변경 | 03시대 SQLite 오류는 과거 기록이며 이번 시험 오류로 세지 않음 |
| 3 | 통보서 생성 | 목록 1건, 합성 문서 ID, 문서수 3, 762byte 상세 표시 | 생성 완료는 미확인 |
| 4 | 청구파일 점검 | SAM파일을 찾을 수 없다는 구체적인 안내 표시, 확인 버튼 복귀 | 실제 SAM 점검 알고리즘 미검증 |
| 5 | 점검 오류 조회 | 오류 목록·상세 테이블·입력 필드 표시 | 시험 오류 데이터가 없어 실제 오류 내용 탐색 미검증 |
| 6 | 청구파일 서식 조회 | JideSwingUtilities 초기화 오류 대화상자 | 화면 진입 실패 |
| 7 | 백업 | `[1908] backup` 패널 오류, 확인 버튼 복귀 | 백업 작업 미실행 |
| 8 | 청구파일 암호화 관리 | `[1908] backupDec` 패널 오류, 확인 버튼 복귀 | GUI 암호화·복호화 미실행 |
| 9 | 통보서 수신 | 필터·수신 목록·상세정보 영역 표시 | 인증·서버 검색·다운로드 미실행 |
| 10 | 사전점검서비스 | 필터와 빈 목록 0건 표시 | 점검 데이터 제출·송신 미실행 |
| 11 | 청구 | 청구 목록 화면 0건 표시 | 실제 송신 버튼은 누르지 않음 |
| 12 | 환경설정 | `[1908] systemInfo` 오류 재현, 확인 버튼 복귀 | 설정 UI 저장 미실행 |

#### 통보 생성의 세부 결과

`ISOLATED-NOTICE-001` 합성 문서가 조회됐다. 원본 ZIP의 개인정보를 표시한 것이 아니라 시험 메타데이터를 연결한 목록이다. 상세정보의 문서수 3과 파일크기 762byte가 기존 시험 값과 일치했다.

접근성 헤더 체크박스는 0→1로 바뀌었다. 그러나 생성 버튼은 “통보서 생성 대상이 지정되지 않았습니다.”를 표시했다. 테이블에 포커스를 주고 Ctrl+Home·Space로 선택한 뒤에도 같은 안내가 나왔다. 헤더 값 변경이 실제 행 선택 이벤트까지 전달되지 않았는지, 테이블 키보드 동작의 문제인지는 미확정이다. 문서 자체의 생성 불가능 판정으로 확대하지 않는다.

일부 버튼은 접근성 이름이 비어 있었다. 스크린샷 좌표 클릭은 원하는 동작이 확인되지 않았고, 접근성 버튼 탐색 중 닫기와 생성 안내 동작을 구분했다. 실제 파일 생성·DB 갱신을 GUI에서 완료했다고 기록하지 않는다.

#### 입력·표시 한계

- 통보 수신 날짜 선택 버튼, 청구구분 콤보 클릭, 날짜 필드 setValue 시도에서 원하는 상태 변화를 확인하지 못했다. 사용자 직접 입력도 불가능하다고 단정하지 않는다.
- 스크린샷에는 일부 날짜·고객센터 문구가 잘리거나 좁게 보였다. 한글 전체 렌더링 실패와는 구분하며, 화면 배율·폭에 따른 재검증이 필요하다.
- 일부 조작은 Computer Use의 user changed 보호로 취소됐다. 최신 상태를 읽고 Raise 후 진행했으며 보호를 우회하지 않았다.
- 로그 패널이 열린 상태에서 접근성 트리가 길어졌다. 후속 관측에서는 필요한 패널·메뉴 부분만 출력했다.

#### 오류 분류

환경설정·백업·암호화 관리의 로그와 서식 조회 대화상자는 JIDE 초기화 문제로 연결된다. 최초 원인은 기존에 확인한 `HashMap cannot be cast to RenderingHints`이며, 후속 `Could not initialize class`를 JAR 파일 부재로 해석하지 않는다.

청구파일점검의 SAM 부재 안내는 입력 조건 확인 결과다. 통보 생성 대상 미선택 안내는 선택/이벤트 처리 경계의 미완료다. 이 둘은 JIDE 패널 생성 오류와 구분한다.

#### 보존과 검증 근거

시험 후 원본 설치 DB의 준비 시점 해시 유지, 시험 DB integrity_check=ok, 합성 통보 DB 상태 1을 확인했다. 상태 1은 이전 CLI 시험에서 이미 만들어진 값이므로 이번 GUI 생성 성공의 증거가 아니다. 앱은 후속 시험을 위해 실행 상태로 남겼다.

- 구조화된 결과: `ddmd/gateway_poc/evidence/computer-use-gui-coverage.json` (local only)
- [전체 검증 종합](#ddmd-summary)
- [Computer Use 앱 실행기](#ddmd-launcher)
- 현재 실행 로그: `/private/tmp/hira-ddmd-ui-wtk92jjq/gui-app-bundle.log`

08:04:28 about, 08:04:37 log, 08:05:24 ntcDocGen, 08:08:57 exam.error.list, 08:10:16 receive, 08:11:04 preExamSend, 08:11:32 send 패널 활성화 로그를 화면 관측과 대조했다. GUI 캡처와 접근성 응답은 이 대화의 Computer Use 도구 결과에 있다.

#### 다음 시험 단위

1. JIDE RenderingHints 호환성 수정 후 실패한 4개 화면을 같은 시나리오로 재시험.
2. 통보 테이블 행의 실제 체크 이벤트를 확인하고, 생성 버튼→결과 파일·백업·DB 갱신까지 검증.
3. 이름 없는 버튼과 날짜·콤보 입력의 접근성 동작을 확인. 자동화 실패와 사용자 조작 실패를 구분.
4. 비운영 SAM+MEDLOG가 준비되면 파일 점검 경로를 검증. 실제 청구 송신은 계속 별도 범위로 둠.

프로그램 업데이트, 외부 포털·원격지원 링크, 실제 송신, 삭제는 이번 GUI 시험에서 실행하지 않았다.

#### 2026-09-09 후속 수정 및 세 화면 재시험

앞의 08:04–08:12 실패 기록은 수정 이전 관측이다. 환경설정 오류 수정 이후
Computer Use로 백업·청구파일암호화관리·청구파일서식조회 화면 진입을 재시험했고,
수정 후 앱 재시작을 거쳐 세 화면 모두 다시 열리는 것을 확인했다.

- 백업: Source/Target 입력란, 실행·닫기 버튼, 진행 표시가 나타남.
- 암호화 관리: 경로, 검색·복호화·닫기 버튼, 빈 파일 목록이 나타남.
- 서식 조회: 별도 창과 건강보험 서식 목록, 청구·통보 경로가 나타남. 다수 서식 버튼은 비활성 상태이며 개별 서식 조회 성공을 뜻하지 않음.
- 기존 JIDE 형변환 및 클래스 초기화 오류는 새 실행 로그에 없음.

추가로 서식 조회 원본 main은 null 인자의 첫 원소를 읽다 NPE를 출력한 뒤
기본값 "0"으로 복구했다. 격리 Java 8 agent가 해당 main의 진입에만 인자
보정을 추가해 null/빈 인자를 {"0"}으로 바꾼다. 다른 인자는 유지한다.
원본 JAR 파일은 변경하지 않았고, 변환은 실행 중 로드되는 클래스에만 적용된다.
재시작·직접 메뉴 클릭 후 adapter 표시 1회와 NPE/VerifyError/NoClassDefFoundError 0건을 확인했다.

암호화 관리 경로의 화면 표시는 Windows식 역슬래시가 남지만 내부 로그에는
정규화된 슬래시 경로가 출력된다. 실제 파일 검색·복호화 경로 전체는 미검증이다.
기존 Windows 프로세스 호출에 대한 격리 Guard 거부 로그는 남으며, 이를 JIDE 오류로 분류하거나
전체 앱 오류가 0건이라고 보고하지 않는다. 이번에는 백업·복호화 실행이나 SAM 송신을 하지 않았다.

- [환경설정/JIDE 수정](#ddmd-jide)
- [서식 조회 인자 보정 소스](../gateway_poc/isolated-ui/SamViewArgumentsAgent.java)
- 세 화면 재시험 증거: `ddmd/gateway_poc/evidence/jide-three-screen-retest.json` (local only)

실행기는 빌드 시 두 호환 소스를 Java 8로 컴파일하고 agent를 패키징한다.
이 agent는 Java 8 내부 ASM API에 의존하므로 다른 JVM으로의 일반 호환성을 보장하지 않는다.

</details>

<a id="ddmd-jide"></a>

<details>
<summary>macOS DDMD 환경설정 오류 수정</summary>

Source: `ddmd/docs/ddmd-jide-settings-fix.md` (historical)

### macOS DDMD 환경설정 오류 수정

2026-09-09, 격리 Zulu 8u504 / macOS 26.6.2에서 검증.

#### 원인과 수정

원본 JIDE 2.11.2의 JideSwingUtilities 정적 초기화가 Toolkit의
`awt.font.desktophints`를 RenderingHints로 직접 형변환한다.
현재 macOS JVM에서는 HashMap이 반환돼 ClassCastException이 발생하고,
환경설정 패널은 후속 `[1908] systemInfo` 오류로 열리지 않았다.

GuiBootstrap에서 원본 DDMD 초기화 전에 해당 Map의 내용을 RenderingHints로
복사하고 이 JVM의 Toolkit 캐시에 설정하도록 했다. macOS이며 값이 Map이고
RenderingHints가 아닌 경우에만 적용한다. 원본 JIDE JAR와 OS 설정은 변경하지 않았다.
기존 네트워크·하위 프로세스 실행 차단 Guard는 유지한다.

#### 직접 검증

- 컴파일 성공, 격리 앱 재시작 후 HashMap 정규화 로그 확인.
- 새 실행 로그에 기존 형변환 및 systemInfo 1908/1990 오류 없음.
- Computer Use 관리→환경설정 클릭으로 실제 패널 표시 확인.
- 합성 기관번호 00000000, OS·CPU·메모리, 청구·통보 SAM 경로 표시 확인.
- 닫기 버튼으로 닫은 후 같은 메뉴로 재진입 성공.
- 원본 설치본과 격리 JIDE JAR SHA-256 동일.

설정 저장은 이번 검증에 포함하지 않았다. 다른 패널, 파일 선택 대화상자,
실행 중 OS 글꼴 설정 변경, 다른 JVM 버전의 호환성은 별도 검증이 필요하다.
이 수정은 Java 8의 Toolkit protected 메서드에 대한 reflection에 의존한다.
앱은 환경설정 화면을 연 상태로 남겼다. 실제 SAM 송신은 수행하지 않았다.

소스: [GuiBootstrap.java](../gateway_poc/isolated-ui/GuiBootstrap.java)

증거: jide-settings-fix.json: `ddmd/gateway_poc/evidence/jide-settings-fix.json` (local only)

기존 GUI 시험 보고서의 실패 기록은 수정 이전의 관측으로 보존한다.

</details>

<a id="ddmd-update"></a>

<details>
<summary>DDMD macOS 실제 업데이트 시험</summary>

Source: `ddmd/docs/ddmd-macos-update-test.md` (historical)

### DDMD macOS 실제 업데이트 시험

2026-09-09 08:37–08:45 KST. macOS ARM64 Zulu Java 8u504.

#### 결과

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

#### 환경과 보존

후보 경로: `/private/tmp/hira-jvm-trial/hira-live-auth-update-gkcc7n7q/candidate`

기존 성공 GUI 경로 `/private/tmp/hira-ddmd-ui-wtk92jjq`에 업데이트를 적용하지 않았다.
원본 신규 설치본을 별도 복사하고 합성 기관번호 00000000과 후보 전용 경로를 설정했다.
실제 기관번호와 인증서 자료는 기존 인증 도구를 통해 stdin으로만 전달했다.
후보 앱 ID는 `local.hira.ddmd.update-isolated`로 기존 앱과 구분된다.
실제 SAM 청구 및 통보 송수신 action은 수행하지 않았다.

수신 단계는 HIRA endpoint로 제한한 기존 headless 인증 경로를 사용했다.
적용·GUI 단계는 네트워크와 하위 프로세스를 차단하는 기존 Guard를 유지했다.
이는 OS 전체 샌드박스의 증명이 아니다.

#### 시험 중 수정한 사항

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

#### 남은 범위

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

#### 근거

- 종합 결과: `ddmd/gateway_poc/evidence/macos-update-summary.json` (local only)
- 최초 조회: `ddmd/gateway_poc/evidence/macos-update-result.json` (local only)
- 수신 성공: `ddmd/gateway_poc/evidence/macos-update-download-result.json` (local only)
- 첨부 검증: `ddmd/gateway_poc/evidence/macos-update-files.json` (local only)
- 적용·DB 검증: `ddmd/gateway_poc/evidence/macos-update-applied.json` (local only)
- 최종 서버 재조회: `ddmd/gateway_poc/evidence/macos-update-postcheck-result.json` (local only)

실행 소스는 `gateway_poc/update/`에 있다. prepared.json과 modules.tsv 및 복사본에
의존하는 이번 시험용 도구이며 배포용 자동 업데이트 서비스가 아니다.

#### 자동 실행기 후속 구현

이 문서의 단계별 수동 연결 이후, 한 번의 실행으로 수신·적용·macOS 앱 시작·서버 결과 응답·최종 조회까지 연결한 실행기를 검증했다. [구현 및 검증](#ddmd-auto-update)을 참조한다. 원본 GUI 버튼 및 OS 스케줄 연동은 여전히 별도 범위다.

</details>

<a id="ddmd-auto-update"></a>

<details>
<summary>macOS DDMD 자동 업데이트 구현 계획</summary>

Source: `ddmd/docs/ddmd-auto-update-plan.md` (historical)

### macOS DDMD 자동 업데이트 구현 계획

- 목표: 한 번의 실행으로 조회·수신·해시 검증·원본 적용·후보 빌드·재실행·결과 보고·최종 조회를 연결한다.
- 범위: 전용 로컬 runtime, 기존 macOS 인증 로더와 원본 DDMD 업데이트 action. SAM 송신은 제외한다.
- 완료: 실서버에서 갱신이 있는 설치본을 자동으로 전환하고 결과 응답 및 추가 갱신 0개를 확인한다. 두 번째 실행은 불필요한 적용/재시작 없이 종료한다.
- 보존: 후보 검증 전 기존 파일을 변경하지 않는다. 이전 버전과 실패 후보를 남기고 원자적으로 active.json을 교체한다. 중복 실행은 잠금으로 거부한다.
- 보고: 원본 updated.dat를 JVM 재시작 전에 별도 보관한다. 서버 응답 전에는 삭제하지 않는다. 통신 결과가 모호하면 자동 재전송하지 않고 pending 상태를 남긴다.
- 검증: 해시 불일치·경로 이탈·중복 실행 차단 및 실서버 전체 흐름, 재실행 무변경, Computer Use 화면 확인.

macOS native 실행기와 Java 8 호환 처리를 재사용한다. 이번 구현은 호출 시 자동 갱신하는 실행기로 만들며 OS 부팅 서비스나 정기 스케줄 등록은 포함하지 않는다. 인증서 저장소 잠금 시에는 우회하지 않고 실패 상태를 보존한다.

#### 구현 및 실제 검증 결과

2026-09-09 08:54경 단일 명령으로 모듈 13개 적용, 후보 앱 실행,
CLT_MOD_UPT_RES의 예외 없는 null 응답, 재조회 추가 0개까지 완료했다.
적용된 모듈 해시 및 기준자료 DB 10개 quick_check를 확인했다.
두 번째 실행은 변경 없음으로 종료됐고 PID 21585가 유지됐다.
Computer Use에서 본 화면·환경설정 표시를 확인했다.
안전/실패 경로 단위 검사 7개 통과. 서버 내부 감사 저장은 별도 미검증이다.

- [실행기](../gateway_poc/auto-update/run.command)
- [사용법 및 제약](../gateway_poc/auto-update/README.md)
- 증거: `ddmd/gateway_poc/evidence/macos-auto-update-result.json` (local only)

원본 GUI 업데이트 버튼과 OS 스케줄에는 연결하지 않았다. 현재는 실행기 호출 시
전체 자동 처리하며, 운영 설치/데이터 이전 없이 기존 격리 임시 경로를 사용한다.

</details>

<a id="ddmd-cleanup"></a>

<details>
<summary>DDMD 시험 환경 정리</summary>

Source: `ddmd/docs/ddmd-environment-cleanup.md` (historical)

### DDMD 시험 환경 정리

2026-09-09 사용자 요청으로 시험을 종료하고 이번에 설치한 외부 실행 환경을 삭제했다.

#### 삭제 범위

- `/private/tmp/hira-jvm-trial`: Zulu ARM64 JDK 8u504, 다운로드 아카이브, JVM 시험 실행 복사본.
- `/private/tmp/hira-ddmd-inspect`: 외부 ECJ 컴파일러와 분석용 배포 바이너리 복사본.
- `/private/tmp/hira-ddmd-ui-wtk92jjq`: 임시 GUI 실행 환경.
- `/private/tmp/hira-ddmd-auto-runtime`: 정식 경로 이전 후 남은 임시 자동 업데이트 실행 환경.
- `.local/ddmd/*/candidate/jre18` 2개: 정식 DDMD 복사본에 포함된 Windows JRE.

#### 보존 및 검증

삭제 전 소스·설정·로그·바이트코드 분석 텍스트 등 290개를 `.local/ddmd/cleanup-archive-20260909/`에 보존했다. 비공개 자료가 포함될 수 있으므로 Git에서 제외하며 공개하지 않는다. 삭제 대상 디렉터리의 심볼릭 링크를 따라 외부 파일을 삭제하지 않았다.

정식 DDMD 복사본의 lib/data 파일 370개는 삭제 전후 SHA-256이 일치했다. 개발 소스, 연구 문서, 정식 로컬 DB·통보 자료, NPKI 인증서·Keychain, 사용자가 제공한 Downloads 설치파일과 원격 Windows 설치본은 보존했다.

삭제 대상 7개 경로의 부재를 확인했다. 관련 Java 실행 프로세스는 없었고, macOS `java_home -V`는 설치된 JVM을 찾지 못했다. Applications와 시스템 Java 등록 경로 및 Homebrew Caskroom에서 Zulu 설치를 발견하지 않았다.

현재 GUI와 자동 업데이트는 실행 환경이 제거된 상태다. 역사적 시험 성공 기록은 당시 환경의 결과이며 현재 실행 가능함을 의미하지 않는다. 재실행 시 외부 JVM을 별도 설치하고 `.local/ddmd/config.json`의 java 경로를 갱신해야 한다. 이번 정리에서는 인증 서버 연결과 SAM 송신을 수행하지 않았다.


</details>
