#!/usr/bin/env python3
"""Isolated macOS DDMD update launcher; no SAM actions or OS service registration."""
import argparse, ast, datetime, fcntl, hashlib, json, os, re, shutil, signal
import sqlite3, subprocess, sys, tempfile, time, xml.etree.ElementTree as ET, zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
POC=HERE.parent
NS={'d':'http://www.hira.or.kr/ddmd'}
SERIAL='maxdepth=32;maxrefs=10000;maxbytes=268435456;maxarray=1048576;java.lang.*;java.util.*;java.security.cert.*;sun.security.x509.X509CertImpl;javax.crypto.spec.SecretKeySpec;hira.ddmd.jmc.agent.auth.*;hira.ddmd.jmc.common.dto.*;hira.ddmd.jmc.common.DdmdException;kr.co.bizframe.msi.*;kr.co.bizframe.msi.registry.AttachmentReference;!*'

def atomic_json(path,data):
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(data,indent=2)+'\n');os.chmod(temporary,0o600);os.replace(temporary,path)
def digest(path):return format(int(hashlib.sha256(path.read_bytes()).hexdigest(),16),'x')
def contained(root,relative):
    p=(root/relative).resolve()
    if not p.is_relative_to(root.resolve()):raise ValueError('path escapes trial')
    return p

def modules(home,output):
    rows=[]
    for m in ET.parse(home/'update/release.xml').findall('.//d:module',NS):
        loc=m.findtext('d:location',namespaces=NS);p=contained(home,loc)
        fields=[m.get('id'),m.get('type'),m.get('revision'),m.get('date',''),loc,digest(p) if p.is_file() else '']
        if any('\t' in f or '\n' in f for f in fields):raise ValueError('invalid manifest')
        rows.append('\t'.join(fields))
    output.write_text('\n'.join(rows)+'\n')

def checked(cmd,cwd=None,log=None,timeout=120):
    result=subprocess.run([str(x) for x in cmd],cwd=cwd,capture_output=True,timeout=timeout)
    if log:log.write_bytes(result.stdout+result.stderr)
    if result.returncode:raise RuntimeError('command failed: '+str(cmd[0])+' exit='+str(result.returncode))
    return result

def prepare_transport(work,source,java,institution):
    for n in ['lib','classes','parts','javatmp']:(work/n).mkdir()
    tree=ast.parse((POC/'gateway/prepare.py').read_text())
    libs=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='libs' for t in n.targets))
    hashes={}
    for name in libs:
        p=source/name;dst=work/'lib'/p.name;shutil.copy2(p,dst);hashes[p.name]=hashlib.sha256(dst.read_bytes()).hexdigest()
    shutil.copy2(source/'data/kmCert.der',work/'kmCert.der')
    (work/'ddmd.properties').write_text('msi.endpoint=http://ddmd.hira.or.kr/imxs/msi\n')
    cp='classes:'+':'.join('lib/'+n for n in hashes)
    checked([java.with_name('javac'),'-XDignore.symbol.file','-cp',cp,'-d','classes',POC/'macos-jvm/HeadlessGateway.java',HERE/'AutoUpdateTransport.java'],work,work/'compile.log')
    return {'cwd':str(work),'java':str(java),'institutionFile':str(institution),'libraries':hashes,'sourceSha256':hashlib.sha256((POC/'macos-jvm/HeadlessGateway.java').read_bytes()).hexdigest(),'args':['-Djava.awt.headless=true','-Djava.io.tmpdir='+str(work/'javatmp'),'-Dhira.update.serialFilter='+SERIAL,'-cp',cp,'AutoUpdateTransport','query']}

def transport(work,state,mode,name):
    state=dict(state);state['args']=list(state['args']);state['args'][-1]=mode;state['reportFile']=str(work/(name+'.json'))
    atomic_json(work/'transport.json',state)
    checked(['node',HERE/'transport.mjs',work/'transport.json'],log=work/(name+'.safe.log'),timeout=270)
    report=json.loads(Path(state['reportFile']).read_text())
    if not report['passed']:raise RuntimeError('transport failed')
    return report

def payloads(work):
    rows=[]
    for line in (work/'response.tsv').read_text().splitlines():
        f=line.split('\t')
        if len(f)!=8 or not re.fullmatch(r'[A-Za-z0-9_.-]+',f[0]) or f[0] in ('.','..'):raise ValueError('invalid module metadata')
        if int(f[1])<=0:raise ValueError('module deletion requires separate validation')
        if not re.fullmatch(r'[A-Za-z0-9_.-]+',f[4]) or f[4] in ('.','..'):raise ValueError('invalid payload name')
        p=Path(f[5]).resolve()
        if not p.is_relative_to((work/'parts').resolve()) or not p.is_file():raise ValueError('invalid attachment path')
        if not re.fullmatch('[0-9a-fA-F]{1,64}',f[3]) or int(digest(p),16)!=int(f[3],16):raise ValueError('payload checksum mismatch')
        rows.append(f)
    return rows

