# DDMD Windows 설치본의 Mac 연계 조사

> 2026-09-08~09 조사 시점의 정적 계약과 단계별 관측이다. 아래 '현재'는 당시 설치본을
> 뜻한다. 후속 실험·오류 수정·시험 환경 종료는 [히스토리](HISTORY.md),
> 지금의 재개 조건은 [DDMD README](../README.md)를 따른다.

조사일: 2026-09-08 KST. 대상: 로컬 Windows 시험 PC의 `C:\hira\DDMD` (SSH 계정·호스트 주소 생략).

## 결론과 검증 범위

DDMD에는 명령 파일을 통해 기존 실행 프로그램에 작업을 전달하고 JSON 결과를 받는 내부 연동 구조가 있다. Mac에서 Windows에 파일을 전달하는 연계 후보는 확인했으나, 실제 호출·무인 송수신·macOS 직접 실행을 검증한 것은 아니다.

설치 바이너리와 설정을 읽고, 프로그램 파일만 Mac 임시 폴더에 복사해 정적으로 분석했다. 실행 파일을 호출하거나 명령 파일·완료 마커를 생성하지 않았다. GUI 접근, 청구 송수신, 설정 변경, 인증서·SAM·기관 DB 복사는 하지 않았다. 원격 프로그램이 자체적으로 수행하는 동작은 이번 조사 명령과 구분한다.

현재 workspace는 Git 저장소가 아니다. 기존 `docs/biz-hira-sitemap.md`는 비로그인 SiteMap이므로 로그인 후 업로드 기능의 존재 여부를 증명하는 자료로 사용할 수 없다.

## 설치 상태

- 청구 SAM 설정: `compatibility.dmd.dir = C:\hira\DDMD\sam\in`
- 통보 SAM 설정: `compatibility.ntc.dir = C:\hira\DDMD\sam\out`
- 포함 JRE: Java `1.8.0_171`, Windows `i586`.
- 관측 당시 DDMD `javaw.exe` PID 4828, Windows SessionId 2. 조사용 SSH PowerShell은 SessionId 0.
- `work` 아래 파일 목록은 관측 시 비어 있었다. 실제 교환된 명령 파일의 사례는 확보하지 못했다.

## webapi.exe와 명령 파일

`webapi.exe`의 NSIS 압축 데이터를 실행 없이 해제한 결과 다음 문자열을 확인했다.

- 옵션: `/args=`, `/outfile=`
- 설치 위치 참조: `Software\Microsoft\Windows\CurrentVersion\Uninstall\DDMD`, `InstallLocation`
- 작업 경로: `\work\in`, `\work\out`, `\work\in\cmd_`, `\work\out\cmd_`
- 요청 내용: `command = api`, `arguments = `, `result = `
- 상태/시작 처리: `loading`, `stop` 오류 JSON, `\bin\launcher.exe" start`, launcher/loading/update 잠금 파일명.

옵션과 파일 전달 구조는 확인했지만, EXE의 전체 제어 흐름·인용부호 규칙·대기시간·종료코드·동시 요청 처리까지 검증하지 않았다. 따라서 실행 가능한 호출 예제를 확정 규약으로 제시하지 않는다. 호출 시 launcher 시작이나 업데이트 등 부수 동작 가능성이 있다.

Java 측 확인 근거:

| 클래스·메서드 | 확인한 동작 |
|---|---|
| `Launcher.doLoad` | `work/in`, `work/out` 감시 구성 |
| `Launcher.onFileCreated` | 이름에 `.end`가 있는 생성 이벤트에서 해당 접미 부분 앞의 원본 파일을 읽고 명령 큐에 추가 |
| `FileCommandParser.parse` | `command`, `arguments`, `result`를 읽음. `#`·`[`로 시작하는 줄과 빈 줄 무시. 첫 `=`로 키와 값 분리 |
| `FileCommandParser.parse` | `arguments`를 공백으로 분할. 기본 문자셋의 `InputStreamReader` 사용 |
| `Launcher.commandProcess` | `command=api`를 `Launcher$5`로 전달해 AWT 이벤트 큐에서 처리 |
| `Launcher$5.run` | 업데이트 분기 후 `WebCommandProcessor.process` 호출. 결과를 UTF-8 파일로 쓰고 결과 파일명에 `.end`를 붙인 마커 생성 |
| `WebCommandProcessor` 생성자 | 첫 인자를 내부 명령, 다음 인자를 요양기관기호로 취급하고 나머지를 명령 인자로 전달 |
| `WebCommandProcessor.process` | `status: ok`와 `result`, 또는 `status: err`와 `reason` 형태의 문자열 응답 구성 |

`updatefalse` 인자에 따른 업데이트 생략 분기가 코드에 있다. 이는 분석 사실이며, 업데이트를 생략하도록 설정하거나 실행하지 않았다.

## 지원 명령과 SAM 입력의 차이

