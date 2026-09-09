# HIRA DDMD의 macOS headless 실행 및 GUI 검증 종합

작성일: 2026-09-09 KST
대상 프로젝트: `/Users/<owner>/Playground/HIRA_eform_login`
기준: 2026-09-09까지의 로컬 시험 기록과 증거 파일. 이 문서는 누적 README의 중간 판정을 종합한 최신 요약이며, 신규 서버 요청이나 실행 시험을 수행한 보고서는 아니다.

## 1. 핵심 결론

**DDMD의 인증·통신·암호·로컬 통보 처리에는 macOS JVM에서 재사용 가능한 Java 구현이 있다.** Wine 없이 네이티브 macOS Java로 실제 HIRA 인증, 토큰 재발급, 통보 조회·다운로드, 로컬 복호화와 통보 생성까지 검증했다.

다만 DDMD 전체를 순수 Java 프로그램이라고 단정할 수는 없다. 배포본에는 Windows 실행기, 레지스트리·프로세스 조회, 보안 연동 및 GUI 결합 부분이 남아 있다. 원본 GUI의 화면과 버튼 동작, 실제 SAM 점검 엔진 전체, 청구 송신은 검증되지 않았다.

현재 판정은 **“macOS headless gateway의 주요 기능은 실증됐으나, 완전한 gateway 및 운영 사용 가능 판정은 미완료”**다. Linux 실행은 직접 시험하지 않았으므로 macOS 결과를 Linux의 검증 완료로 확대하지 않는다.

## 2. 시작 목적과 승인 범위

진료비청구 프로그램에서 생성하는 SAM 파일과 심평원 송수신 기능을 macOS에서 연계할 수 있는지 확인하는 것이 출발점이었다. 사용자가 macOS 포털 로그인 가능 및 SAM 업로드 기능 부재를 관찰했으나, 이 시험은 포털 전체 기능의 존재·부재를 별도로 증명하지 않는다. 기존 사이트맵도 로그인 후 기능 부재를 입증하는 자료는 아니다.

검증 순서는 Windows CLI 경로 확인, Wine 격리 시험, 네이티브 macOS JVM 시험, 실제 인증·통보 처리, GUI·설정·DB 결합 시험이었다. Windows CLI 가능 여부는 사용자가 확인된 것으로 받아들이고 이후 macOS 검증으로 진행했다.

| 구분 | 범위 |
|---|---|
| 실제 서버 | 승인된 인증, 만료 후 재인증, 수신처 인증서 조회, 통보 목록 및 실제 통보 1건 다운로드 |
| 실제 통보 로컬 처리 | 확보한 파일의 복호화, 서명·해시 검증, 원본 코드로 생성 및 백업 |
| GUI·DB 시험 | 설치본 복제, 합성 문서 메타데이터, 기존 실제 통보 ZIP 사본 사용 |
| 지속 제외 | 실제 SAM 청구 송신. SAM 테스트 서버 송신도 이번 검증에 포함하지 않음 |
| 운영 상태 | GUI·DB 시험에서 Windows 운영 DB와 실제 수신 이력을 시험 데이터로 수정하지 않음 |

후속 GUI 시험 중 필요한 서버 연결도 추가로 허용됐지만, 해당 단계는 로컬 문제여서 서버 연결을 사용하지 않았다. 실제 다운로드의 서버 내부 수신 이력 변화는 직접 검증하지 않았다.

## 3. 시험 환경과 격리 방식

| 환경 | 구성 및 결과 |
|---|---|
| Windows 기준 설치 | `C:\hira\DDMD`, 포함 Java 8u171 32비트 |
| Windows SAM 경로 | 청구 `C:\hira\DDMD\sam\in`, 통보 `C:\hira\DDMD\sam\out` |
| Wine | Wine 11.0, 전용 prefix `/private/tmp/hira-wine-trial/prefix` |
| 네이티브 JVM | Azul Zulu 8u504, macOS ARM64, `/private/tmp/hira-jvm-trial/zulu8.96.0.205-ca-jdk8.0.504-macosx_aarch64/Contents/Home` |
| GUI·DB 시험 복제본 | `/private/tmp/hira-ddmd-ui-wtk92jjq` |
| 설치 파일 | 사용자 제공 `/Users/<owner>/Downloads/hira_ddmd_setup.exe` |

Wine과 JVM은 별도 디렉터리에 설치했고 시스템 JVM 등록이나 전역 PATH/JAVA_HOME 변경을 하지 않았다. Wine prefix의 Mac 사용자 폴더 연결을 제한했다. GUI 시험에는 전용 폴더와 Java SecurityManager를 사용해 네트워크·하위 프로세스 및 외부 Java 쓰기를 제한했다.

