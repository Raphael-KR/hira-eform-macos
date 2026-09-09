from pathlib import Path
import os,subprocess,shutil,json,hashlib,datetime,tempfile
root=Path(__file__).resolve().parents[1]
prefix=Path('/private/tmp/hira-wine-trial/prefix')
trial=Path(tempfile.mkdtemp(prefix='hira-headless-poc-wine-',dir=prefix/'drive_c'))
(trial/'classes').mkdir(exist_ok=True);(trial/'lib').mkdir(exist_ok=True)
libs=['ddmd-common-2.0.2.jar','ddmd-agent-1.0.4.jar','bizframe-commons-1.1.2-jdk5.jar','log4j-1.3alpha-9.jar','commons-io-2.0.1.jar','commons-codec-1.4.jar','jcaos-1.3.2.2.jar','bcprov-jdk15-146.jar','bcmail-jdk15-146.jar','ksign_ui-1.5.jar']
for name in libs:
 matches=list((prefix/'drive_c/hira/DDMD/lib').rglob(name));assert len(matches)==1
 shutil.copy2(matches[0],trial/'lib'/name)
shutil.copy2(root/'src/HeadlessAuthProbe.java',trial)
compiler=Path('/private/tmp/hira-ddmd-inspect/ecj-3.26.0.jar')
assert hashlib.sha1(compiler.read_bytes()).hexdigest()=='4837be609a3368a0f7e7cf0dc1bdbc7fe94993de'
shutil.copy2(compiler,trial)
subprocess.run(['node',str(root/'scripts/make-fixtures.mjs'),str(trial)],check=True)
env={**os.environ,'WINEPREFIX':str(prefix),'WINEDEBUG':'-all','MVK_CONFIG_LOG_LEVEL':'0'}
java=['/private/tmp/hira-wine-trial/Wine Stable.app/Contents/Resources/wine/bin/wine',r'C:\hira\DDMD\jre18\bin\java.exe','-Xint']
def run(args):
 r=subprocess.run(java+args,cwd=trial,env=env,capture_output=True,text=True,timeout=120)
 print(r.stdout);print(r.stderr);assert r.returncode==0
 return r.stdout+r.stderr
cp=';'.join('lib/'+name for name in libs)
run(['-jar','ecj-3.26.0.jar','-1.8','-proc:none','-classpath',cp,'-d','classes','HeadlessAuthProbe.java'])
out=run(['-Djava.awt.headless=true','-classpath','classes;'+cp,'HeadlessAuthProbe','C:/'+trial.name])
(root/'evidence/wine-offline-probe.txt').write_text(out)
r=subprocess.run(['node',str(root/'scripts/verify-java-envelope.mjs'),str(trial)],capture_output=True,text=True,check=True)
print(r.stdout);(root/'evidence/wine-node-interop.txt').write_text(r.stdout)
