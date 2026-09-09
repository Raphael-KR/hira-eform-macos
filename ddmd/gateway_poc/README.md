# DDMD 코드와 진단 도구

현재 준비 상태와 문서는 [DDMD README](../README.md)를 기준으로 한다.
기존 분산 시험 보고서는 [실험 히스토리](../docs/HISTORY.md)로 통합했다.
이 디렉터리에는 소스·시험 도구만 보존하며 제공사 JAR, JVM, 인증서, 실자료를 배포하지 않는다.

## 도구 색인

| 디렉터리 | 역할 | 실험 기록 |
|---|---|---|
| `src/`, `scripts/` | 합성 키·암호·직렬화 및 Windows 오프라인 프로브 | [오프라인](../docs/HISTORY.md#ddmd-offline) |
| `live/` | Windows 실제 인증 한정 프로브 | [인증](../docs/HISTORY.md#ddmd-live) |
| `gateway/` | 토큰 수명·조회·오류 주입 프로브 | [gateway](../docs/HISTORY.md#ddmd-gateway) |
| `macos-jvm/` | macOS JVM 인증·통보·파일 처리 프로브 | [JVM](../docs/HISTORY.md#ddmd-macos) |
| `isolated-ui/` | 격리 JDBC·JIDE·인자 어댑터와 GUI 제어 | [격리 GUI](../docs/HISTORY.md#ddmd-isolated) |
| `isolated-ui/app-launcher/` | APPL/JLI 기반 격리 앱 빌드 | [실행기](../docs/HISTORY.md#ddmd-launcher) |
| `update/` | 단계별 업데이트 조회·수신·적용 시험 | [업데이트](../docs/HISTORY.md#ddmd-update) |
| `auto-update/` | 단일 실행 업데이트와 실패 복구 | [현재 계약](auto-update/README.md) |

## 실행 주의

시험용 외부 JVM은 2026-09-09에 제거했다. 과거 스크립트의 임시 경로는
현재 유효하다고 보장하지 않는다. 과거 Windows 도구는 `DDMD_WINDOWS_TEMP`로
원격 임시 경로를 지정하며 SSH 준비가 필요하다. README의 과거 명령을 그대로 실행하지 않는다.

재개 시 정식 진입점은 [auto-update/run.py](auto-update/run.py)다.
해당 경로도 로컬 설정·JVM·제공사 설치본과 실제 인증/업데이트 승인이 필요하다.
도구는 Keychain 조회·원격 연결·파일 변경·GUI 시작을 할 수 있다.
`npm run test:ddmd`의 합성 검증과 실제 실행을 구분한다.

기관·통보·토큰·원본 로그·개인키는 로컬 전용이다. 소스 정리 과정에서 이 자료를
삭제하거나 공개 폴더로 옮기지 않았다.

macOS 과거 진단 도구 `offline.py`, `prepare-live.py`, `verify-notice.mjs`는
`DDMD_SOURCE_DIR`에 사용 권한이 있는 DDMD 설치본의 절대 경로를 명시해야 한다.
설치본의 `lib/`와 `data/kmCert.der`를 읽으며 다른 시험 환경에서 자동 탐색하지 않는다.
JVM·컴파일러·시험 데이터의 과거 경로는 여전히 별도 준비 대상이다.
이 설정은 자동 업데이트 실행기의 `.local/ddmd/config.json`과 별개다.
