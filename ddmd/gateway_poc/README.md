# DDMD headless 인증 경계 PoC

최신 추가 검증: **2026-09-09 Windows headless 실제 HIRA 인증과 AuthToken 발급·미만료 검사를 통과했다.** [실제 인증 검증](live/README.md)을 참조한다. 아래 내용은 앞서 수행한 합성·오프라인 시험의 범위와 증거다.

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

## 실행 방법

Mac의 기존 `macos_agent/node_modules`, Node·Python·OpenSSL과 SSH 접근이 필요하다. 컴파일러는 [Maven Central의 Eclipse ECJ 3.26.0](https://repo.maven.apache.org/maven2/org/eclipse/jdt/ecj/3.26.0/)을 `/private/tmp/hira-ddmd-inspect/ecj-3.26.0.jar`에 두며, runner가 게시 SHA-1 `4837be609a3368a0f7e7cf0dc1bdbc7fe94993de`와 대조한다. 시스템에 JDK를 설치하지 않는다.

프로젝트 루트에서:

```sh
python3 gateway_poc/scripts/run-windows-probe.py
```

이 명령은 Mac 임시 디렉터리에 합성 fixture를 만들고, Windows의 `C:\Users\user\AppData\Local\Temp\hira-headless-poc-*`에 필요한 JAR·컴파일러·PoC를 복사하여 실행한다. 실제 DDMD JRE는 실행 런타임으로만 사용한다. 합성 키와 암호문은 임시 디렉터리에 남으며, 정확한 최신 위치는 `evidence/run.json`에 기록한다. 기존 설치 폴더를 청구 작업 디렉터리로 사용하지 않는다.

## 2026-09-09 검증 결과

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

## 판정 한계

이 결과는 **인증 객체·키 공급·암호처리를 GUI 없이 기존 라이브러리로 수행할 수 있다는 실행 증거**다. `CLT_AUTH_REQ` 본문인 Credentials의 처리를 시험했으며 실제 transport action/header를 서버에 전달하지 않았다. 합성 peer는 실제 HIRA 서버가 아니다.

실제 서버의 인증 수용·tokenId 발급·토큰 만료 후 재인증, NPKI 부가 속성 호환성, 청구 파일 서명과 통보 복호화, SAM 점검의 headless 분리, Windows 서비스 설치는 미검증이다. Node CMS와 Java 서명 알고리즘 전체의 호환성도 이번 시험만으로 확정하지 않는다. 실행 순서상 키 선택 창이 필수라는 기존 우려는 좁혀졌지만, 완전한 HIRA gateway 완료로 보고하지 않는다.
