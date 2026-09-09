# DDMD 설정·DB·GUI 격리 검증

- Goal: 복호화된 실제 통보 ZIP을 시험 DB 레코드와 연결하고 원본 DDMD UI 경로를 검증한다.
- Boundary: 새 설치본의 프로그램/기본 DB를 복제한 전용 폴더, 합성 문서 메타데이터와 기존 로컬 통보 ZIP 사본. 원본 Windows 운영 상태는 보존한다.
- Done: 원본 DAO 등록·조회·파일 연결 검증과 원본 GUI 실행 결과를 구분해 기록한다.
- Non-goals: 서버 인증/조회/수신/송신, 실제 수신 상태 변경, 전역 설정 변경, 원본 운영 DB 쓰기.
- Verification: 복사 전후 해시, 원본 SQL/DAO 사용, 실행 네트워크·프로세스 차단, GUI 승인 범위 내 직접 확인.

## 2026-09-09 실행 결과

macOS ARM64의 격리 Zulu Java 8에서 원본 DDMD DAO와 SQLite 매핑으로 합성 통보 1건을 등록·조회하고 생성 상태로 변경했다. 종료 후 SQLite integrity_check는 ok이고, 복제 원본 DB의 SHA-256은 준비 시점과 일치한다. 운영 Windows에는 접근하지 않았다.

기존 실제 복호화 ZIP 사본을 시험 문서의 로컬 경로에 배치하고 원본 Commons.decompress로 3개 파일(총 3,596바이트)을 생성했다. 생성 파일은 ZIP 엔트리와 바이트 단위로 모두 일치했다. DAO 상태 변경과 파일 생성은 분리된 시험이다. GUI 버튼을 통한 일괄 처리를 입증한 것은 아니다.

원본 ApplicationBootstrap 및 원본 클래스 로더로 GUI 프로세스가 시작되고 Launcher의 설정/DB 초기화 경로까지 실행됐다. 그러나 격리 Guard가 VACUUM 중 파일 쓰기 가능 여부 확인을 차단했고 이후 SQLITE_BUSY가 관측됐다. 이 결과만으로 macOS의 DB 호환성 결함이라고 판단할 수 없다. launcher.exe, tasklist, reg 등 Windows 전용 프로세스 호출도 관측되었고 Guard가 실행을 차단했다.

CUA 앱 목록에는 GuiBootstrap이 표시되었지만 앱 이름, bundle ID, 실행 경로 선택은 Invalid app으로 실패했다. 따라서 실제 창 표시, 수신함 행 표시, 설정 저장/재로딩, GUI를 통한 통보 생성은 미확인이다. 시험 Java PID 84665에 TERM을 보내 종료했다. GUI 통과로 간주하지 않는다.

격리는 전용 폴더와 Java SecurityManager 기반이며 OS 수준의 완전한 샌드박스 증명은 아니다. 네트워크 연결과 하위 프로세스 실행을 차단하고 시험 폴더 밖 Java 쓰기를 제한했다. 인증서와 운영 기관 설정을 복사하지 않았다. 보호 설정을 해제해 GUI 성공을 강제하지 않았다.

판정: 설정·DB·통보 파일 처리의 분리 재사용은 부분 실증되었다. 원본 GUI 전체 흐름은 검증 미완료다. 다음 시험은 복제 환경에서 VACUUM의 임시 경로 요구를 정확히 식별하고, GUI 도구가 해당 Java 앱을 선택할 수 있는 실행 방식을 확보한 뒤 수행해야 한다.

증거: ../evidence/isolated-db.txt, ../evidence/isolated-ui-result.json. 실행 준비 스크립트 run-local.py는 같은 시험 DB에 재실행하면 중복 키가 발생하므로 새 복제 DB에서만 실행한다.

## 4단계 추가 시험 — 2026-09-09 04:22 KST

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