내부 메서드로 `send`, `searchList`, `searchPreExamList`, `searchNtcList`, `receive`, `generateNtc`, `searchNtcGenList`, `systemData`, `validateYkiho` 등을 확인했다. `deleteDmd`, `deleteNtc`, `deleteNtcList`, `systemDataSave`, `idChange` 등 변경 명령도 존재한다. 이름이 조회형이어도 상위 업데이트·인증 경로의 부수 동작까지 없다는 뜻은 아니다.

`send`의 인자는 청구구분코드와 청구문서 ID 목록이다. `SendWebController.send`는 구분코드 `0` 또는 `1`, `DMD`로 시작하는 길이 11의 문서 ID를 검사하고 `RequestDocumentDAO.getRequestDocumentsByDmdDocIds`로 기존 문서를 조회한다. 여러 ID는 `@@`로 분리한다. 코드값의 업무상 의미는 이번 조사에서 확정하지 않았다.

따라서 `send`는 임의의 SAM 경로를 직접 받는 업로드 함수가 아니다. **SAM 배치 → DDMD 문서 등록·점검 → 문서 ID 확인 → 인증·송신**의 앞단은 아래 후속 조사에서 정적으로 확인했다. SAM 폴더에 복사하는 것만으로 등록이나 전송이 발생한다고 확인하지 않았다.

`receive`는 통보문서 ID, 본원·본부코드, 청구구분코드, 통보서상태코드를 받아 수신 컨트롤러에 전달하며 목록 구분자로 `@@`를 사용한다. `generateNtc`는 별도 통보서 생성 진입점이다.

## 인증과 성공 판정

- `SendWebController.send`에는 재전송·중복송신 확인 대화상자 분기가 있다.
- `SendController.sendDmdDocs`는 `ClientContext.getAuthToken`과 전송 대화상자를 사용한다.
- `ClientContext.getAuthToken`에는 인증서 UI 호출과 `KSignAxHIRA.SignedData` 경로가 있다. Windows XP/2003과 그 외 경로를 분기한다.
- 설치본에는 `AxHIRA_JNI_Module.dll`, KSign/Kcase 및 키보드 보안 DLL·드라이버가 있다.

따라서 내부 API의 존재가 인증 생략이나 headless 실행 가능성을 뜻하지 않는다. 기존 DDMD 세션 2에 SSH 세션 0의 요청이 전달되고 인증 화면까지 정상 처리되는지는 미검증이다.

`status=ok`와 결과 `.end`는 명령 처리 결과일 뿐, 실제 청구 접수 성공의 충분한 증거로 사용할 수 없다. 코드에서 `send`는 전송 컨트롤러를 호출한 뒤 문자열을 반환하며, 하위에는 조기 반환·인증 취소·실패 기록 경로가 있다. 실제 구현 시 문서별 송신 이력과 심평원 응답을 별도로 대조해야 한다.

## 후속 검증의 최소 순서

1. SAM을 DDMD 내부 문서로 등록하는 경로와 필요한 파일 구성을 정적으로 확인한다. 아래 후속 조사에서 진입점·DB 등록·결과 파일을 확인했다. 특정 청구 프로그램의 실제 출력 묶음과 호환되는지는 미검증이다.
2. 서버 접근·업데이트·GUI 동작이 없는 최소 진단 요청을 찾거나, 해당 영향이 필요한 검증 범위를 명확히 한다.
3. Windows의 기존 실행 세션을 이용한 명령 전달·결과 회수만 검증한다. GUI를 여는 검증은 사용자 승인 범위에서 수행한다.
4. 실제 SAM의 이동과 청구 제출은 별도 구체 범위에서 수행하며 문서 ID·송신 이력·접수 응답으로 검증한다.

현재 후보 구성은 Mac의 파일 준비·상태 조회와 Windows DDMD의 인증·송수신을 연결하는 방식이다. 연결 기능을 구현하거나 활성화하지 않았다.

## 분석 대상 식별

Mac 임시 분석 위치: `/private/tmp/hira-ddmd-inspect`. 원본 프로그램은 프로젝트에 추가하지 않았다. 아래 SHA-256은 Mac 분석 복사본과 Windows 원본에서 각각 계산했으며 세 파일 모두 일치했다.

| 파일 | SHA-256 |
|---|---|
| `bin/webapi.exe` | `fc777781b07ba999d5ec5bcf39399bde826a9376b7838d005a4a2703fd91912e` |
| `lib/ddmd-client-1.0.0.jar` | `833256ccd5795624f260725262dd1f6dbed04263d89de6284708f696eee86224` |
| `data/bootstrap.jar` | `47eab4f661cbeeb59a2205db970b20d4fc71df094b13173f9f0d02f512e48b1f` |

Java 분석은 클래스 파일의 상수 풀과 메서드 바이트코드를 Python으로 읽어 관련 호출과 문자열을 확인하는 방식으로 수행했다. 전체 소스 복원이나 실행 테스트는 아니다.

## 후속 조사: SAM 등록·점검 경로

