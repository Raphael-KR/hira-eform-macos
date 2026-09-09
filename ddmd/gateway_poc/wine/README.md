# macOS Wine DDMD 검증

- Goal: 사용자 제공 설치파일로 macOS Wine에서 DDMD 실행 가능 여부를 검증한다.
- Boundary: 격리 Wine prefix와 복사본만 사용하고 Windows 설치본을 보존한다.
- Done: Windows JRE와 DDMD 코드의 실제 Wine 실행 결과 및 한계를 기록한다.
- Non-goals: SAM 제출/시험, 청구, 운영 통보 조회/수신, 보안 정책 우회.
- Verification: 배포본 체크섬, Wine/JRE 실행, 오프라인 probe, 가능한 인증 전용 시험.

## 입력 확인

- 설치파일: `/Users/<owner>/Downloads/hira_ddmd_setup.exe`
- 형식: PE32 Intel 80386, NSIS self-extracting installer
- SHA256: `4e7e46516cc62f2bb7d915cf2468fa5626353c19ff0d49ef12424ad366d4fb2f`
- Mac: arm64 macOS 26.6.2; `arch -x86_64 /usr/bin/true` exit 0.
- 기존 Wine 설치 없음. Homebrew wine-stable 11.0_1은 Gatekeeper 검사 사유로 disabled 상태. 공식 배포본 검증을 진행하며 보안 설정은 변경하지 않는다.

## 2026-09-09 배포본 사전 검사

- 공식 배포 URL: https://github.com/Gcenx/macOS_Wine_builds/releases/download/11.0_1/wine-stable-11.0_1-osx64.tar.xz
- Homebrew 게시 SHA256 및 실파일: `b50dc50ec7f41d58b115a6b685d4d1315ba3c797bd3aa0f49213f2703cb82388` 일치.
- 배포본 위치: `/private/tmp/hira-wine-trial/Wine Stable.app`
- Gatekeeper 실검사: `rejected`, `source=no usable signature`.
- codesign 실검사: `code object is not signed at all`, architecture x86_64.
- Homebrew wine-stable 및 wine@devel 모두 disabled 상태를 공식 페이지에서 확인.
- Wine, Wine prefix, DDMD 설치/실행은 아직 수행하지 않았다. 인증서 및 Keychain에 접근하지 않았다.
- 다음 단계에는 검증한 이 Wine 배포본의 서명 없는 CLI 바이너리 실행에 대한 사용자 결정이 필요하다. 전역 Gatekeeper 해제는 제안하지 않는다.

## 승인 후 실행 결과

사용자가 해당 Wine 배포본 실행을 명시적으로 승인했다. Gatekeeper 전역 설정, quarantine 속성, 코드 서명은 변경하지 않고 CLI 바이너리를 실행했다.

- Wine 11.0 실행 성공. 전용 prefix: `/private/tmp/hira-wine-trial/prefix`.
- 새 prefix의 `z:` 및 Mac Desktop/Documents/Downloads 등 연결 심볼릭 링크만 제거했다. 이는 경로 분리이며 OS 수준의 완전한 파일·네트워크 sandbox를 뜻하지 않는다.
- 사용자 제공 설치파일 `/S /D=C:\hira\DDMD` 실행 exit 0. Java, lib, bin, 기본 설정 등이 설치됐다. 실제 기관 번호는 빈 값이며 실제 인증서·운영 DB·SAM을 복사하지 않았다.
- 설치된 Java `1.8.0_171`, 32비트 Client VM 버전 확인 성공.
- 기본 JVM에서 ECJ 컴파일 시 `EXCEPTION_ACCESS_VIOLATION (0xc0000005)` 발생.
- 원본 `bin/ddmd.exe` 기본 실행도 같은 주소 `0x7bf21139`에서 JVM 충돌.
- `-Xint`로 ECJ 컴파일 및 기존 HeadlessAuthProbe 17개 검사 모두 성공. 원본 DDMD 인증 객체, SEED 봉투 왕복, 합성 토큰 복원/만료/연장/verifier, 오류 반환 및 네트워크·GUI·프로세스 차단을 검증했다. Node 교차 복호화도 성공.
- `JAVA_TOOL_OPTIONS=-Xint`로 원본 DDMD 재실행 시 초기화가 더 진행되어 새 SQLite DB 접근 및 AWT 스레드 생성이 관찰됐지만 다시 JVM 충돌했다. `Dispatcher-Thread-2`의 `java.io.FileOutputStream.writeBytes` / log4j Dispatcher 호출 중 native 프레임에서 발생했다. 정확한 Wine/JRE 결함 원인은 확정하지 않았다.
- 동일 실행 경로의 두 차례 실패 후 추가 DLL·JRE 교체나 패치를 누적하지 않았다. 시험 prefix의 프로세스를 종료했다.
- 실제 HIRA 인증, SAM·청구·운영 통보 요청은 실행하지 않았다.

