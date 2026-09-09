from pathlib import Path
import json,subprocess,shutil
p=Path('/private/tmp/hira-ddmd-ui-wtk92jjq');r=Path(__file__).resolve().parents[1];j=Path(json.loads((p/'gui-command.json').read_text())[0]).parent;b=p/'loader-probe';b.mkdir(exist_ok=True)
for n in ['GuiBootstrap.class','GuiBootstrap$Guard.class']:shutil.copy2(p/'probe'/n,b/n)
# Flow is loaded by the original application class loader, not the bootstrap parent.
import zipfile
with zipfile.ZipFile(p/'lib/isolated-flow-trial.jar','w') as z:
 for n in ['FlowProbe.class','FlowProbe$1.class']:
  z.write(p/'probe'/n,n)
  f=p/'resources'/n
  if f.exists():f.rename(p/(n+'.unused'))

cp=str(b)+':'+str(p/'data/bootstrap.jar');subprocess.run([str(j/'javac'),'-cp',cp,'-d',str(b),str(r/'isolated-ui/LoaderProbe.java')],check=True)
a=subprocess.run([str(j/'java'),'-Djava.awt.headless=true','-Djava.io.tmpdir='+str(p/'javatmp'),'-cp',cp,'LoaderProbe',str(p)],cwd=p,capture_output=True,text=True,timeout=30)
(r/'evidence/isolated-controller-original-loader.txt').write_text(a.stdout+a.stderr);print(a.returncode,'\n'.join(x for x in (a.stdout+a.stderr).splitlines() if any(t in x for t in ['CONTROLLER_','CAUSE=','Exception','FlowProbe']))[-2000:])