추가 대상은 `bin/exam.exe`, `bin/examsnd.exe`, `bin/dmdsndui.exe`, `lib/ext/exam-Com-1.0.0.jar`이다. 이번에도 프로그램 호출·SAM 투입·GUI·원격 데이터 변경 없이 정적으로 분석했다.

추가 네 파일의 Windows 원본과 Mac 복사본 SHA-256도 모두 일치했다.

| 파일 | SHA-256 |
|---|---|
| `bin/exam.exe` | `9c2c3d7cc5124a8140d59e6d009ecbb66a0320d183a4a06d6a6dea3cfa914975` |
| `bin/examsnd.exe` | `279fa36e7aac2fee6f139ba00d551dd6b19fd5d5e2d0cd7a1f417546766ba967` |
| `bin/dmdsndui.exe` | `85a69250ef60c3e40968513bbee41f38a70f1e6a73e06e3c0cffccfd4ad9742e` |
| `lib/ext/exam-Com-1.0.0.jar` | `29b2b5f90bce44dcd842a755f65d7592c05274ddc10905f98735aedd5563f4ec` |

### 진입점 구분

| 실행 파일 | NSIS 데이터에서 확인한 명령 | Java 처리 |
|---|---|---|
| `exam.exe` | `command = exam` | 점검 경로 |
| `examsnd.exe` | `command = examSend` | 점검 및 청구 경로 |
| `dmdsndui.exe` | `command = showPanel`, `arguments = module send` | 송신 화면 호출 |

`Launcher.commandProcess`는 소문자로 바꾼 이름이 `exam`으로 시작하면 `Launcher$6`에 전달한다. 이 클래스는 `examSend`에 해당하는 경우 내부 모드 `2`, 그 외 점검은 모드 `1`로 `CExamController`를 호출한다. `CExamControllerContext`는 첫 모드가 `2`일 때 `needAuthentication=true`로 설정한다. 따라서 점검과 점검·청구를 별도 경로로 구분할 근거가 있다.

점검 경로도 `EventModuleFrame`을 열고 AWT 이벤트 큐에서 실행한다. `-update=false` 옵션 분기가 존재하지만 기본 실행에는 업데이트와 대화상자 경로가 포함되어 있다. headless 점검을 검증한 것은 아니다.

### 파일 입력과 등록 순서

1. `CExamController.main`이 `createDocumentId`로 `DMD` 문서 ID를 만들고 기존 `ExamResult.txt`를 지운 뒤 `existFileExam`을 호출한다. **ID 생성 시점 자체는 등록 성공 시점이 아니다.**
2. `CExamExistFile.exam`이 설정된 청구 SAM 폴더를 조회한다. 파일 목록을 `CExamCodeList.getSamFileCode`로 분류하고 종류·버전별 점검 모듈로 전달한다. 단일 SAM 파일 하나만을 가정하지 않는다.
3. 암호화 입력을 복호화하고 처리 파일을 삭제하는 분기가 있다. 검사 대상 SAM 파일명에는 `EUC_KR` 바이트 기준 최대 30바이트 제한이 있다.
4. 일반 경로는 `MEDLOG.ENC`를 찾고 `MedlogDAO`를 통해 청구정보를 읽는다. 거래처 ID·청구 소프트웨어 정보와 문서 제목 등을 확인해 등록 객체에 반영한다. 파일이 없을 때 `CExamMedlogController.createMedlogFrm`으로 입력 화면을 여는 경로도 있다. 따라서 MEDLOG 부재를 모든 경우의 즉시 실패로 해석하면 안 된다. 내부 `fileCodeId=11` 경로는 `LABINFO.ENC`를 별도 처리하며, 해당 코드의 업무상 의미는 확정하지 않았다.
5. `CExamController.examChoice`가 파일 종류와 버전에 따라 실제 점검을 수행한다. 한방용·첩약용 점검 분기도 확인했다. 특정 사용자의 SAM 버전과의 호환성은 확인하지 않았다.
6. `processSuccess` → `CExamSuccessController.insertDmdDocs` → `ExamRequestDocumentDAO.insertRequestDocuments`로 문서와 파일 정보를 등록한다. JAR 내 `sqlite/DdmdData_Sqlite.xml`에서 `TBJFA100`에 청구문서, `TBJFA101`에 문서별 파일 정보가 INSERT되는 것을 확인했다. 실제 기관 DB를 열거나 변경한 것은 아니다.
7. `SamDAO.saveResultTextFile`은 `C:\hira\DDMD\sam\in\ExamResult.txt`에 문서 ID와 정수 결과 코드를 CRLF로 구분하여 쓴다. ID는 `MS949`로 인코딩한다. 별도의 명령 결과 파일에는 Launcher가 정수 결과와 `.end` 완료 마커를 기록한다.

`ExamFileListDragListener`도 드롭된 파일을 설정된 청구 SAM 폴더로 복사한 후 `CExamController`를 모드 `1`로 호출한다. 이 경로는 “입력 폴더 배치 후 점검” 구조를 뒷받침한다. 실행 중 폴더 감시만으로 자동 등록되는지는 확인하지 않았다.