이는 **설치 경로 분리와 실행 제한이며, OS 수준의 완전한 샌드박스를 입증한 것은 아니다.** 임시 경로는 OS 정리로 사라질 수 있다. 실행 스크립트 일부는 해당 시험 경로와 선행 컴파일 산출물에 의존하므로 배포용 실행기나 깨끗한 환경의 원클릭 재현 도구가 아니다.

## 4. 기능별 최신 판정

| 기능 | 판정 | 확인한 범위와 한계 |
|---|---|---|
| Wine 설치 | 성공 | 제공 설치파일 설치 및 포함 JVM 버전 확인 |
| Wine 원본 GUI | 실패 | 기본 실행과 `-Xint` 실행에서 JVM 충돌. 정확한 Wine/JRE 결함 원인은 미확정 |
| Wine headless 암호 | 부분 성공 | 합성 오프라인 시험 및 Node 교차 복호화 성공 |
| Wine 실제 인증 | 미검증 | stdin native 오류로 인증 서버에 도달하기 전에 실패 |
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

## 5. 실제 인증과 기존 HIRA_eform_login 코드의 역할

기존 macOS 인증서·Keychain 접근 코드와 암호 처리 코드를 활용했다. 인증 경로에서는 필요한 공개 인증서와 VID 관련 입력을 준비해 Java에 전달했고, 실제 개인키·비밀번호 자체를 Wine/인증용 JVM에 전달하지 않았다. 실제 통보 복호화에서는 macOS 코드가 개인키를 메모리에서 사용했다.

DDMD 원본 Java 라이브러리는 인증 메시지 구성과 HIRA 통신, 토큰 처리를 수행했다. 따라서 기존 로그인 코드만으로 DDMD 보안 기능 전체를 구현했다고 표현하는 것은 정확하지 않다. **기존 macOS 인증정보 처리 코드와 DDMD 원본 Java 코드를 조합한 경로가 실증된 것**이다.

초기 실제 인증 준비에서는 기관 번호를 Windows 설정에서 읽었다. Windows 의존성을 완전히 제거한 실행기로 만들려면 기관 번호 등 필수 설정을 Mac에서 공급해야 한다.

합성 암호 시험 22개는 통과했지만, 원본 `DdmdMessageSignatureImpl.verify`에는 `DdmdContents.getInstance`의 byte[] 처리 오류가 남았다. 실제 통보는 별도 ASN.1 파싱과 OpenSSL 검증으로 확인했으며 원본 JAR를 수정하거나 해당 검증기를 통과한 것으로 처리하지 않았다.

## 6. 실제 통보 다운로드·복호화·서명 검증

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

## 7. GUI·설정·DB 네 단계 시험

### 7.1 DB 임시 경로 문제

원본 SQLite JDBC 3.7.2의 `VACUUM`이 `/var/tmp`에 대해 `File.canWrite`를 호출하다 격리 Guard에 차단되는 것을 재현했다. 이후 GUI에서 DB 잠금 오류가 이어졌다.

같은 드라이버에 `PRAGMA temp_store=MEMORY`를 실행하니 VACUUM이 통과했다. JDBC URL 쿼리 매개변수 방식은 효과가 없었다. 시험용 `IsolatedJdbc`를 추가해 연결 직후 PRAGMA를 실행하고 원본 설정의 `driver.class.name`과 `url`로 선택했다. 적용 후 GUI 로그에서는 기존 `SQLITE_BUSY`가 관측되지 않았다.

원본 배포 JAR는 바꾸지 않았지만 시험 드라이버와 설정 조정은 추가됐다. 따라서 아무 조정 없는 원본 실행과 구분한다.

### 7.2 Windows 전용 기능

`launcher.exe`, `tasklist`, `reg` 호출 실패가 남았다. 실행 제한 아래에서도 이후 Launcher 초기화와 수신함 SQL 실행은 이어졌다. 이 관찰만으로 모든 Windows 의존성이 무해하거나 제거 가능하다고 단정하지 않는다.

### 7.3 실제 창 접근

실행 중인 `GuiBootstrap`은 앱 목록에 나타났다. 처음에는 Mac 잠금에 막혔고, 사용자 잠금 해제 후에도 앱 ID 선택은 `Invalid app`, JDK 번들 경로는 실행 앱 찾기 실패, 시험용 번들 경로는 `Exec format error`를 반환했다.

이는 도구가 화면 검증을 수행하지 못했다는 증거다. DDMD 창이 정상 표시됐거나 표시 자체가 불가능하다는 증거로 사용할 수 없다. 화면 표시, 수신함 행, 설정 버튼, 통보 생성 버튼 동작은 여전히 미확인이다.

### 7.4 설정·통보 처리 흐름

원본 `SystemInfoController.saveProperties`로 합성 기관 번호, 입출력 경로, 백업 기간, 보안 옵션을 저장했다. 새 JVM에서 읽은 값이 모두 일치했다.

