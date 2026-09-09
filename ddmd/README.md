# DDMD macOS 개발 환경

개발 코드·문서의 정식 위치는 이 저장소의 `ddmd/`다.
JVM·Wine 외부 설치 경로와 개발 코드·로컬 실행 데이터를 분리한다.

| 대상 | 위치 | Git |
|---|---|---|
| 자동 업데이트·GUI 호환·인증 프로브 | `ddmd/gateway_poc/` | 포함 |
| 분석·검증 문서 | `ddmd/docs/` | 포함 |
| DDMD 활성 버전·DB·프로그램 파일·기관 설정 | `.local/ddmd/` | 제외 |
| 인증서·비밀번호 | macOS NPKI·Keychain | 제외 |
| 개인 통보 파일·실행 원본 로그·검증 상세 자료 | 로컬 전용 폴더 | 제외 |
| JVM·Wine | 별도 외부 설치 경로 | 제외 |

## 실행

2026-09-09 시험 종료 후 외부 JVM·Wine과 임시 실행 환경을 삭제했다.
현재 로컬 GUI·업데이트 실행은 중지된 상태이며, 재실행하려면 JVM을 별도로 준비하고
`.local/ddmd/config.json`의 `java` 경로를 갱신해야 한다. [정리 기록](docs/ddmd-environment-cleanup.md)을 참조한다.

저장소 루트에서 `npm run ddmd:update`를 실행한다.
`ddmd/gateway_poc/auto-update/run.command`도 같은 진입점을 호출한다.

로컬 준비 상태는 `.local/ddmd/config.json`, `institution.txt`, `active.json`으로 관리한다.
config.json은 외부 JVM의 `java` 절대 경로와 DDMD 초기 설치본의 `source` 절대 경로를 갖는다.
기관번호는 institution.txt의 한 줄이며 파일 권한은 0600으로 유지한다.
이 파일들은 저장소에 포함되지 않으므로 다른 컴퓨터에서는 로컬 설정과
외부 JVM·정식 DDMD 설치본을 별도로 준비해야 한다. 인증서 로더는 현재 사용자의 NPKI와 Keychain을 사용한다.

자동 업데이트는 조회·수신·검증·후보 적용·macOS 앱 시작·결과 보고·최종 조회를 수행한다.
원본 GUI의 업데이트 버튼·OS 스케줄에는 아직 연결하지 않았다.
완료한 구버전 폴더는 보존되며 active.json이 현재 실행 대상이다.

## 검증과 유지보수

- `npm test`: 기존 인증기 및 공개 파일 검사 테스트
- `npm run test:ddmd`: DDMD 업데이트 안전/실패 경로
- `npm run check:release`: 공개 소스 허용 목록·비밀정보 형태 검사

기존 `gateway`, `live`, `wine`, `macos-jvm`, `scripts`, `update` 디렉터리에는 당시
시험 경로를 사용하는 진단 도구도 포함된다. 정식 실행 진입점은 `auto-update/run.py`다.
과거 Windows 진단 도구는 `DDMD_WINDOWS_TEMP` 환경 변수로 원격 임시 폴더를 지정한다.
기존 문서의 임시 경로·시험 실패는 역사적 기록이며 현재 실행 설정이 아니다.
문서에 언급된 상세 evidence와 개인 파일은 로컬 전용으로 공개하지 않는다.

2026-09-09 경로 이전 검증: 라이브러리·데이터 파일 186개 해시 일치,
정식 로컬 경로에서 앱 본 화면·환경설정 표시, macOS 인증을 통한
업데이트 조회 0개를 확인했다. JVM·Wine은 이동하거나 재설치하지 않았다.
실제 SAM 청구 전송은 검증하지 않았으며 시험에서 제외했다.