### 결과 코드와 부수 효과

`CExamController.examResult`의 정상 처리 경로에서 결과 코드 계산은 다음과 같다.

- `0`: 점검 성공으로 분류되는 경로.
- `1`: 오류가 있으나 청구 가능한 오류로 분류되는 경로.
- `-1`: 청구 불가 점검 오류로 분류되는 경로.

별도로 Launcher는 초기 진행 상태에 `Integer.MIN_VALUE`, 일부 취소·재시작 경로에 `-2`를 사용한다. 전체 EXE 종료코드 체계로 확대 해석하지 않는다.

오류 기록과 문서 등록은 별도 분기가 있고, 오류 문서도 `processErr`에서 등록될 수 있다. `DMD` ID가 존재하거나 DB에 행이 있다는 이유만으로 점검 통과·송신 완료로 판단해서는 안 된다. 결과 코드, 점검 상태, 등록 문서와 실제 파일 준비 상태를 함께 대조해야 한다.

점검 과정에는 압축·암호화, 백업, 파일 복사·이동·삭제, DB INSERT가 있다. 백업 경로 구성에는 청구 입력 폴더 아래 `backup/yyyyMM` 및 `SAMbackup`이 사용된다. 실행 전에는 입력 묶음을 별도 보존해야 하며, 이번 조사에서는 그러한 변경을 실행하지 않았다.

`examTransmit`은 `needAuthentication=true`인 컨텍스트에서 `SendController.sendDmdDoc`을 호출한다. 실제 점검 시험을 준비할 때 `examsnd.exe`를 점검 전용 실행 파일로 사용하면 안 된다. 점검 전용 경로에도 대화상자가 있을 수 있으므로 GUI 승인 없이 호출하지 않았다.

### Mac 연계에 대한 판단

구조상 후보 흐름은 **Mac에서 완전한 출력 묶음 준비 → Windows 입력 폴더에 배치 → 기존 DDMD의 점검 경로 실행 → ExamResult와 DB 등록 상태 대조 → 별도 인증·송신**이다.

등록 메커니즘을 찾는 정적 조사는 완료했다. 남은 것은 실제 청구 프로그램이 출력하는 파일 묶음과 버전 확인, 기존 Windows 데스크톱 세션에서의 점검 동작, 결과·등록·파일 준비 완료의 일치 검증이다. 실행 브리지는 구현하거나 활성화하지 않았다.

## Windows 완전 headless 판정

### 판정 기준과 결론

완전 headless는 로그인된 데스크톱이나 클릭·인증서 선택 창에 의존하지 않고, 새 프로세스 시작부터 SAM 점검·등록, 최초 인증, 송신, 통보 조회·수신·생성, 토큰 만료 후 재인증, 오류 결과 회수까지 수행하는 것으로 정의한다. 숨긴 창, GUI 자동 클릭, 미리 로그인한 세션이나 기존 토큰만을 이용한 성공은 이 조건을 충족하지 않는다.

**현재 설치본의 Launcher 및 기존 명령 경로 그대로는 완전 headless 구조가 아니다.** 창 생성과 대화상자 호출이 처리 경로에 포함되어 있다. `webapi.exe` 래퍼나 SSH 호출만 추가하는 방안으로 완전 headless를 달성했다고 판단할 수 없다.

**라이브러리를 재사용하고 GUI 실행 계층을 대체하는 별도 Windows gateway는 검토할 기술적 근거가 있지만, 가능성 확정은 보류한다.** 핵심 미확인 항목은 최초 인증·재인증의 무화면 수행 및 네이티브 DLL 내부 동작이다. 이번 결과는 코드 기반 판정이며 실제 headless 실행 실패·성공을 관측한 결과는 아니다.

### 직접 확인한 차단 지점

| 단계 | 설치 클래스에서 확인한 사실 | 의미 |
|---|---|---|
| Launcher 초기화 | `Launcher.<clinit>` 바이트코드 오프셋 8과 38에서 `new javax/swing/JFrame`, 각각 `DEFAULT_FRAME`·`MESSAGE_FRAME`에 저장. 해당 생성 앞에 headless 분기 없음 | 요청 처리 전부터 GUI 객체 생성에 의존 |
| SAM 점검 | `Launcher$6`가 `EventModuleFrame`을 열고 `CExamController`를 호출. 점검·오류·MEDLOG 입력 화면 경로 존재 | 기존 점검 명령을 그대로 무화면 엔진으로 취급할 수 없음 |
| 최초 인증 | `ClientContext.getAuthToken`은 XP/2003에서 `CertificateUI.showUI`, 다른 OS에서는 `KSignAxHIRA.SignedData` 경로 사용 | 현재 Windows 인증 경로에는 인증서와 키를 명시적으로 주입하는 호출이 보이지 않음. `SignedData`의 DLL 내부 UI는 미분석 |
| 송신 | `SendController.sendDmdDocs`가 인증 및 `MessageTransferDialog.setVisible(true)` 호출 | 인증을 별도로 해결해도 기존 송신 컨트롤러의 화면 의존성이 남음 |
| 통보 조회 | `ReceiveController.searchReceiveList`가 `SimpleTransferDialog`를 생성하고 표시 | 조회 또한 기존 경로에서는 GUI 결합 |
| 통보 수신·생성 | `receiveNtcDoc`의 `MessageTransferDialog`, `zipReleaseConts`의 `NtcDocGenDialog` 표시 호출 | 수신과 SAM 생성까지 분리 작업 필요 |
| 토큰 재사용 | `ReceiveWebController.searchNtcList`가 토큰 부재·만료를 검사하고 다시 인증 경로로 진입 | 사전 인증 토큰으로 한 번 성공해도 재시작·만료 후 무인 운영이 입증되지는 않음 |