통보 생성 시험은 원본 `ApplicationBootstrap`의 클래스 로더를 사용하고 `ReceiveController.zipReleaseCont`를 reflection으로 직접 호출했다. 원본 `DocumentUtils.asFileName` 규칙으로 입력 ZIP을 배치했다. 반환값 true, DB 상태 `1`, 파일 생성·일반 백업·월별 백업의 바이트 일치를 확인했다.

이 시험에서 화면 객체와 진행창은 null이었다. 실제 ZIP과 합성 메타데이터를 사용했으며 운영 수신 이력을 복원한 것이 아니다. **원본 컨트롤러의 로컬 흐름은 검증됐지만 GUI 이벤트 연결은 검증되지 않았다.**

## 8. 변경 및 종료 상태

- 원본 배포 JAR와 복제본의 원본 JAR 바이트 일치 확인.
- 복제 원본 DB의 준비 시점 SHA-256 유지 확인.
- 시험 DB `integrity_check=ok` 확인.
- 마지막 격리 GUI 프로세스 종료 확인.
- GUI·DB 후속 시험의 서버 연결 0회, 실제 SAM 청구 송신 없음.
- 이번 문서 작성은 기존 증거 정리만 수행하며 인증정보 접근이나 서버 재시험을 포함하지 않음.

## 9. 다음 검증 과제

1. **GUI 관측 경로 확보:** 실행 중인 Java 창을 도구가 선택할 수 있는 방식 또는 사용자 직접 관측으로 화면 존재부터 확인한다. 접근 실패를 화면 정상 판정으로 대체하지 않는다.
2. **GUI 사용자 흐름:** 설정 저장→종료·재실행→설정 유지→시험 통보 표시→생성 버튼→파일·DB 일치를 같은 복제 환경에서 검증한다.
3. **실행기 안정화:** 다운로드 후 로컬 저장 실패를 해결하고, 설정·원본 클래스 로더·시험 JDBC 적용을 재현 가능한 실행기로 정리한다.
4. **신뢰 검증:** 실제 서명자의 CA 체인·신뢰앵커·폐지 확인과 원본 메시지 검증 파서 호환성을 검증한다.
5. **SAM 점검:** 검증 가능한 비운영 SAM+MEDLOG 묶음으로 파싱·점검·결과 생성을 시험한다. 서버 송신은 기존 제외 범위와 별도로 결정한다.
6. **Linux:** 별도 환경에서 인증·암호·SQLite·파일 처리 경로를 실행해 판단한다.

## 10. 근거 문서와 증거

아래 링크는 이 문서 위치를 기준으로 한 프로젝트 내 상대 경로다. 증거 JSON의 조회 건수·유효기간·파일 상태는 각 시험 시점의 관측이다.

| 내용 | 근거 |
|---|---|
| Windows 설치본 정적 조사 | [초기 분석](ddmd-integration-analysis.md) |
| SAM 테스트 경계 | [송신 시험 경계](ddmd-sam-test-boundary.md) |
| Wine 시험 | [Wine 기록](../gateway_poc/wine/README.md) |
| macOS JVM 누적 기록 | [JVM 기록](../gateway_poc/macos-jvm/README.md) |
| GUI·DB 상세 | [격리 시험 기록](../gateway_poc/isolated-ui/README.md) |
| 실제 인증 | [인증 결과](../gateway_poc/evidence/macos-live-auth-result.json) |
| 토큰 재발급 | [수명 관리 결과](../gateway_poc/evidence/macos-lifecycle-result.json) |
| 다운로드 복구 | [파일 확보 결과](../gateway_poc/evidence/macos-download-recovered.json) |
| 복호화·서명 | [검증 결과](../gateway_poc/evidence/macos-notice-verification.json) |
| 네 단계 종합 | [최신 결과](../gateway_poc/evidence/isolated-four-stage-result.json) |

누적 README에는 당시의 “아직 미검증” 문장이 이력으로 남아 있다. 최신 기능별 판정은 이 문서와 각 문서의 마지막 후속 시험 결과를 함께 기준으로 삼는다.

## 11. 시작 화면만 보였던 원인 — 2026-09-09 07:52 KST 후속 확인

사용자 캡처로 macOS에서 LauncherSplash가 실제 표시됨을 확인했다. 원본 바이트코드에서 Launcher.doLoad는 StandaloneFrame을 생성·캐시하지만, ClientContext.openFrame 자체는 표시하지 않는 것을 확인했다. 별도 `showpanel standalone` 명령의 Launcher$4.run이 Frame.showFrame을 호출한다. 기존 시험은 bootstrap start만 반복했고 이 표시 명령을 보내지 않았다.

