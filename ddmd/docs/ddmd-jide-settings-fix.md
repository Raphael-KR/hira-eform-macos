# macOS DDMD 환경설정 오류 수정

2026-09-09, 격리 Zulu 8u504 / macOS 26.6.2에서 검증.

## 원인과 수정

원본 JIDE 2.11.2의 JideSwingUtilities 정적 초기화가 Toolkit의
`awt.font.desktophints`를 RenderingHints로 직접 형변환한다.
현재 macOS JVM에서는 HashMap이 반환돼 ClassCastException이 발생하고,
환경설정 패널은 후속 `[1908] systemInfo` 오류로 열리지 않았다.

GuiBootstrap에서 원본 DDMD 초기화 전에 해당 Map의 내용을 RenderingHints로
복사하고 이 JVM의 Toolkit 캐시에 설정하도록 했다. macOS이며 값이 Map이고
RenderingHints가 아닌 경우에만 적용한다. 원본 JIDE JAR와 OS 설정은 변경하지 않았다.
기존 네트워크·하위 프로세스 실행 차단 Guard는 유지한다.

## 직접 검증

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

증거: [jide-settings-fix.json](../gateway_poc/evidence/jide-settings-fix.json)

기존 GUI 시험 보고서의 실패 기록은 수정 이전의 관측으로 보존한다.
