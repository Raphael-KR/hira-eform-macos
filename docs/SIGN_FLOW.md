# e-Form 서명 흐름

범위: 확인된 `ef.hira.or.kr`의 `hira.sign("")` / APIName 21 경로.
현재 사용법은 [README](../README.md), 실패·수정 이력은 [HISTORY](HISTORY.md)를 참조한다.
일반적인 KCase 전체 명세나 새 암호 프로토콜 설계 권고가 아니다.

## 로컬 엔드포인트

브라우저는 KCase `wss://127.0.0.1:8443`와 KAccess
`https://127.0.0.1:39091`를 각각 호출한다.
확인된 페이지에서는 PKI 초기화 성공 콜백 뒤 SSO 초기화·버전 확인과 인증서 선택을 진행한다.

SSO는 [ssoServer.js](../src/ssoServer.js)의 제한적인 REST stub이다.
`POST /init`은 `{"resultCode":"INIT1"}`,
`POST /CheckVersion`의 `version=1.0.4.7` 요청은
`{"resultCode":"UPDATE00"}`으로 응답한다. 이 클라이언트에서 UPDATE01은 업데이트 필요다.
다른 토큰 엔드포인트까지 실제 KAccess 구현과 동등하다고 검증한 것은 아니다.

## Bootstrap

구현: [server.js](../src/server.js), [protocol.js](../src/protocol.js),
[session.js](../src/session.js). 상태는 WebSocket 연결별이다.

| 단계 | 요청 | 응답·처리 |
|---|---|---|
| hello | `0open` | 응답하지 않음. 빈 객체도 설치 응답으로 오인될 수 있음 |
| CHECK_INSTALL (0) | `{"APIName":0}`, Method=install | Status=0, Version=1.3.28 |
| INTEGRITY_INIT (1) | Version·Config 등 | Status, Version, SessionId, PubKey, Hash, IntMsg, KcmvpVersion |
| HANDSHAKE (2) | EncryptedKey | Status, SessionId, HandshakeMsg |

데이터 요청은 `1data=` 뒤에 `{SessionId, Data, Method}` JSON을 붙인다.
bootstrap의 Data는 Base64로 인코딩한 JSON 바이트이며,
install 이외에는 JSON 앞에 **16바이트 keyId**가 있다.

INTEGRITY_INIT:
- 연결별 RSA-1024 키를 생성한다. 레거시 상호운용 용도이며 현대적 신규 설계 권고가 아니다.
- PubKey는 **raw RSAPublicKey DER의 Base64**다. 함수 이름
  `getPubKeyBase64Spki()`와 달리 SPKI 래퍼를 반환하지 않는다.
- Hash는 128개 랜덤 바이트의 Base64 문자열이다.
- IntMsg는 **Hash 문자열 자체**의 SHA-256을 RSA PKCS#1 v1.5로 서명한 Base64다.
- KcmvpVersion은 UI 호환 값 `2.5.1.1`이며, 이 에뮬레이터의 KCMVP 인증을 뜻하지 않는다.

HANDSHAKE의 RSA PKCS#1 v1.5 복호화 결과는
`SEED key(16) || IV(16) || nonce(32)`로 총 64바이트다.
**이 응답 자체는 평문 JSON**이며, HandshakeMsg만 nonce32를 SEED-CBC로
암호화한 Base64다. 후속 요청부터 아래 secure 프레이밍을 적용한다.

## Secure 프레이밍

요청과 응답은 서로 다른 형태다.

```text
Request Data =
  Base64(keyId[16] || SEED-CBC(Base64(nonce[8]) || Base64(JSON)))
                                    12 characters

Response =
  {"Output": Base64(SEED-CBC(JSON({Status, ...result})))}
```

응답에는 요청의 keyId/nonce prefix가 없다. API 21 성공이면 복호화된 내부
Output은 CMS Base64이고, 바깥 Output은 응답 암호문이다. 둘을 혼동하지 않는다.
세션 중 서버를 재시작하면 기존 브라우저 키를 복원하지 못하므로 페이지를 다시 열어야 한다.

## 인증서 목록과 keep-alive

CERT_LIST (10) 요청 예시:

```json
{"APIName":10,"Media":0,"Drive":0,"CertOpt":15233,"CertPolicies":[]}
```

복호화된 응답은 `{Status:0, CertList:[], CertStatus:[]}`다.
CertList 각 항목은 `Base64(UTF8(JSON(certObj)))`이며 같은 인덱스의 상태가 CertStatus에 있다.
상세 필드는 [certInfo.js](../src/certInfo.js)가 정의한다.
forge가 반환하는 DN byte-string을 Unicode로 변환한 뒤 직렬화해 한글 이중 인코딩을 피한다.
현재 구현의 유효기간 검사가 CA 신뢰·폐지 검증까지 수행한다는 뜻은 아니다.

AGENT_CHECK (8)는 암호화된 `{Status:0}`으로 응답한다.

## 서명 요청과 암호 오류

CERT_GENERATE_SIGNDATA (21)의 주요 필드:

