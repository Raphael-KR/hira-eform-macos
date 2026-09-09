from pathlib import Path
import json,subprocess,shutil,hashlib,sys
root=Path(__file__).resolve().parents[1];s=json.loads((root/'evidence/isolated-ui-prepared.json').read_text());p=Path(s['home']);src=Path(s['source']);s['originalDbSha256']=hashlib.sha256((src/'data/ddmd_data.db3').read_bytes()).hexdigest()
lib=p/'lib';names=['ddmd-client-1.0.0.jar','ddmd-common-2.0.2.jar','bizframe-commons-1.1.2-jdk5.jar','ibatis-2.3.0.677.jar','sqlite-jdbc-3.7.2.jar','spring-2.5.6.jar','commons-logging-1.1.1.jar','log4j-1.3alpha-9.jar']
cp=':'.join(str(next(lib.rglob(n))) for n in names);j=Path('/private/tmp/hira-jvm-trial/zulu8.96.0.205-ca-jdk8.0.504-macosx_aarch64/Contents/Home/bin')
subprocess.run([str(j/'javac'),'-cp',cp,'-d',str(p/'probe'),str(root/'isolated-ui/DbProbe.java')],check=True)
r=subprocess.run([str(j/'java'),'-Dlog4j.defaultInitOverride=true','-Djava.awt.headless=true','-Djava.io.tmpdir='+str(p/'javatmp'),'-cp',str(p/'probe')+':'+cp,'DbProbe',str(p)],cwd=p,capture_output=True,text=True,timeout=30)
(root/'evidence/isolated-db.txt').write_text(r.stdout+r.stderr);print(r.stdout);print(r.stderr[-1600:]);assert r.returncode==0
z=p/'sam/out/ISOLATED-NOTICE-001/zip';z.mkdir(parents=True,exist_ok=True);shutil.copy2(root/'private-downloads/notice-xcDjRX/decrypted-notice.zip',z/'ISOLATED-NOTICE-001')
(root/'evidence/isolated-ui-prepared.json').write_text(json.dumps(s,indent=2)+'\n')
bcp=str(p/'data/bootstrap.jar');subprocess.run([str(j/'javac'),'-cp',bcp,'-d',str(p/'probe'),str(root/'isolated-ui/GuiBootstrap.java')],check=True)
cmd=[str(j/'java'),'-Dclient.home='+str(p),'-Djava.io.tmpdir='+str(p/'javatmp'),'-Duser.home='+str(p),'-Dupdate=false','-Dlog4j.defaultInitOverride=true','-cp',str(p/'probe')+':'+bcp,'GuiBootstrap']
(p/'gui-command.json').write_text(json.dumps(cmd))
print('GUI_READY')
