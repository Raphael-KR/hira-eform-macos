# SAM 제외 headless gateway 검증

- 목표: 실제 인증의 수명·복구와 비청구성 조회를 Windows headless 경로로 검증한다.
- 범위: 별도 임시 Java 실행부, 기존 macOS 키 공급 코드, 실제 인증 및 읽기 전용 공개 인증서/수신처 메타데이터 조회 후보.
- 완료: 실제 만료 관찰 후 새 토큰 발급, 독립 프로세스에서 인증 복구, 토큰 사용 조회, 통신·인증 오류의 안전한 처리와 근거 기록.
- 제외: SAM 송신·사전점검·청구, 운영 통보 조회/수신, DDMD 설치본·기관 DB 수정, 서비스 설치, 잘못된 인증서·비밀번호를 운영 서버에 보내는 시험.
- 검증: 원본 코드와 조회 의미를 먼저 확인한다. 실제 인증 만료는 시계를 조작하지 않고 기다린다. 네트워크 차단·비정상 인증 응답은 로컬 fault injection으로 검증하여 실제 서버 장애·잘못된 자격증명 거절 검증과 구분한다.

비밀번호·개인키는 Mac 밖으로 보내지 않는다. 토큰과 인증 키는 메모리에만 보관한다. 단일 실행부가 지원하는 고정 명령만 사용하며 임의 action은 지원하지 않는다. 기존 `live/LiveAuth.java`와 이전 성공 기록은 보존한다.

## 2026-09-09 결과

| 항목 | 실행 결과 | 증거 |
|---|---|---|
| 실제 만료 후 재인증 | 02:43:22–02:48:25 KST. 발급된 약 5분 만료시각까지 실제 대기했고, 새 tokenId와 더 늦은 만료시각을 받은 것을 메모리에서 비교 | [lifecycle](../evidence/gateway-lifecycle-result.json) |
| 토큰 사용 조회 | `CLT_CERT_REQ`로 현재 기관의 수신처 공개 인증서 1건 조회. 토큰 식별자·verifier·timestamp·MAC 헤더를 사용했고 응답의 AuthToken·RecpHbrRes를 복원. 첨부파일 없음 | [recipient](../evidence/gateway-recipient-result.json) |
| 프로세스 종료 후 인증 복구 | lifecycle 프로세스 종료 후 02:49:28–02:49:32 KST에 별도 SSH/JVM에서 인증 성공. 이전 토큰 파일이나 GUI 로그인 상태를 사용하지 않음 | [auth](../evidence/gateway-auth-result.json) |
| 인증 응답 오류 | 잘못된 직렬화 헤더를 로컬에서 주입하여 거부됨을 확인 | [failure-tests](../evidence/gateway-failure-tests-result.json) |
| 네트워크 오류 | 정상 인증 후 연결 직전 강제 차단. DDMD 예외로 반환하며 프로세스가 계속 동작하고 기존 미만료 토큰을 보존 | [failure-tests](../evidence/gateway-failure-tests-result.json) |
| SAM 명령 제외 | Node CLI에서 `sam`을 exit 2로 거부. 이 검사는 Keychain 조회·SSH 시작 전 수행 | [summary](../evidence/gateway-summary.json) |

네트워크 오류 시험의 `requests=2`는 정상 인증 1회와 연결 전에 차단된 send 호출 1회의 합이다. 잘못된 자격증명을 실제 HIRA 서버에 보낸 것은 아니다. 만료된 토큰을 서버에 제출해 거절시키지도 않았으며, 서버가 준 만료시각을 기준으로 재인증한 것이다. 서버 측 장애·계정 잠금·비밀번호 오류 응답의 실환경 검증으로 확대 해석하지 않는다.

조회는 원본 DDMD `SendController`의 `RecpHbrReq`를 이용하는 읽기 전용 인증서 조회다. `ClientConstants`에서 건강보험 코드 `Y`를 확인했고, 현재 날짜를 수신처 적용일 조회 조건으로 사용했다. 환자·SAM·청구문서 ID를 넣지 않았다. 원본 일반 조회는 MXS를 사용하지만, 이번 독립 실행부는 기존 MSI transport에서 같은 action·암호화 DTO 및 원본 MXS의 토큰 MAC 헤더 방식을 사용해 실제 서버 수용을 검증했다. 따라서 MXS/ebMS 전체를 검증했다는 뜻은 아니다.

첫 조회 실행은 응답의 공개 인증서가 Java `CertificateRep.readResolve`를 거쳐 복원되는 과정에서 클래스 필터에 걸렸다. 표준 구현 `sun.security.x509.X509CertImpl`만 추가한 뒤 재실행에 성공했다. 최초 실패는 시간별 JSON에 보존했다. 토큰·인증서 내용·응답 payload는 저장하지 않았다.

`RecipientProbe`는 응답 토큰의 만료 갱신과 verifier 갱신 코드를 포함한다. 이번 조회 한 번의 성공만으로 장시간 연속 요청·동시성·무중단 갱신까지 검증한 것은 아니다.

## 실행

```sh
python3 gateway_poc/gateway/prepare.py
node gateway_poc/gateway/run.mjs auth
node gateway_poc/gateway/run.mjs lifecycle
node gateway_poc/gateway/run.mjs recipient
node gateway_poc/gateway/run.mjs failure-tests
python3 gateway_poc/gateway/verify-remote.py
```

`auth`는 새 프로세스에서 인증하고 종료한다. `lifecycle`은 실제 만료 후 재인증까지 약 5분 걸린다. `recipient`는 인증과 공개 수신처 인증서 조회만 수행한다. `failure-tests`도 정상 인증 1회는 실제 서버에서 수행하고, 그 뒤 오류를 로컬에서 주입한다. 자동 재시도·토큰 영구 저장·상시 서비스 등록은 구현하지 않았다.

실행 식별은 [prepared](../evidence/gateway-prepared.json), 환경 검증은 [environment](../evidence/gateway-environment.json), 종합 판정은 [summary](../evidence/gateway-summary.json)에 기록한다. 각 실행의 소스 해시와 시각을 별도로 보존한다. 초기 lifecycle은 조회 클래스 추가 전 준비된 폴더에서 실행했으며 HeadlessGateway 소스 해시는 최종본과 같다.

사후 확인에서 SSH는 Session 0이고 14개 라이브러리는 설치본과 일치했으며 시험 폴더에 payload 파일은 없었다. 기존 DDMD `javaw` GUI 프로세스는 이 사후 확인 시점에 관찰되지 않았다. 이번 실행부는 프로세스 실행을 차단하며 DDMD 종료·재시작 명령을 수행하지 않았다. 기존 GUI의 종료 시점·원인은 확인하지 않았다. `macos_agent`는 `main...origin/main`의 clean 상태를 유지했다.

## 판정

**SAM을 제외한 최소 인증·조회 CLI와 요청된 수명·재시작 검증을 완료했다.** 오류 처리는 로컬 주입 범위에서 확인했다. 이 구현은 macOS가 인증 재료를 공급하고 Windows 원본 Java 라이브러리가 실행하는 구조다. Windows 단독 비밀 공급, macOS/Linux 단독 실행, 운영 상시 서비스, SAM 및 통보 처리는 이번 완료 범위에 포함하지 않는다.
