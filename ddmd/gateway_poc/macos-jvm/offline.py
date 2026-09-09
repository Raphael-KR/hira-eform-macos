from pathlib import Path
import os,subprocess,shutil,json,hashlib,datetime,tempfile
root=Path(__file__).resolve().parents[1]
source=Path(os.environ.get('DDMD_SOURCE_DIR',''))
if not os.environ.get('DDMD_SOURCE_DIR') or not source.is_absolute() or not (source/'lib').is_dir() or not (source/'data/kmCert.der').is_file():
 raise SystemExit('Set DDMD_SOURCE_DIR to an absolute DDMD installation directory containing lib/ and data/kmCert.der')
trial=Path(tempfile.mkdtemp(prefix='hira-headless-poc-macos-',dir='/private/tmp/hira-jvm-trial'))
(trial/'classes').mkdir(exist_ok=True);(trial/'lib').mkdir(exist_ok=True)
libs=['ddmd-common-2.0.2.jar','ddmd-agent-1.0.4.jar','bizframe-commons-1.1.2-jdk5.jar','log4j-1.3alpha-9.jar','commons-io-2.0.1.jar','commons-codec-1.4.jar','jcaos-1.3.2.2.jar','bcprov-jdk15-146.jar','bcmail-jdk15-146.jar','ksign_ui-1.5.jar']
for name in libs:
 matches=list((source/'lib').rglob(name));assert len(matches)==1
 shutil.copy2(matches[0],trial/'lib'/name)
shutil.copy2(root/'macos-jvm/HeadlessAuthProbe.java',trial)
compiler=Path('/private/tmp/hira-ddmd-inspect/ecj-3.26.0.jar')
assert hashlib.sha1(compiler.read_bytes()).hexdigest()=='4837be609a3368a0f7e7cf0dc1bdbc7fe94993de'
shutil.copy2(compiler,trial)
subprocess.run(['node',str(root/'scripts/make-fixtures.mjs'),str(trial)],check=True)
env=os.environ.copy()
java=['/private/tmp/hira-jvm-trial/zulu8.96.0.205-ca-jdk8.0.504-macosx_aarch64/Contents/Home/bin/java']
def run(args):
 r=subprocess.run(java+args,cwd=trial,env=env,capture_output=True,text=True,timeout=120)
 print(r.stdout);print(r.stderr);assert r.returncode==0
 return r.stdout+r.stderr
cp=':'.join('lib/'+name for name in libs)
run(['-jar','ecj-3.26.0.jar','-1.8','-proc:none','-classpath',cp,'-d','classes','HeadlessAuthProbe.java'])
out=run(['-Djava.awt.headless=true','-classpath','classes:'+cp,'HeadlessAuthProbe',str(trial)])
(root/'evidence/macos-offline-probe.txt').write_text(out)
r=subprocess.run(['node',str(root/'scripts/verify-java-envelope.mjs'),str(trial)],capture_output=True,text=True,check=True)
print(r.stdout);(root/'evidence/macos-node-interop.txt').write_text(r.stdout)

print("SYNTHETIC_FIXTURE_DIR",trial)

for name in ['file-signed.cms','message-signed.cms']:
 result=subprocess.run(['openssl','cms','-verify','-binary','-inform','DER','-in',str(trial/name),'-CAfile',str(trial/'cert.pem'),'-purpose','any','-out',str(trial/(name+'.verified'))],capture_output=True,text=True)
 print('OPENSSL',name,'PASS' if result.returncode==0 else 'FAIL')
 assert result.returncode==0
 if name=='file-signed.cms':assert (trial/(name+'.verified')).read_bytes()==(trial/'file-original.bin').read_bytes()
(root/'evidence/macos-file-crypto.json').write_text(json.dumps({'syntheticOnly':True,'fileCmsOpenSslVerified':True,'messageCmsOpenSslVerified':True,'fixture':str(trial),'originalMessageVerifierPassed':False},indent=2)+'\n')