`java.awt.headless=true`는 창 생성·인증·결과 처리의 대체 구현을 제공하지 않는다. 위 무조건적 JFrame 생성 때문에 기존 Launcher를 strict Java headless 모드에 그대로 넣는 방안은 코드상 적합하지 않다. Session 0에서 headless 속성 없이 숨은 창이 만들어지는 경우도 완전 headless 성공과 구분해야 한다.

### 재사용 가능성을 뒷받침하는 사실

1. `ddmd-agent-1.0.4.jar`의 `Agent` 인터페이스는 `send(DdmdMessage)`와 `asyncSend(DdmdMessage)`를 제공한다. `Credentials`는 요양기관기호·X509 인증서·추가 바이트 값과 시각·nonce를 포함하는 데이터 객체다. 이러한 구조는 UI 아래에 통신·인증 데이터 계층이 있음을 보여준다. 객체를 만들 수 있다는 사실만으로 서버 인증 성공이 보장되지는 않는다.
2. `KSignAxHIRA`에 `SignedDataCert(String,String,String,String)` 래퍼와 문자열 인자 5개를 받는 `public native` 함수가 존재한다. 클래스 파일 메서드 플래그 `0x101`로 native임을 확인했다. 래퍼의 디버그 인자명은 `strUserDn`, `strInputCert`, `strInputKey`, `strPasswd`이며 추가 DLL 경로를 전달한다. 인자명의 정확한 의미·입력 인코딩은 공식 SDK 계약으로 확인한 것이 아니다.
3. `SendController`의 메시지 생성 경로는 인증서 인코딩 값과 `DdmdPrivateKey.getEncKey()`를 구성하여 이 `SignedDataCert` 함수를 호출한다. 따라서 명시적인 키 재료를 사용하는 서명 진입점은 실제 업무 코드에 쓰인다. 다만 이미 인증으로 확보한 키를 이용하는 경로이므로, **최초 인증까지 GUI 없이 가능하다는 증거는 아니다.** DLL 호출 중 UI가 절대 열리지 않는지도 미검증이다.

상수 풀의 AWT/Swing 직접 참조를 조사한 범위는 아래와 같다. 이는 정적 결합의 지표이며, 리플렉션·전이 의존성·DLL 내부 UI의 부재를 증명하지 않는다.

| JAR | 클래스 수 | AWT/Swing 참조 클래스 |
|---|---:|---:|
| `ddmd-client-1.0.0.jar` | 362 | 170 |
| `exam-Com-1.0.0.jar` | 93 | 28 |
| `ddmd-common-2.0.2.jar` | 148 | 5 |
| `ddmd-agent-1.0.4.jar` | 33 | 0 |
| `bootstrap.jar` | 10 | 1 |

이 5개 JAR에서 `java.awt.headless`·`isHeadless` 문자열 참조는 발견하지 못했다. 모든 설치 라이브러리나 네이티브 코드에 headless 경로가 전혀 없다는 전수 결론은 아니다.

### 다음 검증을 결정하는 기준

추가 래퍼 구현보다 **인증의 독립성**을 먼저 검증해야 한다.

1. 격리된 Windows 시험 환경에서 실제 기관 인증서·SAM·HIRA 접속 없이 합성 시험 인증서와 키로 네이티브 명시적 서명·복호화 함수의 입력 규약 및 무화면 성공·실패 반환을 확인한다. 기존 설치본과 로그인 상태를 이용하지 않는다. 네이티브 UI 가능성이 남아 있으므로 실제 호출 범위는 시험 전에 확정한다.
2. 네이티브 함수가 UI를 요구하지 않는다면 `Credentials` 생성부터 인증 요청·응답·토큰 갱신까지 UI와 독립적인 호출 경로를 정리한다. 실제 서버 인증은 별도 승인된 계정·접속 범위에서 검증한다. 합성 인증서의 로컬 서명 성공을 HIRA 인증 성공으로 간주하지 않는다.
3. 인증이 확인된 뒤 점검 컨트롤러의 UI·DB·파일 작업을 분리하고, 서비스 세션에서 점검→등록→송신→통보 생성과 만료·취소·오류 반환을 검증한다. 실제 청구 제출은 별도 제출 범위에서 수행한다.

