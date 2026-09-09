// Fixed authentication-only macOS JVM trial. Never persists identity or response payloads.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {spawn,spawnSync} from 'node:child_process';
import {loadIdentity} from '../live/identity.mjs';
if(process.argv.length!==2){console.error('AUTH_ONLY_NO_ARGUMENTS');process.exit(2);}
let setupStage="prepared";
try {
 const state=JSON.parse(fs.readFileSync(new URL('./prepared.json',import.meta.url)));
 const hash=crypto.createHash('sha256').update(fs.readFileSync(new URL('../macos-jvm/HeadlessGateway.java',import.meta.url))).digest('hex');
 if(hash!==state.sourceSha256||state.args.at(-1)!=='update')throw Error('prepared mismatch');
 for(const [name,hash] of Object.entries(state.libraries))if(crypto.createHash('sha256').update(fs.readFileSync(state.cwd+'/lib/'+name)).digest('hex')!==hash)throw Error('library mismatch');
 const script="$ErrorActionPreference='Stop'; $line=Get-Content -LiteralPath 'C:\\hira\\DDMD\\conf\\ddmd.properties' | Where-Object {$_ -match '^ykiho[ ]*='} | Select-Object -First 1; if(!$line){exit 2}; [Console]::Write(($line.Split('=',2)[1]).Trim())";
 setupStage="institution-read";
 const q=spawnSync('ssh',['-o','BatchMode=yes','-o','ConnectTimeout=10','user@192.168.219.146','powershell -NoProfile -EncodedCommand '+Buffer.from(script,'utf16le').toString('base64')],{encoding:'utf8',timeout:20000,maxBuffer:4096});
 if(q.status!==0||!/^\d{8}$/.test(q.stdout)){console.log(JSON.stringify({sshStatus:q.status,stdoutBytes:q.stdout?.length??0,stderrBytes:q.stderr?.length??0}));throw Error('institution unavailable');}
 setupStage="identity-read";
 const i=loadIdentity();const attr=i.values.find(v=>v.oid==='1.2.410.200004.10.1.1.3');const bits=attr?.node?.value?.[0];const data=bits?.bitStringContents??bits?.value;
 if(bits?.type!==3||typeof data!=='string'||data.length!==21||data.charCodeAt(0)!==0)throw Error('VID invalid');
 const random=Buffer.from(data.slice(1),'binary');
 const input=Buffer.from(q.stdout+'\n'+Buffer.from(i.certDer,'binary').toString('base64')+'\n'+random.toString('base64')+'\n');random.fill(0);
 setupStage="jvm-spawn";
 const startedAtUtc=new Date().toISOString();
 const child=spawn(state.java,state.args,{cwd:state.cwd,env:process.env,stdio:['pipe','pipe','pipe']});
 let stdout='',stderrBytes=0;
 child.stdout.on('data',b=>{if(stdout.length+b.length>65536)child.kill();else stdout+=b.toString('utf8');});child.stderr.on('data',b=>stderrBytes+=b.length);
 child.stdin.on('error',()=>{});child.stdin.end(input,()=>input.fill(0));
 const timer=setTimeout(()=>child.kill(),90000);
 const code=await new Promise((resolve,reject)=>{child.on('error',reject);child.on('close',resolve);});clearTimeout(timer);
 const lines=stdout.split(/\r?\n/).filter(s=>/^(RESULT|EVENT|CHECK) [A-Za-z0-9= ._-]+$/.test(s)||/^ERROR_CLASS [A-Za-z0-9_.$]+$/.test(s)||/^DDMD_CODE -?[0-9]+$/.test(s)||/^FRAME [A-Za-z0-9_.$<>]+:-?[0-9]+$/.test(s)||/^RESPONSE_CLASS [A-Za-z0-9_.$;\[\]]+$/.test(s));
 const passed=code===0&&lines.includes('RESULT GATEWAY_PASS mode=update headless=true requests=2');
 const report={startedAtUtc,finishedAtUtc:new Date().toISOString(),sourceSha256:hash,runtime:'macOS ARM64 Zulu Java 8u504 native JVM',exitCode:code,passed,stderrBytes,lines};
 fs.writeFileSync(new URL('../evidence/macos-update-postcheck-result.json',import.meta.url),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));if(!passed)process.exitCode=1;
}catch{console.error('MACOS_AUTH_SETUP_FAILED stage='+setupStage);process.exitCode=1;}
