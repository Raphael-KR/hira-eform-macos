import os from 'node:os';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {createRequire} from 'node:module';
import {loadEncryptedKeyDer} from '../../../src/krPbe.js';
import {readCertificatePassword} from '../../../src/keychain.js';
const require=createRequire(new URL('../../../package.json',import.meta.url));const forge=require('node-forge');
const root=new URL('../private-downloads/notice-xcDjRX/',import.meta.url);let stage='integrity';
const report={networkRequests:0,signatureCryptographicallyValid:false,signedAttachmentDigestMatches:false,decrypted:false};
const ensure=b=>{if(!b)throw Error('validation failed');};
const oid=n=>forge.asn1.derToOid(n.value);
try{
 process.umask(0o077);
 const recovered=JSON.parse(fs.readFileSync(new URL('../evidence/macos-download-recovered.json',import.meta.url)));
 for(const f of recovered.files)ensure(crypto.createHash('sha256').update(fs.readFileSync(f.file)).digest('hex')===f.sha256);
 const enc=fs.readFileSync(new URL('encrypted-notice.cms',root));const sig=fs.readFileSync(new URL('signature.cms',root));
 stage='signature';
 // -noverify separates signature mathematics from certificate identity trust below.
 const verify=spawnSync('openssl',['cms','-verify','-binary','-inform','DER','-noverify'],{input:sig,maxBuffer:1048576});ensure(verify.status===0);report.signatureCryptographicallyValid=true;
 const contents=forge.asn1.fromDer(verify.stdout.toString('binary'));ensure(contents.type===16&&contents.value.length===1);
 const entry=contents.value[0];ensure(entry.type===16&&entry.value.length===2);
 const digestInfo=entry.value[1];const algorithm=oid(digestInfo.value[0].value[0]);ensure(algorithm==='2.16.840.1.101.3.4.2.1');
 ensure(crypto.timingSafeEqual(Buffer.from(digestInfo.value[1].value,'binary'),crypto.createHash('sha256').update(enc).digest()));report.signedAttachmentDigestMatches=true;report.digestAlgorithm='SHA-256';
 const pkcs7=forge.pkcs7.messageFromAsn1(forge.asn1.fromDer(sig.toString('binary')));ensure(pkcs7.certificates.length===1);
 const signer=pkcs7.certificates[0];const center=forge.pki.certificateFromAsn1(forge.asn1.fromDer(fs.readFileSync('/private/tmp/hira-wine-trial/prefix/drive_c/hira/DDMD/data/kmCert.der').toString('binary')));
 report.signerMatchesInstalledCenterKey=signer.publicKey.n.equals(center.publicKey.n)&&signer.publicKey.e.equals(center.publicKey.e);
 report.signerCurrentlyValid=Date.now()>=signer.validity.notBefore&&Date.now()<=signer.validity.notAfter;
 report.signerCertificateSha256=crypto.createHash('sha256').update(Buffer.from(forge.asn1.toDer(forge.pki.certificateToAsn1(signer)).getBytes(),'binary')).digest('hex');
 stage='key-load';
 const base=os.homedir()+'/Library/Preferences/NPKI/KICA/USER';const dirs=fs.readdirSync(base,{withFileTypes:true}).filter(e=>e.isDirectory()).map(e=>base+'/'+e.name).filter(d=>fs.existsSync(d+'/kmCert.der')&&fs.existsSync(d+'/kmPri.key'));ensure(dirs.length===1);
 const cert=forge.pki.certificateFromAsn1(forge.asn1.fromDer(fs.readFileSync(dirs[0]+'/kmCert.der').toString('binary')));
 let password=readCertificatePassword(),key;try{key=loadEncryptedKeyDer(fs.readFileSync(dirs[0]+'/kmPri.key').toString('binary'),password);}finally{password=undefined;}
 ensure(key.n.equals(cert.publicKey.n)&&key.e.equals(cert.publicKey.e));
 stage='decrypt';const top=forge.asn1.fromDer(enc.toString('binary'));ensure(oid(top.value[0])==='1.2.840.113549.1.7.3');const env=top.value[1].value[0];const recipients=env.value.find(n=>n.tagClass===0&&n.type===17);ensure(recipients.value.length===1);const recipient=recipients.value[0];
 ensure(oid(recipient.value[2].value[0])==='1.2.840.113549.1.1.1');
 const normalize=s=>s.replace(/^0+/,'').toLowerCase();ensure(normalize(forge.util.bytesToHex(recipient.value[1].value[1].value))===normalize(cert.serialNumber));
 const secret=key.decrypt(recipient.value[3].value,'RSAES-PKCS1-V1_5');const content=env.value[env.value.indexOf(recipients)+1];ensure(oid(content.value[1].value[0])==='1.2.410.200004.1.4');
 const bytes=n=>typeof n.value==='string'?n.value:n.value.map(bytes).join('');const dec=forge.cipher.createDecipher('SEED-CBC',secret);dec.start({iv:content.value[1].value[1].value});dec.update(forge.util.createBuffer(bytes(content.value[2])));ensure(dec.finish());
 const plain=Buffer.from(dec.output.getBytes(),'binary');ensure(plain.length>0);
 const dest=new URL('decrypted-notice.bin',root);fs.writeFileSync(dest,plain,{flag:'wx',mode:0o600});report.decrypted=true;report.plaintextBytes=plain.length;report.plaintextSha256=crypto.createHash('sha256').update(plain).digest('hex');report.outputPath=dest.pathname;report.format=plain.subarray(0,2).equals(Buffer.from('PK'))?'ZIP':plain.subarray(0,4).toString('ascii')==='%PDF'?'PDF':'binary-or-text';plain.fill(0);
 report.completedAtUtc=new Date().toISOString();fs.writeFileSync(new URL('../evidence/macos-notice-verification.json',import.meta.url),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
}catch{report.failedStage=stage;fs.writeFileSync(new URL('../evidence/macos-notice-verification.json',import.meta.url),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));process.exitCode=1;}