판정: **기본 설치본을 그대로 Wine에서 안정 실행하는 데 실패했다. 그러나 headless 인증·암호 라이브러리는 -Xint 조건에서 오프라인 실행이 가능했다.** 전체 DDMD 사용 가능 및 실제 인증 서버 연결 성공으로 확대 해석하지 않는다. 다음 후보는 성공한 headless 경로의 실제 인증 전용 검증이며, 원본 GUI 안정화는 별도 Wine/JRE 호환성 조사다.

실행 스크립트: `python3 gateway_poc/wine/offline.py` (고정 Wine prefix/설치본과 ECJ를 필요로 하며 합성 fixture는 매 실행 별도 폴더에 생성).
증거: `../evidence/wine-result.json`, `wine-offline-probe.txt`, `wine-node-interop.txt`, `wine-launcher-crash.txt`.

## 실제 인증 전용 추가 검증 계획

- Goal: Wine Windows Java `-Xint` headless 실행으로 실제 HIRA AuthToken 발급을 확인한다.
- Boundary: 기존 인증 실행부와 설치된 인증 관련 JAR, 인증 전용 endpoint/action만 사용한다. 기관 번호·인증 공개키·VID random은 stdin으로만 전달한다.
- Done: 실제 응답에서 AuthToken 유형, ID 존재, 미만료를 확인하고 비밀 없는 결과를 보관한다.
- Non-goals: DDMD GUI 실행, SAM·청구·통보 요청, 토큰 또는 개인키 파일 저장.
- Verification: 원본 대비 실행부 변경 확인, 컴파일, 단일 인증 요청, payload 파일 없음 및 프로세스 종료 확인.

## 실제 인증 전용 시험 결과: 서버 도달 전 실패

2026-09-09 03:15:35–03:15:42 KST, 03:17:06–03:17:13 KST에 실행했다. **두 실행 모두 `requests=0`, `connectChecks=0`이며 HIRA 인증 서버 연결·토큰 발급은 검증하지 못했다.**

- 인증용 14개 원본 JAR과 Java 실행부를 Wine `-Xint`에서 컴파일했다.
- 기관 번호는 Windows 설정에서 읽어 메모리로만 전달했다. 최초 준비 실패는 키와 `=` 사이 공백을 처리하여 해결했다. Windows 설정은 수정하지 않았다.
- 기존 macOS Keychain/인증서 읽기 경로를 호출하고 기관 번호, 공개 인증서, VID random을 child stdin으로 전달했다. 개인키·비밀번호 자체는 Wine에 전달하지 않았다.
- Wine Windows Java에서 stdin 읽기 중 `java.io.IOException`, `FileInputStream.available0`가 발생했다. 최초 실패 뒤 FilterInputStream의 `available()`을 0으로 반환하도록 수정했으나 System.in 내부 BufferedInputStream이 같은 native 함수를 호출하여 두 번째에도 실패했다.
- 인증 전송 함수에 진입하기 전 실패했다. 이는 HIRA 서버 거부, 인증서 오류 또는 토큰 발급 실패 응답이 아니다.
- 동일 입력 호환성 문제의 두 차례 실패 후 추가 우회는 중단했다. 다음 조사는 실제 인증정보 없이 합성 입력으로 Wine stdin/Windows Java 호환성을 분리 검증하는 것이 적절하다.
- 시험 Wine 프로세스를 종료했고 parts/javatmp payload 0개, crash 파일 0개, SAM 파일 0개를 확인했다. 실제 인증정보·응답·토큰은 파일로 저장하지 않았다. macos_agent는 clean 상태다.

관련 코드: `prepare-live.py`, `HeadlessGateway.java`, `run-auth.mjs`.
증거: `../evidence/wine-live-auth-stdin-failure.json` (첫 실패), `../evidence/wine-live-auth-result.json` (재검증), `../evidence/wine-live-prepared.json` (소스·라이브러리 해시/실행 인자).

`run-auth.mjs`는 실제 인증 전용이며 반복 실행하면 인증정보를 다시 읽는다. stdin 호환성 문제가 해결되기 전에는 자동 재시도하지 않는다. 최신 결론은 **오프라인 암호 시험 통과, 실제 서버 인증 미검증**이다.