def stage(candidate,rows):
    root=ET.Element('ddmd-client',xmlns='http://www.hira.or.kr/ddmd');ms=ET.SubElement(root,'modules')
    for f in rows:
        location=f[2].rstrip('/')+'/'+f[4];contained(candidate,location)
        dest=contained(candidate,'update/downloads/'+f[0]+'/'+f[4]);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f[5],dest)
        m=ET.SubElement(ms,'module',id=f[0],type=f[6],revision=f[1],date=f[7] or datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        ET.SubElement(m,'location').text=location;ET.SubElement(m,'checksum').text=f[3]
    ET.ElementTree(root).write(candidate/'update/downloads/release.xml',encoding='utf-8',xml_declaration=True)

def configure(candidate,previous):
    # Preserve settings, remap only machine-local paths, and build our own JDBC adapter.
    path=candidate/'conf/ddmd.properties'
    content=path.read_bytes().decode('latin1').replace(str(previous),str(candidate))
    replacements={'compatibility.dmd.dir':str(candidate/'sam/in'),
                  'compatibility.ntc.dir':str(candidate/'sam/out'),
                  'driver.class.name':'IsolatedJdbc',
                  'url':'jdbc:isolated-sqlite:'+str(candidate/'data/ddmd_data.db3')}
    for key,value in replacements.items():
        pattern=r'(?m)^'+re.escape(key)+r'\s*=.*$'
        line=key+'='+value
        content=re.sub(pattern,lambda m:line,content) if re.search(pattern,content) else content+'\n'+line+'\n'
    path.write_bytes(content.encode('latin1'))
    (candidate/'conf/SqlMapConfig.properties').write_text('url_tbjcc010 = jdbc:sqlite:'+str(candidate/'data/tbjcc010.db')+'\nhome = '+str(candidate)+'\n')
    for n in ['probe','javatmp']:(candidate/n).mkdir(exist_ok=True)


def apply(candidate,java,work):
    sqlite_jars=list((candidate/'lib').rglob('*sqlite*.jar'))
    if len(sqlite_jars)!=1:raise RuntimeError('SQLite library selection is ambiguous')
    checked([java.with_name('javac'),'-cp',sqlite_jars[0],'-d',candidate/'probe',POC/'isolated-ui/IsolatedJdbc.java'],log=work/'jdbc-compile.log')
    with zipfile.ZipFile(candidate/'lib/shared/isolated-jdbc-trial.jar','w') as z:z.write(candidate/'probe/IsolatedJdbc.class','IsolatedJdbc.class')
    (candidate/'probe/IsolatedJdbc.class').unlink()
    cp=':'.join(str(p) for p in (candidate/'lib').rglob('*.jar'))+':'+str(candidate/'data/bootstrap.jar')
    checked([java.with_name('javac'),'-cp',cp,'-d',candidate/'probe',POC/'update/ApplyUpdateProbe.java',POC/'isolated-ui/GuiBootstrap.java'],log=work/'apply-compile.log')
    checked([java.with_name('javac'),'-cp',str(candidate/'probe')+':'+str(candidate/'data/bootstrap.jar'),'-d',candidate/'probe',POC/'update/UpdateLoader.java'],log=work/'loader-compile.log')
    with zipfile.ZipFile(candidate/'lib/isolated-update-probe.jar','w') as z:z.write(candidate/'probe/ApplyUpdateProbe.class','ApplyUpdateProbe.class')
    (candidate/'probe/ApplyUpdateProbe.class').unlink()
    checked([java,'-Djava.io.tmpdir='+str(candidate/'javatmp'),'-Duser.home='+str(candidate),'-cp',str(candidate/'probe')+':'+str(candidate/'data/bootstrap.jar'),'UpdateLoader',candidate],candidate,work/'apply.log',180)
    if 'UPDATE_APPLY_RETURNED' not in (work/'apply.log').read_text(errors='replace'):raise RuntimeError('apply did not finish')
    pending=candidate/'update/updated.dat'
    if not pending.is_file():raise RuntimeError('update receipt missing')
    shutil.move(pending,work/'pending.dat') # Keep it out of original startup's delete-before-send path.

def verify(candidate,rows):
    installed={m.get('id'):m for m in ET.parse(candidate/'update/release.xml').findall('.//d:module',NS)};results=[]
    for f in rows:
        m=installed[f[0]];p=contained(candidate,m.findtext('d:location',namespaces=NS))
        if m.get('revision')!=f[1] or int(digest(p),16)!=int(m.findtext('d:checksum',namespaces=NS),16):raise ValueError('applied module mismatch')
        result={'id':f[0],'revision':f[1],'digest':digest(p)}
        if p.suffix=='.db':
            with sqlite3.connect('file:'+str(p)+'?mode=ro',uri=True) as db:result['sqlite']=db.execute('pragma quick_check').fetchone()[0]
            if result['sqlite']!='ok':raise ValueError('invalid SQLite module')
        results.append(result)
    return results

def launch(candidate,java,work,bundle):
    args=[str(java),'-Dclient.home='+str(candidate),'-Djava.io.tmpdir='+str(candidate/'javatmp'),'-Duser.home='+str(candidate),'-Dupdate=false','-Dlog4j.defaultInitOverride=true','-cp',str(candidate/'probe')+':'+str(candidate/'data/bootstrap.jar'),'GuiBootstrap']
    (candidate/'gui-command.json').write_text(json.dumps(args))
    checked([sys.executable,POC/'isolated-ui/app-launcher/build.py','--home',candidate,'--bundle-id',bundle],log=work/'build.log')
    checked(['open','-n',candidate/'DDMD Computer Use.app'])
    deadline=time.monotonic()+60
    while time.monotonic()<deadline:
        log=candidate/'gui-app-bundle.log'
        if log.exists():
            text=log.read_text(errors='replace')
            if 'Application started' in text:
                if 'HashMap cannot be cast' in text:raise RuntimeError('JIDE startup regression')
                return
        time.sleep(.5)
    raise RuntimeError('candidate startup timeout')

def stop_owned(home):
    pidfile=home/'native-app.pid'
    if not pidfile.exists():return False
    pid=int(pidfile.read_text().strip())
    process=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True)
    expected=str(home/'DDMD Computer Use.app/Contents/MacOS/DDMDTrial')
    if process.returncode:return False
    if process.stdout.strip()!=expected:raise RuntimeError('PID identity mismatch')
    os.kill(pid,signal.SIGTERM)
    for _ in range(40):
        try:os.kill(pid,0)
        except ProcessLookupError:return True
        time.sleep(.25)
    raise RuntimeError('owned app did not terminate')