이 순서의 1·2가 실패하면, 전처리·파일 전달만 headless인 시스템은 만들 수 있어도 목표인 완전 headless gateway가 검증된 것은 아니다. 기존 DDMD를 UI 자동화로 감싼 결과를 본 목표의 성공으로 보고하지 않는다.

이번 조사에서는 네이티브 호출, 기존 Launcher의 headless 실행, 인증서 접근, 실제 인증·송수신, 서비스 설치를 실행하지 않았다. 설치본은 변경하지 않았다.

## HIRA_eform_login 인증 기반 재사용 대조

사용자가 동일 인증서·동일 프로토콜임을 확정했다. 이를 현재 설계 전제로 적용한다. 아래 비교는 이 전제를 다시 검증하려는 것이 아니라, 현재 구현의 입력·출력과 DDMD 호출 경계를 연결하기 위한 것이다.

### 갱신한 판단

`macos_agent`에는 이미 GUI 없이 NPKI 개인키를 복호화하고 CMS를 서명하는 구현이 있다. 따라서 앞 절의 “네이티브 서명 함수를 먼저 시험해야 한다”는 순서를 조정한다. **기존 Node 암호 구현을 재사용하고 DDMD 인증 요청·응답 및 키 역할을 연결하는 최소 시험을 먼저 설계할 수 있다.** Windows 인증서 선택 창을 반드시 재사용해야 한다고 볼 근거는 없다.

다만 현재 e-Form 로그인 함수를 호출한 결과만으로 DDMD `AuthToken`이 공급되지는 않는다. 동일 인증서·프로토콜을 전제로 해도 애플리케이션별 반환 객체와 운반 형식은 연결해야 한다. 전체 headless gateway 성공 판정은 여전히 보류하며, Launcher·점검·수신의 GUI 결합에 관한 앞선 판정은 유지한다.

### 코드 대조표

| 기능 | 현재 macos_agent 구현 | DDMD 연결에 필요한 사항 |
|---|---|---|
| 인증서·키 로딩 | `src/npkiLocator.js`가 `signCert.der`·`signPri.key` 쌍을 찾음 | DDMD의 서명·암호화 두 키 역할에 맞는 공급 경로 확인. 반드시 서로 다른 인증서여야 한다는 뜻은 아님 |
| 키 복호화 | `src/krPbe.js:136`의 `loadEncryptedKeyDer`가 PBES1/PBES2 SEED 기반 키를 RSA 키 객체로 반환 | 재사용 가능 기반. 함수가 원래 PrivateKeyInfo의 부가 속성까지 반환하는 것은 아니므로 DDMD의 추가 키 정보 요구와 대조 필요 |
| CMS 서명 | `src/signer.js:41`의 `signDn`이 CP949 DN, SHA-256/RSA, signedAttrs 없는 CMS를 생성 | 재사용할 암호 기반. 임의 바이너리를 DN용 UTF-8→CP949 변환에 넣으면 안 되며 원시 바이트용 경계는 별도 필요 |
| 최초 로그인 | `src/cliLogin.js:52`에서 키 일치·유효기간 검사, SSO 로그인, `/isLogin.do` 검증 후 `{http,ykiho}` 반환 | `ClientContext`의 `CLT_AUTH_REQ`와 응답 `AuthToken` 연결 필요 |
| 세션 운반 | `src/hiraHttp.js`는 `ef.hira.or.kr`·`extsso.hira.or.kr` 쿠키 세션 및 HTML/SSV 처리 | DDMD의 메시지 운반·바이너리 요청/응답과 같은 함수라고 취급하지 않음. 기존 허용 도메인을 수정하지 않았음 |
| 재인증·연장 | 현재 `src`의 CLI 구현에 DDMD 토큰 만료·연장·재발급 흐름 없음 | DDMD 토큰 상태 관리와 재인증 호출을 추가해야 함 |
| 비밀 공급 | `src/keychain.js`의 macOS Keychain 조회 | Windows 실행 계층에서 같은 코드를 그대로 실행할 수 없음. 실제 키·비밀번호를 argv·로그로 보내는 방식은 채택하지 않음 |

`src/session.js`는 로컬 KCase WebSocket 연결의 SEED 채널 상태다. 이를 DDMD 서버의 AuthToken과 혼동하지 않는다. `src/ssoServer.js`의 토큰 경로는 에뮬레이션 응답을 포함하며 DDMD 토큰 재발급 구현의 증거로 사용할 수 없다.

### DDMD가 실제로 요구하는 결과

