import os
import base64,datetime,json,pathlib,subprocess,hashlib
root=pathlib.Path(__file__).resolve().parents[1]
name='hira-live-auth-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
remote=os.environ['DDMD_WINDOWS_TEMP'].rstrip('/'+chr(92))+'/'+name
rw=remote.replace('/','\\')
libs=['lib/ddmd-common-2.0.2.jar','lib/ddmd-agent-1.0.4.jar','lib/bizframe-commons-1.1.2-jdk5.jar','lib/shared/log4j-1.3alpha-9.jar','lib/shared/commons-io-2.0.1.jar','lib/shared/commons-codec-1.4.jar','lib/security/jcaos/jcaos-1.3.2.2.jar','lib/security/jcaos/bcprov-jdk15-146.jar','lib/security/jcaos/bcmail-jdk15-146.jar','lib/security/npkcrypt/ksign_ui-1.5.jar','lib/bizframe-msi-1.0.0.jar','lib/shared/commons-httpclient-3.1-modified.jar','lib/shared/commons-logging-1.1.1.jar','lib/shared/spring-2.5.6.jar']
def ps(s):
 b="$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue';[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding;"+s
 r=subprocess.run(['ssh','-o','BatchMode=yes','user@192.168.219.146','powershell -NoProfile -EncodedCommand '+base64.b64encode(b.encode('utf-16le')).decode()],capture_output=True,text=True,timeout=90)
 if r.returncode:raise RuntimeError(r.stdout+'\n'+r.stderr)
 return r.stdout
s="New-Item -ItemType Directory -Path '"+rw+"\\lib','"+rw+"\\classes','"+rw+"\\javatmp','"+rw+"\\parts' | Out-Null;"
for lib in libs:s+="Copy-Item -LiteralPath 'C:\\hira\\DDMD\\"+lib.replace('/','\\')+"' -Destination '"+rw+"\\lib';"
ps(s)
compiler=pathlib.Path('/private/tmp/hira-ddmd-inspect/ecj-3.26.0.jar')
assert hashlib.sha1(compiler.read_bytes()).hexdigest()=='4837be609a3368a0f7e7cf0dc1bdbc7fe94993de'
subprocess.run(['scp','-q',str(root/'gateway/HeadlessGateway.java'),str(root/'gateway/RecipientProbe.java'),str(compiler),'user@192.168.219.146:'+remote+'/'],check=True)
s="Set-Location '"+rw+"';$cp=(Get-ChildItem '.\\lib\\*.jar').FullName -join ';'; & 'C:\\hira\\DDMD\\jre18\\bin\\java.exe' -jar .\\ecj-3.26.0.jar -1.8 -proc:none -classpath $cp -d .\\classes .\\HeadlessGateway.java .\\RecipientProbe.java;if($LASTEXITCODE -ne 0){throw 'compile failed'};'COMPILE PASS'"
print(ps(s))
# Global Java serialization limits; only credential/token DTOs and basic Java data are accepted.
fil='maxdepth=32;maxrefs=10000;maxbytes=1048576;maxarray=1048576;java.lang.*;java.util.*;java.security.cert.*;sun.security.x509.X509CertImpl;javax.crypto.spec.SecretKeySpec;hira.ddmd.jmc.agent.auth.*;hira.ddmd.jmc.common.dto.*;hira.ddmd.jmc.common.DdmdException;kr.co.bizframe.msi.*;!*'
# cmd.exe consumes stdin directly; no PowerShell stdin read ambiguity with secret pipes.
cmd='cd /d "'+rw+'" && "C:\\hira\\DDMD\\jre18\\bin\\java.exe" -Djava.awt.headless=true "-Djava.io.tmpdir='+rw+'\\javatmp" "-Djdk.serialFilter='+fil+'" -cp "classes;lib/*" HeadlessGateway'
state={'remote':remote,'command':cmd,'sourceSha256':hashlib.sha256((root/'gateway/HeadlessGateway.java').read_bytes()).hexdigest(),'recipientSha256':hashlib.sha256((root/'gateway/RecipientProbe.java').read_bytes()).hexdigest(),'preparedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'realAuthSent':False}
(root/'evidence/gateway-prepared.json').write_text(json.dumps(state,indent=2)+'\n')
print('READY: compiled; no authentication request sent')
