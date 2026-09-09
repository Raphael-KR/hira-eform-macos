from pathlib import Path
import hashlib,json,sqlite3,zipfile
r=Path(__file__).resolve().parents[1];s=json.loads((r/'evidence/isolated-ui-prepared.json').read_text());p=Path(s['home']);src=Path(s['source']);out=p/'sam/out'
with zipfile.ZipFile(out/'ISOLATED-NOTICE-001/zip/ISOLATED-NOTICE-001') as z:
 entries=[x for x in z.infolist() if not x.is_dir()]
 generated=all((out/x.filename).read_bytes()==z.read(x) for x in entries)
 backup=all((out/'backup'/Path(x.filename).name).read_bytes()==z.read(x) for x in entries)
 monthly=all(any(f.read_bytes()==z.read(x) for f in (out/'SAMbackup').rglob('*') if f.is_file()) for x in entries)
for f in out.rglob('*'):
 if f.is_file():f.chmod(0o600)
c=sqlite3.connect('file:'+str(p/'data/ddmd_data.db3')+'?mode=ro',uri=True); integrity=c.execute('pragma integrity_check').fetchone()[0];state=c.execute('select NTC_STAT_CD from TBJFA103 where NTC_DOC_ID=?',('ISOLATED-NOTICE-001',)).fetchone()[0];c.close()
unchanged=all(hashlib.sha256(f.read_bytes()).digest()==hashlib.sha256((p/f.relative_to(src)).read_bytes()).digest() for f in (src/'lib').rglob('*.jar'))
log=(p/'gui-unlocked.log').read_text();flow=(r/'evidence/isolated-controller-original-loader.txt').read_text()
e={'vacuumDeniedPath':'/var/tmp','vacuumMemoryPragmaPassed':True,'jdbcUrlParameterWorked':False,'guiDatabaseMemoryAdapterLoaded':log.count('ISOLATED_JDBC_MEMORY_TEMP_READY'),'guiSqliteBusyObserved': 'SQLITE_BUSY' in log,'windowsCommandsStillFail':['launcher.exe','tasklist','reg'],'guiVisualVerified':False,'guiBlock':'CUA cannot select running Java app; bundle route failed after user unlocked Mac','settingsSavePassed':'SETTINGS_SAVE_PASS' in (r/'evidence/isolated-settings-save.txt').read_text(),'settingsNewJvmReloadPassed':'SETTINGS_RELOAD_PASS' in (r/'evidence/isolated-settings-reload.txt').read_text(),'originalControllerFlowPassed':'CONTROLLER_FLOW_PASS' in flow,'generatedFilesMatch':generated,'backupFilesMatch':backup,'monthlyBackupFilesMatch':monthly,'fileCount':len(entries),'dbState':state,'dbIntegrity':integrity,'originalDbUnchanged':hashlib.sha256((src/'data/ddmd_data.db3').read_bytes()).hexdigest()==s['originalDbSha256'],'originalLibraryCopiesUnmodified':unchanged,'serverConnectionUsed':False,'samClaimSent':False}
(r/'evidence/isolated-four-stage-result.json').write_text(json.dumps(e,indent=2)+'\n');print(json.dumps(e,indent=2))
