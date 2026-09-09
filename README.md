# HIRA e-Form login for macOS

**v1.0.0 · macOS에서 심평원 e-Form 시스템의 공동인증서 로그인**

Windows용 KCase/KAccess 로컬 통신의 일부를 Node.js로 재현한다.
지원 범위는 **[ef.hira.or.kr](https://ef.hira.or.kr)의 확인된 로그인 흐름**이다.
HIRA 전체 사이트나 모든 인증기관에 대한 호환성을 보장하지 않으며, HIRA·KSIGN의 공식 제품이 아니다.

## 사용 방식

| 방식 | 진입점 | 용도 |
|---|---|---|
| 메뉴 막대 앱 | `HIRA e-Form.app` | `eF` 메뉴에서 브라우저용 서버 시작·중지 |
| 터미널 서버 | `npm start` | 같은 로컬 서버를 터미널에서 실행 |
| CLI 수집 | `npm run collect:chuna -- --from YYYY-MM-DD --to YYYY-MM-DD` | 브라우저 없이 로그인하고 한방추나요법 조회 결과를 로컬 저장 |

CLI 수집은 위 로컬 서버를 켤 필요가 없다. Keychain 준비와 개인정보 처리 범위는
[CLI 수집 가이드](docs/CLI_COLLECTION.md)를 먼저 확인한다.
별도 [DDMD 연구](ddmd/README.md)는 이 메뉴 막대 앱이나 e-Form 로그인과 다른 작업이다.

## 설치와 실행

### 1. 공통 준비

macOS, Node.js 20 이상, 본인 또는 사용 권한이 있는 공동인증서가 필요하다.
앱을 직접 빌드할 때는 Xcode Command Line Tools도 필요하다.

```bash
git clone https://github.com/Raphael-KR/hira-eform-macos.git
cd hira-eform-macos
npm ci
```

인증서 기본 탐색 위치:

```text
~/Library/Preferences/NPKI/<CA>/USER/<DN>/signCert.der
~/Library/Preferences/NPKI/<CA>/USER/<DN>/signPri.key
```

브라우저용 서버에는 로컬 TLS 인증서가 필요하다. 이미 설정했다면 재생성하지 않는다.
처음 설정할 때만 아래 명령으로 생성하고, 생성한 인증서를 확인한 뒤 신뢰를 등록한다.
신뢰 등록은 사용자의 login Keychain 설정을 변경한다.

```bash
npm run gen-cert
security add-trusted-cert -d -r trustAsRoot \
  -k ~/Library/Keychains/login.keychain-db certs/server.crt
```

TLS 개인키와 인증서는 이 Mac에만 보관한다. 앱이 이를 자동 생성하거나 신뢰 등록하지 않는다.

### 2. 메뉴 막대 앱

```bash
npm run build:app
```

출력된 `dist/build-*/HIRA e-Form.app`을 응용프로그램 폴더로 옮겨 실행한다.
기존 앱을 교체할 때는 먼저 종료한다.

- 앱을 열면 서버는 꺼진 상태다. 메뉴의 **서버 시작**을 눌러 사용한다.
- `eF` 회색: 꺼짐 또는 전환 중, 녹색: 실행 중, 빨간색: 오류 또는 포트 충돌.
- 상태에 따라 시작·중지 중 하나만 표시한다. 별도 재시작 항목은 없다.
- 터미널에서 실행한 서버는 앱이 종료하지 않는다. 포트가 겹치면 먼저 해당 서버를 직접 종료한다.
- 앱 실행만으로 인증서 로그인·Keychain 조회·자동 시작 등록을 하지 않는다.

**프로젝트 폴더와 설치된 Node에 연결되는 로컬 앱**이다. 이들을 이동하면 다시 빌드해야 한다.
독립 실행형·Developer ID 공증 배포판이 아니다. 상세 내용은 [앱 가이드](docs/MENUBAR_APP.md)를 참조한다.

### 3. 터미널에서 실행할 경우

```bash
npm start
```

서버를 켠 상태에서 e-Form의 공동인증서 로그인을 진행한다. 인증서가 여러 개라면
터미널 실행에 한해 파일 경로를 명시할 수 있다. 암호는 환경변수나 명령 인자로 넣지 않는다.

```bash
HIRA_SIGN_CERT="/path/to/signCert.der" \
HIRA_SIGN_KEY="/path/to/signPri.key" npm start
```

앱은 최소 환경으로 실행하므로 셸의 환경변수를 자동으로 물려받지 않는다.
CLI 수집은 인증서 쌍 하나를 명확히 선택하도록 요구한다.
서버를 재시작했다면 기존 로그인 팝업을 닫고 페이지를 새로 열어 세션을 다시 만든다.

## 동작 구조

확인한 e-Form 로그인 페이지는 인증서에 직접 접근하지 않고 로컬 에이전트 두 개를
호출한다. macOS에서 해당 Windows 실행 파일을 사용할 수 없어 필요한 통신을 재현했다.

```text
Browser: ef.hira.or.kr
  |-- HTTPS 127.0.0.1:39091 --> KAccess subset (SSO stub)
  |-- WSS   127.0.0.1:8443  --> KCase subset --> NPKI / CMS signer
  '-- signed login form -------------------> HIRA external SSO
```

두 로컬 포트는 브라우저가 각각 호출하며, SSO 서버를 거쳐 PKI 서버로 순차 전달되는 구조가 아니다.
CLI 경로는 별도로 Node HTTP·cookie jar·Cheerio·Acorn을 사용한다.

## 로그인에 사용한 CMS 형태

Windows 참고 결과와 대조해 아래 형태를 적용한 뒤 실제 e-Form 로그인을 확인했다.

1. **signedAttrs 없음**: 콘텐츠 바이트를 SHA-256/RSA로 직접 서명한다.
2. **콘텐츠는 CP949 DN**: 브라우저의 UTF-8 입력을 CP949로 변환한다.
3. **signatureAlgorithm은 sha256WithRSAEncryption**: OID `1.2.840.113549.1.1.11`을 사용한다.

이는 확인된 구현 프로파일이다. 각 변경의 필요성을 독립 실험으로 증명하거나,
모든 HIRA 서버·CMS 검증기가 같은 형태만 허용한다고 확인한 것은 아니다.
[서명 흐름과 공개용 ASN.1 예시](docs/SIGN_FLOW.md), [실험 이력](docs/HISTORY.md)을 참고한다.

## 문서와 코드

| 문서 | 내용 |
|---|---|
| [메뉴 막대 앱](docs/MENUBAR_APP.md) | 빌드·설치·상태·프로세스 소유권 |
| [CLI 수집](docs/CLI_COLLECTION.md) | Keychain 설정·HTTP 로그인·조회·비공개 결과 |
| [서명 흐름](docs/SIGN_FLOW.md) | 프레이밍·암호·CMS 구조·오류 처리 |
| [작업 히스토리와 실험](docs/HISTORY.md) | e-Form 로그인·CLI 수집·앱 개발 과정 |
| [공개 준비](docs/RELEASE.md) | 공개 파일 검토·테스트·Git 승인 경계 |
| [DDMD 연구](ddmd/README.md) | 별도 Java 도구와 현재 중지된 시험 환경 |

주요 코드: [Swift 앱](macos/main.swift),
[서버](src/server.js), [프로토콜](src/protocol.js),
[CMS 서명](src/signer.js), [인증서 탐색](src/npkiLocator.js),
[CLI 진입점](scripts/collect-chuna.js).

## 검증

```bash
npm test
npm run test:app
npm run check:release
git diff --check
```

기본 검사는 합성 인증서·임시 포트를 사용한다. 실제 계정 로그인이나 환자 조회를 하지 않는다.
DDMD의 별도 합성 검사는 `npm run test:ddmd`다. 테스트 통과가 실서버·GUI·공증 검증을 대신하지 않는다.

## 개인정보와 배포 경계

- 암호·개인키·CMS·쿠키·캡처·기관/환자 조회 결과를 코드·로그·커밋에 넣지 않는다.
- 서명 콘텐츠가 정적 DN이므로 실제 CMS도 민감 인증 산출물로 취급한다. 공개 예시에 실제 바이트를 쓰지 않는다.
- 브라우저 경로는 입력 암호와 복호화 키를 프로세스 메모리에 보관한다. CLI Keychain 저장은 별도 명시적 설정이 필요하다.
- `HIRA_DEBUG=1`도 요청/응답 본문 대신 메타데이터만 출력한다.
- `tmp/`, `.local/`, `dist/`, 인증서·빌드 산출물은 로컬 전용이다. 제외된 파일도 강제 stage하면 유출될 수 있으므로 공개 검사를 수행한다.

## 프로젝트 성격

권한 있는 인증서의 소유자가 자신의 Mac에서 확인된 e-Form 기능을 사용하는 비공식 구현이다.
무보증이며 실제 청구 전송이나 다른 사이트의 동작을 보장하지 않는다.
제품·회사명은 호환 대상 설명을 위한 것이다.

통신 분석과 브라우저 JavaScript를 참고했으며, `src/seed.js`에는 클라이언트 SEED 구현에서
옮긴 코드가 포함되어 있다. 기술적 재현 성공이나 공개 파일 검사가 배포 권리·법적 적합성을
입증하는 것은 아니다. 공동인증서 키 형식의 독립 구현 참고 자료로
[PyPinkSign](https://github.com/bandoche/PyPinkSign)이 있다.