`ClientContext.getAuthToken`의 Windows 경로는 `SignedData` 반환 문자열을 `$`로 분리하고 5개 항목을 요구한다. 뒤의 네 항목으로 서명 인증서/키와 암호화 인증서/키 정보를 구성한다. `macos_agent.signDn`의 반환값은 CMS DER의 base64 문자열 하나이므로, 이 문자열을 해당 자리에 그대로 넘기는 것은 호환되지 않는다. 키 재료는 실제로 읽거나 출력하지 않았으며 설치 코드의 구조만 분석했다.

이후 흐름은 다음과 같다.

1. `KeyInfoSet`에 서명 키·암호화 키·추가 바이트 값을 구성한다.
2. `Credentials`에 요양기관기호, 서명 인증서, 추가 바이트 값, timestamp·nonce를 담아 `CLT_AUTH_REQ` 메시지를 만든다. 일부 호출은 `long-term` 속성을 설정한다.
3. `ClientAgentProxy`가 인증 요청을 `MessageCipherAgent`로 분기한다.
4. `MessageCipherAgent.beforeRequestSend`가 본문을 **Java ObjectOutputStream으로 직렬화**하고 본원 암호화 인증서로 `EnvelopedDataCipher` 암호화를 수행한다. 이 구조는 DN SignedData 하나를 반환하는 함수보다 넓은 처리 범위다.
5. `afterResponseReceive`가 요청 처리에 사용한 대칭키 정보로 응답을 복호화하고 객체로 복원한다. `ClientContext`는 응답 본문을 `AuthToken`으로 받고 `SecureInfoContainer.put(token,keyInfoSet)`에 보관한다.
6. `AuthToken`에는 `tokenId`, 만료 시각과 속성이 있다. `updateAndGetVerifier`는 `digestAlgorithm`, `verifier`, `nonce`를 사용해 검증값을 갱신한다. `updateExpiredTime`은 응답 토큰을 이용한 만료 시각 갱신 경로다. 실제 서버에서 언제 연장·재발급하는지는 이번에 호출하지 않았다.

따라서 최소 연결 단위는 웹 쿠키 전달이 아니라 **키 공급 + DDMD 인증 메시지 처리 + AuthToken/KeyInfoSet 수명 관리**다. Java 객체 직렬화까지 Node에서 새로 작성하기보다, 해당 데이터·통신 라이브러리를 재사용하는 독립 Java 실행부를 우선 검토할 근거가 생겼다. 이 실행부가 기존 ClientContext/ResourceContainer를 통해 다시 GUI를 끌어오지 않는지는 별도 격리 검증해야 한다.

### 이번 검증과 남은 범위

- `macos_agent` 저장소는 `main...origin/main`이며 조사 전후 working tree가 깨끗했다. 부모 workspace는 Git 저장소가 아니다.
- `node scripts/test-signer.js` 실행 성공: 합성 RSA-2048 인증서·키 사용, 잘못된 비밀번호 분류 확인, 기존 `signDn`의 CMS를 OpenSSL로 검증했다.
- 이 테스트는 PBES2/SEED와 ASCII 시험 DN을 사용한다. PBES1·한글 DN·실제 HIRA 서버 수용 여부를 이번 실행만으로 검증한 것은 아니다.
- 실제 인증서·Keychain·캡처 파일·쿠키·SAM은 열지 않았고, HIRA 서버 접속·인증·청구 전송·실행 코드 수정은 하지 않았다.

현재 재사용 가능한 기반과 부족한 경계의 대조는 완료했다. 다음 최소 구현·검증은 합성 키를 이용해 **UI 없는 KeyInfoSet 공급과 CLT_AUTH_REQ의 직렬화·암호화 왕복**을 확인하는 것이다. 인증 서버 접속과 토큰 발급은 그 이후의 실제 환경 검증이며, 현재 완료로 표시하지 않는다.

## 2026-09-09 실행 검증: 합성 headless 인증 경계