```json
{
  "APIName": 21,
  "Media": 0,
  "CertDn": "<base64 UTF-8 DN>",
  "CertSn": "<certificate serial>",
  "Input": "<base64 UTF-8 DN>",
  "Password": "{\"IsSec\":0,\"Data\":\"<password entered locally>\"}"
}
```

`signedDN:true` 경로에서는 Input이 DN이다. Password는 JSON 래퍼의 Data를
추출해 사용하며 IsSec가 0이 아닌 전송 암호 방식은 지원하지 않는다.

[krPbe.js](../src/krPbe.js)는 암호화된 PKCS#8 키를 읽는다.
실제 KICA 키에서 확인한 PBES1 `1.2.410.200004.1.15`의 파생식:

```text
dk  = SHA1^iterations(UTF8(password) || salt)
key = dk[0:16]
iv  = SHA1(dk[16:20])[0:16]
```

PBES2/PBKDF2/SEED-CBC 경로는 합성 키로 시험했다. 두 시험의 증거 범위를 구분한다.
틀린 암호의 패딩 실패뿐 아니라 복호화 후 ASN.1 해석 실패도
`BadPasswordError`로 처리한다. 내부 `{Status:24584}` (0x6008)을 정상 secure
응답으로 보내므로 브라우저가 암호 안내를 표시하고 재입력할 수 있다.
이는 키 손상과 암호 오류를 완벽하게 구별하는 진단은 아니다.

## CMS 생성과 사이트 로그인

[signer.js](../src/signer.js)의 현재 프로파일:

1. Input Base64를 UTF-8 문자열로 해석하고 iconv-lite로 **CP949** 바이트를 만든다.
2. 콘텐츠와 인증서를 SignedData에 넣고 RSA 개인키로 SHA-256 서명한다.
3. **authenticatedAttributes를 생략**해 signedAttrs 없는 SignerInfo를 만든다.
4. signatureAlgorithm을 **sha256WithRSAEncryption**으로 설정해 DER/Base64를 반환한다.

내부 성공 응답 `{Status:0, Output:"<CMS Base64>"}`를 위 secure 응답으로 감싼다.
이후 사이트 JavaScript가 서명 폼을
`https://extsso.hira.or.kr/sso/pmi-sso-login-certificate.jsp`로 전송하고,
사이트의 HTTP/SSO 흐름에서 로그인을 마친다. 로컬 SSO stub이 이 서버 검증을 수행하지 않는다.
브라우저 없는 별도 HTTP 경로는 [CLI_COLLECTION](CLI_COLLECTION.md)에 정리했다.

이 형태를 적용한 뒤 실제 로그인을 확인했다. 오류 [8]만으로 특정 필드의 문제라고
단정할 수 없으며, 세 변경 각각의 필요성이나 다른 OID 수용 범위를 분리 입증하지 않았다.

<a id="cms-example"></a>

## 공개용 ASN.1 예시

기존 `reference-cms.txt`를 이 절로 통합했다. 가상 DN
`c=KR,o=KICA,ou=licensedCA,ou=개인,cn=홍길동`의 구조 설명이며 실제 인증서·서명 바이트가 아니다.

```text
ContentInfo
  contentType: 1.2.840.113549.1.7.2 (signedData)
  [0] SignedData
    version: 1
    digestAlgorithms: SET { AlgorithmIdentifier(sha256, NULL) }
    encapContentInfo
      contentType: 1.2.840.113549.1.7.1 (data)
      [0] OCTET STRING: CP949(DN)
    [0] certificates: Certificate
    signerInfos: SET OF SignerInfo
      version: 1
      sid: issuerAndSerialNumber
      digestAlgorithm: sha256, NULL
      signatureAlgorithm: sha256WithRSAEncryption, NULL
      signature: OCTET STRING (RSA PKCS#1 v1.5)
```

SignerInfo는 signedAttrs 없이 다섯 필드다. SHA-256 OID는
`2.16.840.1.101.3.4.2.1`, sha256WithRSAEncryption은
`1.2.840.113549.1.1.11`이다. forge 기본값 rsaEncryption
`1.2.840.113549.1.1.1`과 구분한다. CP949와 UTF-8 차이의 예로
`미`는 각각 `B9 CC`, `EB AF BC`다.

## 진단과 비공개 자료

| 도구 | 경계 |
|---|---|
| `node scripts/test-sign.js` | Keychain을 사용하는 실제 로컬 서명 검사. CMS 출력 없음 |
| `node scripts/verify-keychain.js` | 실제 암호·키·인증서 일치 검사 |
| `node scripts/inspect-cms.js <file>` | 개인 CMS 분석 전용. 출력에는 민감 정보가 포함될 수 있음 |
| `npm test` | 합성 키·프로토콜·수집 회귀 검사 |

실제 암호를 argv·환경변수·로그·문서에 넣지 않는다.
CMS와 네트워크 캡처도 민감 인증 자료로 취급해 Git·공유 채널에서 제외한다.
이 문서 정리에 실제 인증서·캡처·Keychain 값은 사용하지 않았다.
