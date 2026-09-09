from pathlib import Path
import ast,os,shutil,subprocess,json,hashlib,tempfile
root=Path(__file__).resolve().parents[1];prefix=Path('/private/tmp/hira-wine-trial/prefix')
trial=Path(tempfile.mkdtemp(prefix='hira-live-auth-wine-',dir='/private/tmp/hira-jvm-trial'))
for n in ['classes','lib','parts','javatmp']:(trial/n).mkdir()
tree=ast.parse((root/'gateway/prepare.py').read_text())
libs=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='libs' for t in n.targets))
hashes={}
for lib in libs:
 src=prefix/'drive_c/hira/DDMD'/lib;dst=trial/'lib'/src.name;shutil.copy2(src,dst);hashes[src.name]=hashlib.sha256(dst.read_bytes()).hexdigest()
src=root/'macos-jvm/HeadlessGateway.java';shutil.copy2(src,trial);shutil.copy2(root/'macos-jvm/RecipientProbe.java',trial);shutil.copy2(root/'macos-jvm/NoticeListProbe.java',trial);shutil.copy2(root/'macos-jvm/DownloadProbe.java',trial)
compiler=Path('/private/tmp/hira-ddmd-inspect/ecj-3.26.0.jar');assert hashlib.sha1(compiler.read_bytes()).hexdigest()=='4837be609a3368a0f7e7cf0dc1bdbc7fe94993de';shutil.copy2(compiler,trial)
env={**os.environ,'WINEPREFIX':str(prefix),'WINEDEBUG':'-all','MVK_CONFIG_LOG_LEVEL':'0','WINEDLLOVERRIDES':'mscoree,mshtml='}
exe='/private/tmp/hira-jvm-trial/zulu8.96.0.205-ca-jdk8.0.504-macosx_aarch64/Contents/Home/bin/java'
args=['-XX:ErrorFile=/dev/null','-Djava.awt.headless=true']
cp=':'.join('lib/'+Path(lib).name for lib in libs)
r=subprocess.run([exe]+args+['-jar','ecj-3.26.0.jar','-1.8','-proc:none','-classpath',cp,'-d','classes','HeadlessGateway.java','RecipientProbe.java','NoticeListProbe.java','DownloadProbe.java'],cwd=trial,env=env,capture_output=True,text=True,timeout=120)
if r.returncode:print(r.stdout+r.stderr);raise SystemExit(r.returncode)
fil='maxdepth=32;maxrefs=10000;maxbytes=1048576;maxarray=1048576;java.lang.*;java.util.*;java.security.cert.*;sun.security.x509.X509CertImpl;javax.crypto.spec.SecretKeySpec;hira.ddmd.jmc.agent.auth.*;hira.ddmd.jmc.common.dto.*;hira.ddmd.jmc.common.DdmdException;kr.co.bizframe.msi.*;!*'
args+=['-Djava.io.tmpdir='+str(trial/'javatmp'),'-Djdk.serialFilter='+fil,'-cp','classes:'+cp,'HeadlessGateway','auth']
shutil.copy2(prefix/'drive_c/hira/DDMD/data/kmCert.der',trial/'kmCert.der')
(trial/'ddmd.properties').write_text('msi.endpoint=http://ddmd.hira.or.kr/imxs/msi\n')
state={'cwd':str(trial),'java':exe,'prefix':str(prefix),'args':args,'sourceSha256':hashlib.sha256(src.read_bytes()).hexdigest(),'downloadSha256':hashlib.sha256((root/'macos-jvm/DownloadProbe.java').read_bytes()).hexdigest(),'noticeSha256':hashlib.sha256((root/'macos-jvm/NoticeListProbe.java').read_bytes()).hexdigest(),'recipientSha256':hashlib.sha256((root/'macos-jvm/RecipientProbe.java').read_bytes()).hexdigest(),'libraries':hashes}
(root/'evidence/macos-live-prepared.json').write_text(json.dumps(state,indent=2)+'\n')
print('COMPILE PASS; auth-only runtime prepared; no authentication sent')
