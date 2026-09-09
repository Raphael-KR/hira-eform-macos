# DDMD 시험 환경 정리

2026-09-09 사용자 요청으로 시험을 종료하고 이번에 설치한 외부 실행 환경을 삭제했다.

## 삭제 범위

- `/private/tmp/hira-wine-trial`: Wine Stable.app, 다운로드 아카이브, 격리 prefix와 Windows DDMD/JRE 설치본.
- `/private/tmp/hira-jvm-trial`: Zulu ARM64 JDK 8u504, 다운로드 아카이브, JVM 시험 실행 복사본.
- `/private/tmp/hira-ddmd-inspect`: 외부 ECJ 컴파일러와 분석용 배포 바이너리 복사본.
- `/private/tmp/hira-ddmd-ui-wtk92jjq`: 임시 GUI 실행 환경.
- `/private/tmp/hira-ddmd-auto-runtime`: 정식 경로 이전 후 남은 임시 자동 업데이트 실행 환경.
- `.local/ddmd/*/candidate/jre18` 2개: 정식 DDMD 복사본에 포함된 Windows JRE.

## 보존 및 검증

삭제 전 소스·설정·로그·바이트코드 분석 텍스트 등 290개를 `.local/ddmd/cleanup-archive-20260909/`에 보존했다. 비공개 자료가 포함될 수 있으므로 Git에서 제외하며 공개하지 않는다. 삭제 대상 디렉터리의 심볼릭 링크를 따라 외부 파일을 삭제하지 않았다.

정식 DDMD 복사본의 lib/data 파일 370개는 삭제 전후 SHA-256이 일치했다. 개발 소스, 연구 문서, 정식 로컬 DB·통보 자료, NPKI 인증서·Keychain, 사용자가 제공한 Downloads 설치파일과 원격 Windows 설치본은 보존했다.

삭제 대상 7개 경로의 부재를 확인했다. 관련 Java/Wine 실행 프로세스는 없었고, macOS `java_home -V`는 설치된 JVM을 찾지 못했다. Applications와 시스템 Java 등록 경로 및 Homebrew Caskroom에서 Wine/Zulu 설치를 발견하지 않았다.

현재 GUI와 자동 업데이트는 실행 환경이 제거된 상태다. 역사적 시험 성공 기록은 당시 환경의 결과이며 현재 실행 가능함을 의미하지 않는다. 재실행 시 외부 JVM을 별도 설치하고 `.local/ddmd/config.json`의 java 경로를 갱신해야 한다. Wine 기반 시험에는 별도 Wine prefix도 다시 필요하다. 이번 정리에서는 인증 서버 연결과 SAM 송신을 수행하지 않았다.

Wine 종료 후 남은 `/private/tmp/.wine-501`의 빈 잠금 파일과 디렉터리도 제거했다. DDMD 단위 테스트 8개 및 공개 파일 검사(110개, 발견 사항 0개)를 통과했다.