위 최소 PoC를 [gateway_poc/README.md](HISTORY.md#ddmd-offline)에 구현·검증했다. **Windows Session 0에서 Java strict headless 모드의 17개 검사가 통과했다.** 실행한 소스와 라이브러리는 `gateway_poc/evidence/run.json`의 SHA-256으로 식별한다.

실제 DDMD 데이터 클래스 및 `JCAOSSecurityProvider`를 이용해 UI 없이 KeyInfoSet 공급, Credentials 직렬화, SEED 봉투 암호화·복호화, 합성 AuthToken 응답 복원, 만료 판정과 연장, verifier 갱신을 수행했다. 비정상 봉투 입력도 UI 없이 예외로 반환됐다. Node에서 기존 키 복호화 코드를 사용한 합성 키를 Java에 공급했고, Java 봉투를 기존 Node SEED 코드로 복호화하여 직렬화 원본과 일치했다. 한글 합성 DN에 대한 기존 CMS 서명도 OpenSSL로 검증했다.

PoC는 기존 Launcher/ClientContext/MessageCipherAgent를 직접 실행하지 않았다. GUI 결합이 있는 MessageCipherAgent의 직렬화·암호화 순서를 독립 실행부에 구성하고 원본 데이터·암호 클래스를 재사용했다. 네트워크·프로세스·추가 네이티브 로딩·AWT 권한 차단을 유지했으며, guard 자기시험 외의 차단 이벤트는 없었다. JRE 기본 난수·암호 공급자는 guard 전 초기화한다.

**갱신한 결론: 인증 객체·암호 계층을 Windows에서 headless로 재사용할 수 있다는 실행 근거를 확보했다.** 인증서 선택 GUI나 HIRA 전용 DLL을 이 합성 경로에서 호출할 필요가 없었다. 반면 실제 HIRA 서버의 최초 인증·토큰 발급·재발급, 실제 인증서의 키 부가 정보 호환성, SAM 점검·실제 청구·통보 처리는 아직 검증하지 않았다. 합성 토큰의 만료 시각 연장을 실제 서버의 갱신 성공으로 해석하지 않는다.

최종 실행 증거: Windows 검사 결과: `ddmd/gateway_poc/evidence/windows-probe.txt` (local only), Node 교차 복호화 결과: `ddmd/gateway_poc/evidence/node-interop.txt` (local only), 실행 식별 정보: `ddmd/gateway_poc/evidence/run.json` (local only). 기존 `macos_agent` 코드는 변경하지 않았고, DDMD 설치본·기관 DB·실제 인증서·SAM을 수정하지 않았다.

## 2026-09-09 실제 인증 서버 연결 결과

후속 SAM 시험 범위는 [SAM 시험 경로 확인](ddmd-sam-test-boundary.md)을 따른다. 사전점검·SW검사·개발서버 코드의 존재를 확인했으나 현재 기관 인증서의 개발 시험 권한은 미확인이다. 본청구 및 시험 SAM 송신은 실행하지 않는다.

**01:00:03 KST, Windows Session 0의 headless 실행부에서 실제 HIRA AuthToken을 복원하고 tokenId 존재·미만료 검사를 통과했다.** 사용자 지정 macOS KICA 인증서와 기존 Keychain 비밀번호를 사용했다. 비밀번호·개인키는 Mac에서만 처리했고, 인증에 필요한 공개 인증서와 실제 VID random을 SSH 표준입력으로 공급했다.

원본 DDMD Credentials·JCAOS 암호·MSI 통신 라이브러리를 이용하여 `http://ddmd.hira.or.kr/imxs/msi`에 `CLT_AUTH_REQ`를 전송했다. 응답은 요청의 대칭키로 복호화하고 제한된 Java 클래스만 허용하여 복원했다. 최종 응답은 `AuthToken`이며 만료 시각은 01:05:03.671 KST였다. tokenId·키·verifier·응답 payload는 출력하거나 저장하지 않았다.

최초 로컬 guard의 outbound bind 차단 오류를 수정했다. 이후 서버 응답의 `SecretKeySpec` 클래스 허용 목록 문제를 두 번의 응답 진단으로 확인하고 표준 클래스 하나를 추가하여 마지막 인증 실행을 통과했다. 실제 인증 실행은 3회이며 자동 재시도는 없었다. 이 반복 실행을 만료 후 재발급이나 서버 연장 검증으로 해석하지 않는다.

**판정 갱신: 실제 최초 인증까지는 Windows 완전 headless 경로가 가능하다.** GUI 인증서 선택·HIRA 전용 인증 DLL 호출이 필수라는 장애 요인은 이 경로에서 해소됐다. 전체 gateway 판정에는 후속 토큰 사용·만료 후 재인증, SAM 점검·청구·통보 처리의 실행 증거가 더 필요하다. 이번에는 인증 action만 호출했다.

구현·상세 근거: [실제 인증 README](HISTORY.md#ddmd-live), 성공 결과: `ddmd/gateway_poc/evidence/live-result.json` (local only), 실행 환경 대조: `ddmd/gateway_poc/evidence/live-environment.json` (local only). `macos_agent` 코드는 변경하지 않았다.

## 2026-09-09 SAM 제외 추가 검증

[gateway 실행부](HISTORY.md#ddmd-gateway)에서 실제 토큰의 만료시각까지 대기 후 재인증·새 tokenId 발급을 확인했다. 독립 SSH/JVM 프로세스를 다시 실행해 인증 복구도 통과했다. 토큰 헤더와 MAC을 이용하는 `CLT_CERT_REQ`는 MSI transport에서 수신처 공개 인증서 1건과 응답 AuthToken을 반환했다. SAM·청구문서·통보를 조회하거나 전송하지 않았다.

비정상 인증 응답과 연결 차단 처리는 로컬 오류 주입으로 통과했다. 잘못된 비밀번호·인증서를 운영 서버에 보내는 시험, 만료 토큰의 서버 거절 검증, 실제 네트워크 장애 재현은 하지 않았다. 요청된 SAM 제외 인증·조회 CLI 범위의 결과이며 상시 서비스 또는 전체 MXS/ebMS 업무 gateway 완료를 의미하지 않는다.
