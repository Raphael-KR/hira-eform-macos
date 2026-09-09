# DDMD Computer Use용 격리 앱 실행기

## 목적과 판정

2026-09-09, 직접 Java 실행에서는 Computer Use 앱 목록에 GuiBootstrap/com.azul.zulu.java가 나오지만 getApp 선택은 Invalid app이었다. 기존 JDK Info.plist는 com.azul.zulu.jdk, BNDL, libjli.dylib이며 실행용 APPL 번들이 아니었다. 이전 임시 앱은 이 메타데이터를 재사용해 Exec format error가 발생했다.

이를 해결하려고 APPL 번들, 실제 Mach-O 실행 파일, 고유 ID local.hira.ddmd.isolated를 만들었다. 실행기는 자식 java 프로세스로 교체하지 않고 같은 프로세스에서 기존 Zulu libjli의 JLI_Launch로 JVM을 시작한다. 원본 JAR·JVM 및 기존 GuiBootstrap 격리 Guard를 그대로 사용한다. 앱 실행기만 로컬 ad-hoc 서명했으며 TCC/접근성 권한이나 전역 보안 설정을 변경하지 않았다.

Computer Use 내부 구현을 열람한 것은 아니므로 resolver의 정확한 내부 분기는 미확인이다. 다만 기존 직접 실행의 선택 실패와 새 APPL 실행의 선택·조회·클릭 성공을 대조하여 이 앱 식별/실행 구조 조정이 유효함을 확인했다.

## 실행

- 빌드: 프로젝트 루트에서 `python3 gateway_poc/isolated-ui/app-launcher/build.py`
- 결과 앱: `/private/tmp/hira-ddmd-ui-wtk92jjq/DDMD Computer Use.app`
- Computer Use 최초 선택: `cua.getApp('/private/tmp/hira-ddmd-ui-wtk92jjq/DDMD Computer Use.app')`
- 후속 연결: `cua.getApp('local.hira.ddmd.isolated')`
- 상태 읽기 후 창의 Raise를 수행하면 전면 조작이 가능했다. 이후 메뉴 클릭과 최신 상태 읽기를 반복한다. 접근성 인덱스는 매 상태에서 새로 얻는다.

기존 격리 Java가 실행 중이면 같은 DB를 중복으로 사용하지 않도록 그 프로세스만 먼저 종료한다. 재빌드는 앱을 종료한 상태에서 한다. 고정된 시험 경로와 준비된 원본 라이브러리·컴파일 산출물에 의존하므로 배포용 패키지가 아니다. 시작 후 앱을 열어두며 자동 종료시키지 않는다.

## 본 화면 표시

원본 start는 본 화면을 자동 표시하지 않는다. 초기화 중 미리 만든 work/in 명령 파일도 정리되었다. 실행기의 제한된 대기 스레드는 이번 실행 로그에서 Application started를 최대 약 30초 동안 기다린 뒤 원본 showpanel standalone 명령을 넣는다. 이 스레드는 메뉴 클릭이나 테스트를 수행하지 않는다. 실제 시험 조작은 Computer Use로만 수행했다.

## 직접 검증

1. 앱 경로 선택 후 Splash의 접근성 progress indicator 읽기 성공.
2. 본 화면의 스크린샷·메뉴·창 제목 읽기 성공.
3. 고유 앱 ID 재연결 및 창 Raise 성공.
4. 관리 메뉴 클릭 후 AX 메뉴 Value=1 확인.
5. 환경설정 클릭 후 오류 창과 `[1908] 'systemInfo' 패널을 가져오는 도중 오류가 발생하였습니다.` 텍스트 확인.
6. 확인 버튼 클릭 후 본 화면 복귀 확인.

경로 연결 직후 일부 동작은 user changed 보호로 취소됐다. 상태를 다시 읽고 고유 ID로 재연결·Raise한 뒤 위 동작이 성공했다. 이를 UI 성공으로 허위 처리하거나 보호를 우회하지 않았다.

따라서 Computer Use 연결·실제 조작은 해결됐다. JIDE HashMap→RenderingHints 초기화 오류는 재현됐으며 이 실행기에서 수정하지 않았다. 청구·SAM 송신 및 서버 연결은 수행하지 않았다.

구현 참고: OpenJDK JavaAppLauncher가 앱 번들 안에서 JVM을 구동하는 구조를 확인했다. [OpenJDK 8 JavaAppLauncher main.m](https://code.googlesource.com/edge/openjdk/+/jdk8u111-b09/jdk/src/macosx/bundle/JavaAppLauncher/src/main.m). 시험 실행기는 기존 소스를 복사하지 않고 별도로 작성했다.
