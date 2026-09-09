// Owner-authorized fixed gateway commands. Secrets travel only through SSH stdin.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {spawn} from 'node:child_process';
import {loadIdentity} from '../live/identity.mjs';
const evidence=new URL('../evidence/',import.meta.url);
const mode=process.argv[2];
if(!['auth','lifecycle','failure-tests','recipient'].includes(mode)){console.error('INVALID_COMMAND: auth, lifecycle, failure-tests, recipient only');process.exit(2);}
try {
 const state=JSON.parse(fs.readFileSync(new URL('gateway-prepared.json',evidence),'utf8'));
 const hash=crypto.createHash('sha256').update(fs.readFileSync(new URL('./HeadlessGateway.java',import.meta.url))).digest('hex');
 if(hash!==state.sourceSha256)throw Error('Source changed');
 const identity=loadIdentity();
 const attr=identity.values.find(v=>v.oid==='1.2.410.200004.10.1.1.3');
 const bits=attr?.node?.value?.[0];
 // node-forge retains BIT STRING bytes in bitStringContents, even when it decodes a child.
 const contents=bits?.bitStringContents ?? bits?.value;
 if(bits?.type!==3||typeof contents!=='string'||contents.length!==21||contents.charCodeAt(0)!==0)throw Error('VID encoding mismatch');
 const random=Buffer.from(contents.slice(1),'binary');
 const input=Buffer.from(Buffer.from(identity.certDer,'binary').toString('base64')+'\n'+random.toString('base64')+'\n');
 random.fill(0);
 const startedAtUtc=new Date().toISOString();
 const preflight=false; if(mode==='recipient' && crypto.createHash('sha256').update(fs.readFileSync(new URL('./RecipientProbe.java',import.meta.url))).digest('hex')!==state.recipientSha256)throw Error('query source changed');
 const child=spawn('ssh',['-o','BatchMode=yes','-o','ConnectTimeout=10','user@192.168.219.146',(mode==='recipient'?state.command.replace(/HeadlessGateway$/,'RecipientProbe'):state.command)+' '+mode],{stdio:['pipe','pipe','pipe']});
 let stdout='',stderrBytes=0;
 child.stdout.on('data',b=>{if(stdout.length+b.length>65536)child.kill();else {stdout+=b.toString('utf8'); for(const line of b.toString('utf8').split(/\r?\n/))if(/^(EVENT|CHECK|RESULT) [A-Za-z0-9= ._-]+$/.test(line))console.log(line);}});
 child.stderr.on('data',b=>{stderrBytes+=b.length;});
 child.stdin.on('error',()=>{});
 child.stdin.end(input,()=>input.fill(0));
 const timer=setTimeout(()=>child.kill(),480000);
 const code=await new Promise((resolve,reject)=>{child.on('error',reject);child.on('close',resolve);});
 clearTimeout(timer);
 const lines=stdout.split(/\r?\n/).filter(s=>/^(?:RESULT|EVENT|CHECK) [A-Za-z0-9= ._-]+$/.test(s)||/^ERROR_CLASS [A-Za-z0-9_.$]+$/.test(s)||/^DDMD_CODE -?[0-9]+$/.test(s)||/^FRAME [A-Za-z0-9_.$<>]+:-?[0-9]+$/.test(s)||/^RESPONSE_CLASS [A-Za-z0-9_.$;\[\]]+$/.test(s));
 const passed=code===0&&lines.some(s=>s.startsWith('RESULT GATEWAY_PASS '));
 const report={startedAtUtc,finishedAtUtc:new Date().toISOString(),sourceSha256:hash,recipientSha256:state.recipientSha256,mode,preflight,exitCode:code,passed,authenticationSucceeded:lines.some(s=>s.startsWith('RESULT AUTHENTICATED ')),stderrBytes,lines};
 fs.writeFileSync(new URL('gateway-result-'+startedAtUtc.replaceAll(':','-')+'.json',evidence),JSON.stringify(report,null,2)+'\n');
 fs.writeFileSync(new URL('gateway-'+mode+'-result.json',evidence),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify(report,null,2));
 if(!passed)process.exitCode=1;
} catch {
 console.error('LIVE_SETUP_FAILED: no secret details emitted');
 process.exitCode=1;
}
