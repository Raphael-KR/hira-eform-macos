from pathlib import Path
import ast,os,shutil,subprocess,json,hashlib,tempfile
root=Path(__file__).resolve().parents[1];prefix=Path('/private/tmp/hira-wine-trial/prefix')
trial=Path(tempfile.mkdtemp(prefix='hira-live-auth-wine-',dir=prefix/'drive_c'))
for n in ['classes','lib','parts','javatmp']:(trial/n).mkdir()
tree=ast.parse((root/'gateway/prepare.py').read_text())
libs=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='libs' for t in n.targets))
hashes={}
for lib in libs:
 src=prefix/'drive_c/hira/DDMD'/lib;dst=trial/'lib'/src.name;shutil.copy2(src,dst);hashes[src.name]=hashlib.sha256(dst.read_bytes()).hexdigest()
src=root/'wine/HeadlessGateway.java';shutil.copy2(src,trial)
compiler=Path('/private/tmp/hira-ddmd-inspect/ecj-3.26.0.jar');assert hashlib.sha1(compiler.read_bytes()).hexdigest()=='4837be609a3368a0f7e7cf0dc1bdbc7fe94993de';shutil.copy2(compiler,trial)
env={**os.environ,'WINEPREFIX':str(prefix),'WINEDEBUG':'-all','MVK_CONFIG_LOG_LEVEL':'0','WINEDLLOVERRIDES':'mscoree,mshtml='}
exe='/private/tmp/hira-wine-trial/Wine Stable.app/Contents/Resources/wine/bin/wine'
args=[r'C:\hira\DDMD\jre18\bin\java.exe','-Xint','-XX:ErrorFile=NUL','-Djava.awt.headless=true']
cp=';'.join('lib/'+Path(lib).name for lib in libs)
r=subprocess.run([exe]+args+['-jar','ecj-3.26.0.jar','-1.8','-proc:none','-classpath',cp,'-d','classes','HeadlessGateway.java'],cwd=trial,env=env,capture_output=True,text=True,timeout=120)
if r.returncode:print(r.stdout+r.stderr);raise SystemExit(r.returncode)
fil='maxdepth=32;maxrefs=10000;maxbytes=1048576;maxarray=1048576;java.lang.*;java.util.*;java.security.cert.*;sun.security.x509.X509CertImpl;javax.crypto.spec.SecretKeySpec;hira.ddmd.jmc.agent.auth.*;hira.ddmd.jmc.common.dto.*;hira.ddmd.jmc.common.DdmdException;kr.co.bizframe.msi.*;!*'
args+=['-Djava.io.tmpdir=C:/'+trial.name+'/javatmp','-Djdk.serialFilter='+fil,'-cp','classes;'+cp,'HeadlessGateway','auth']
state={'cwd':str(trial),'wine':exe,'prefix':str(prefix),'args':args,'sourceSha256':hashlib.sha256(src.read_bytes()).hexdigest(),'libraries':hashes}
(root/'evidence/wine-live-prepared.json').write_text(json.dumps(state,indent=2)+'\n')
print('COMPILE PASS; auth-only runtime prepared; no authentication sent')
