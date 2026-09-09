import os
"""Run synthetic-only PoC; never invokes DDMD entry points or uses real credentials."""
import base64, datetime, hashlib, json, pathlib, subprocess, tempfile, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
HOST='user@192.168.219.146'
INSPECT=pathlib.Path('/private/tmp/hira-ddmd-inspect')
COMPILER=INSPECT/'ecj-3.26.0.jar'
EXPECTED_COMPILER_SHA1='4837be609a3368a0f7e7cf0dc1bdbc7fe94993de'
if hashlib.sha1(COMPILER.read_bytes()).hexdigest()!=EXPECTED_COMPILER_SHA1:raise SystemExit('Compiler checksum mismatch')
local=pathlib.Path(tempfile.mkdtemp(prefix='hira-headless-poc-'))
name=local.name
remote=os.environ['DDMD_WINDOWS_TEMP'].rstrip('/'+chr(92))+'/'+name
remote_win=remote.replace('/','\\')
evidence=ROOT/'evidence';evidence.mkdir(exist_ok=True)

def ps(script, timeout=120):
    body="$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; [Console]::OutputEncoding=New-Object System.Text.UTF8Encoding; "+script
    command='powershell -NoProfile -EncodedCommand '+base64.b64encode(body.encode('utf-16le')).decode()
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10',HOST,command],capture_output=True,text=True,timeout=timeout)
    if result.returncode:raise RuntimeError('Remote probe failed: '+result.stdout+'\n'+result.stderr)
    return result.stdout

subprocess.run(['node',str(ROOT/'scripts/make-fixtures.mjs'),str(local)],check=True)
subprocess.run(['openssl','cms','-verify','-inform','DER','-in',str(local/'signed.cms'),'-CAfile',str(local/'cert.pem'),'-purpose','any','-out',str(local/'verified.bin')],check=True,capture_output=True)
assert (local/'verified.bin').read_bytes()==(local/'content.bin').read_bytes()
print('PASS Node CMS signature and CP949 content verified by OpenSSL',flush=True)
libs=['lib/ddmd-common-2.0.2.jar','lib/ddmd-agent-1.0.4.jar','lib/bizframe-commons-1.1.2-jdk5.jar','lib/shared/log4j-1.3alpha-9.jar','lib/shared/commons-io-2.0.1.jar','lib/shared/commons-codec-1.4.jar','lib/security/jcaos/jcaos-1.3.2.2.jar','lib/security/jcaos/bcprov-jdk15-146.jar','lib/security/jcaos/bcmail-jdk15-146.jar','lib/security/npkcrypt/ksign_ui-1.5.jar']
setup="New-Item -ItemType Directory -Path '"+remote_win+"\\lib','"+remote_win+"\\classes','"+remote_win+"\\javatmp' | Out-Null; "
for lib in libs:
    setup+="Copy-Item -LiteralPath 'C:\\hira\\DDMD\\"+lib.replace('/','\\')+"' -Destination '"+remote_win+"\\lib'; "
ps(setup)
subprocess.run(['scp','-q',str(COMPILER),str(ROOT/'src/HeadlessAuthProbe.java'),str(local/'signCert.der'),str(local/'private.pk8'),HOST+':'+remote+'/'],check=True)
java='C:\\hira\\DDMD\\jre18\\bin\\java.exe'
command="Set-Location '"+remote_win+"'; $cp=(Get-ChildItem '.\\lib\\*.jar').FullName -join ';'; & '"+java+"' -jar .\\ecj-3.26.0.jar -1.8 -proc:none -classpath $cp -d .\\classes .\\HeadlessAuthProbe.java; if($LASTEXITCODE -ne 0){throw 'compile failed'}; & '"+java+"' '-Djava.awt.headless=true' '-Djava.io.tmpdir="+remote_win+"\\javatmp' -classpath ('.\\classes;'+$cp) HeadlessAuthProbe '"+remote_win+"'; if($LASTEXITCODE -ne 0){throw 'probe failed'}; Get-Process -Id $PID | ForEach-Object {'SESSION '+$_.SessionId}"
try:
    output=ps(command)
except Exception as e:
    (evidence/'last-failure.txt').write_text(str(e))
    print('Probe evidence: '+str(evidence/'last-failure.txt'),flush=True)
    raise
(evidence/'windows-probe.txt').write_text(output)
print(output,flush=True)
subprocess.run(['scp','-q',HOST+':'+remote+'/request.cms',HOST+':'+remote+'/request.bin',str(local)+'/'],check=True)
interop=subprocess.run(['node',str(ROOT/'scripts/verify-java-envelope.mjs'),str(local)],capture_output=True,text=True,check=True)
(evidence/'node-interop.txt').write_text(interop.stdout)
print(interop.stdout,flush=True)
hashcmd="Get-ChildItem '"+remote_win+"\\lib\\*.jar' | Get-FileHash -Algorithm SHA256 | Select-Object Path,Hash | ConvertTo-Json -Compress"
library_hashes=json.loads(ps(hashcmd))
state={'local':str(local),'remote':remote,'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'libraries':library_hashes,'compilerSha1':EXPECTED_COMPILER_SHA1,'nodeCmsVerified':True,'nodeJavaEnvelopeVerified':True,'javaSourceSha256':hashlib.sha256((ROOT/'src/HeadlessAuthProbe.java').read_bytes()).hexdigest(),'actualServerAuthentication':False}
(evidence/'run.json').write_text(json.dumps(state,indent=2)+'\n')
print('FIXTURE_DIR '+str(local),flush=True)