실행 중인 격리 복제본의 work/in에 원본 FileCommandParser 형식으로 `command = showpanel`, `arguments = standalone` 및 완료 마커를 넣었다. 07:52:33 KST 로그에서 원본 watcher→dispatcher→showpanel standalone 처리를 확인했다. update 인자는 사용하지 않았으며 네트워크 차단은 유지했다. 이후 AWT 이벤트 큐의 처리 로그도 이어졌다. 실제 본 화면 표시와 버튼 동작은 사용자 캡처로 추가 확인해야 한다. 따라서 앞선 화면 도구 접근 실패만을 본 화면 미표시의 원인으로 해석하지 않는다.

## 12. 사용자 화면 및 클릭 증거 — 2026-09-09 07:53 KST

사용자 제공 07:52:47 캡처에서 macOS 창 장식, 진료비청구 프로그램 제목, 메뉴·아이콘·한글이 있는 본 화면을 확인했다. 본 화면 표시 판정은 미확인에서 확인으로 갱신한다.

이어 환경설정 클릭 후 07:53:31 캡처에서 `[1908] 'systemInfo' 패널을 가져오는 도중 오류가 발생하였습니다` 대화상자를 확인했다. 07:53:24 실행 로그에 TopIconMouseListener.mouseReleased → FrameActions.showPanel → MDIPanelManager.showPanel → systemInfo 리소스 생성 경로가 기록됐다. 따라서 클릭 이벤트 전달 자체는 확인됐고, 환경설정 패널 생성은 실패했다.

최초 원인은 JideSwingUtilities 정적 초기화의 `ClassCastException: java.util.HashMap cannot be cast to java.awt.RenderingHints`다. SystemInfoFrm.createFolderChooser → JIDE FolderChooser 경로에서 발생했다. 뒤의 NoClassDefFoundError는 이 초기화 실패에 따른 후속 오류이며 JAR 누락으로 단정하지 않는다. 같은 원인으로 백업 관련 패널 초기화도 실패한 로그가 있다. 앞서 관측한 Windows reg 호출 실패나 DB 잠금과는 별개의 GUI 라이브러리 오류다. 원본 설정 함수의 CLI 저장 성공은 이 패널의 성공을 의미하지 않는다.

최신 판정: 본 화면 표시 확인, 환경설정 클릭 이벤트 연결 확인, 환경설정 패널 생성 실패. 다음 조사 대상은 JIDE가 RenderingHints로 변환하는 값의 출처와 macOS JVM에서의 호환 처리다.

## 13. Computer Use 앱 선택 해결 및 직접 클릭 검증

2026-09-09 후속 시험에서 고유 앱 ID `local.hira.ddmd.isolated`와 실제 Mach-O 실행 파일을 가진 격리 APPL 번들을 만들었다. 실행기가 동일 프로세스 안에서 기존 JVM을 구동하도록 하여 Computer Use가 앱 경로와 고유 ID 양쪽으로 선택할 수 있게 됐다. 원본 JAR와 기존 Guard는 유지했다.

Computer Use로 본 화면 스크린샷·접근성 트리를 읽고 창을 전면으로 가져온 뒤 관리→환경설정을 직접 클릭했다. `[1908] systemInfo` 오류를 확인하고 확인 버튼으로 닫아 본 화면으로 복귀했다. 따라서 앱 선택·화면 읽기·클릭·오류 대화상자 조작은 직접 검증됐다. 이전 절의 Computer Use 미접근 상태를 갱신한다. JIDE 초기화 오류는 해결하지 않았다.

실행 방법: [앱 실행기 설명](../gateway_poc/isolated-ui/app-launcher/README.md). 증거: [Computer Use 결과](../gateway_poc/evidence/computer-use-app-result.json). 앱은 후속 시험을 위해 실행 상태로 남겼으며 서버 연결·청구 송신은 하지 않았다.

## 14. Computer Use 직접 GUI 범위 확대

2026-09-09 08:04–08:12 KST에 12개 주요 메뉴·진입 경로를 직접 시험했다. 화면 7개 표시 성공, JIDE 관련 화면 4개 실패, SAM 부재 안내 1개를 확인했다. 통보 생성 화면에서 시험 문서 목록·상세는 표시됐지만 생성 대상 선택이 처리되지 않아 GUI 생성 완료는 미확인이다. [직접 GUI 시험 보고서](ddmd-computer-use-test-report.md)에 항목별 결과와 입력·접근성 한계를 기록했다. 실제 SAM 송신은 하지 않았다.

## 실제 업데이트 추가 시험 (2026-09-09)

별도 후보에서 실제 업데이트 21개 수신(14,574,849 bytes), 원본 UpdController 적용, 21개 해시·버전 및 기준자료 DB 11개 검증, macOS 앱 재실행을 확인했다. 적용 후 서버 재조회는 추가 0개였다. 원본 Windows 자동 재시작과 업데이트 결과 보고 수락은 미검증이다. [상세 업데이트 시험](ddmd-macos-update-test.md)을 참조한다.
