from pathlib import Path
import subprocess,json
p=Path('/private/tmp/hira-ddmd-ui-wtk92jjq');r=Path(__file__).resolve().parents[1];j=Path(json.loads((p/'gui-command.json').read_text())[0]).parent
cp=str(p/'conf')+':'+str(p/'probe')+':'+':'.join(str(x) for x in (p/'lib').rglob('*.jar'))
subprocess.run([str(j/'javac'),'-cp',cp,'-d',str(p/'probe'),str(r/'isolated-ui/SettingsProbe.java')],check=True)
for mode in ['save','reload']:
 a=subprocess.run([str(j/'java'),'-Djava.awt.headless=true','-Djava.io.tmpdir='+str(p/'javatmp'),'-cp',cp,'SettingsProbe',str(p),mode],cwd=p,capture_output=True,text=True,timeout=25)
 (r/('evidence/isolated-settings-'+mode+'.txt')).write_text(a.stdout+a.stderr)
 print(mode,a.returncode,'\n'.join(x for x in (a.stdout+a.stderr).splitlines() if 'PASS' in x or 'Exception' in x)[-1200:])