def run(opts):
    root=opts.root.resolve();root.mkdir(parents=True,exist_ok=True);os.chmod(root,0o700)
    with (root/'update.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        # Never retransmit an ambiguous result report or launch duplicate update runs.
        if list(root.glob('hira-live-auth-*/pending.dat')):raise RuntimeError('pending result report requires reconciliation; not resent automatically')
        active=root/'active.json'
        current=Path(json.loads(active.read_text())['home']) if active.exists() else opts.source.resolve()
        work=Path(tempfile.mkdtemp(prefix='hira-live-auth-',dir=root));os.chmod(work,0o700)
        status={'phase':'prepare','previous':str(current),'work':str(work)};atomic_json(work/'status.json',status)
        candidate=None;stopped=False;published=False
        try:
            state=prepare_transport(work,current,opts.java.resolve(),opts.institution.resolve())
            modules(current,work/'modules.tsv')
            status['phase']='query';atomic_json(work/'status.json',status);transport(work,state,'query','query')
            if not (work/'response.tsv').read_text().strip():
                status.update(phase='up_to_date',changed=False);atomic_json(work/'status.json',status);print(json.dumps(status));return
            status['phase']='download';atomic_json(work/'status.json',status);transport(work,state,'download','download');rows=payloads(work)
            if not rows:raise RuntimeError('update changed between query and download; rerun')
            if active.exists():stopped=stop_owned(current)
            # Stop our own active JVM before copying its SQLite files.
            candidate=work/'candidate';shutil.copytree(current,candidate,ignore=shutil.ignore_patterns('DDMD Computer Use.app','gui-app-bundle.log','*.pid'))
            configure(candidate,current);stage(candidate,rows)
            status['phase']='apply';atomic_json(work/'status.json',status);apply(candidate,opts.java.resolve(),work)
            verified=verify(candidate,rows);atomic_json(work/'verified.json',verified)
            status['phase']='launch';atomic_json(work/'status.json',status)
            bundle='local.hira.ddmd.auto.'+work.name.rsplit('-',1)[-1]
            launch(candidate,opts.java.resolve(),work,bundle)
            # Candidate is healthy. Publish the pointer, retaining the previous version.
            atomic_json(active,{'home':str(candidate),'previous':str(current),'bundleId':bundle,'work':str(work)})
            published=True
            status.update(phase='report',candidate=str(candidate),bundleId=bundle);atomic_json(work/'status.json',status)
            transport(work,state,'report','report')
            (work/'pending.dat').rename(work/'acknowledged.dat')
            modules(candidate,work/'modules.tsv');transport(work,state,'query','postcheck')
            if (work/'response.tsv').read_text().strip():raise RuntimeError('additional updates remain')
            status.update(phase='complete',changed=True,modules=len(rows),acknowledged=True,postcheckModules=0);atomic_json(work/'status.json',status);print(json.dumps(status))
        except Exception as error:
            if not published:
                if candidate is not None:stop_owned(candidate)
                if stopped:checked(['open','-n',current/'DDMD Computer Use.app'])
            status.update(failed=True,error=type(error).__name__+': '+str(error));atomic_json(work/'status.json',status)
            print(json.dumps(status));raise

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--source',type=Path,required=True)
    p.add_argument('--institution',type=Path,required=True);p.add_argument('--java',type=Path,required=True)
    try:run(p.parse_args())
    except Exception as e:print('AUTO_UPDATE_FAILED '+type(e).__name__,file=sys.stderr);sys.exit(1)
