"""Read-only post-run environment and isolated-library verification."""
import base64,datetime,hashlib,json,pathlib,subprocess
root=pathlib.Path(__file__).resolve().parents[1]
state=json.loads((root/'evidence/live-prepared.json').read_text())
remote=state['remote'].replace('/','\\')
script=r"""$ErrorActionPreference='Stop';[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding;
$r='%REMOTE%';$results=@();
foreach($copy in Get-ChildItem ($r+'\lib\*.jar')) {
 $installed=@(Get-ChildItem 'C:\hira\DDMD\lib' -Recurse -File -Filter $copy.Name);
 if($installed.Count -ne 1){throw 'ambiguous library'}
 $a=(Get-FileHash -Algorithm SHA256 -LiteralPath $copy.FullName).Hash;
 $b=(Get-FileHash -Algorithm SHA256 -LiteralPath $installed[0].FullName).Hash;
 $results+=@{name=$copy.Name;sha256=$a;installedCopyMatch=($a -eq $b)};
}
$files=@(Get-ChildItem $r -Recurse -File);
@{sshSessionId=(Get-Process -Id $PID).SessionId;osVersion=[Environment]::OSVersion.Version.ToString();
 sourceSha256=(Get-FileHash -Algorithm SHA256 -LiteralPath ($r+'\LiveAuth.java')).Hash;
 libraries=$results;partFileCount=@(Get-ChildItem ($r+'\parts') -Recurse -File).Count;
 unexpectedFileCount=@($files|Where-Object {$_.Extension -notin '.jar','.class','.java'}).Count;
 ddmdJavawSessionIds=@(Get-Process javaw -ErrorAction SilentlyContinue|Select-Object -ExpandProperty SessionId)
}|ConvertTo-Json -Depth 5 -Compress
""".replace('%REMOTE%',remote)
cmd='powershell -NoProfile -EncodedCommand '+base64.b64encode(script.encode('utf-16le')).decode()
r=subprocess.run(['ssh','-o','BatchMode=yes','user@192.168.219.146',cmd],capture_output=True,text=True,errors='replace',timeout=60)
if r.returncode:raise RuntimeError('Remote verification failed; output suppressed')
data=json.loads(r.stdout)
assert data['sourceSha256'].lower()==state['sourceSha256']
assert data['sshSessionId']==0 and len(data['libraries'])==14 and all(x['installedCopyMatch'] for x in data['libraries'])
assert data['partFileCount']==0 and data['unexpectedFileCount']==0
data['verifiedAtUtc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
data['preparedCommandSha256']=hashlib.sha256(state['command'].encode()).hexdigest()
(root/'evidence/live-environment.json').write_text(json.dumps(data,indent=2)+'\n')
print('PASS: SSH Session 0; source hash matches; 14 installed libraries match; no payload files; DDMD javaw remains present='+str(bool(data['ddmdJavawSessionIds'])))
