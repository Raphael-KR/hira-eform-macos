import os from 'node:os';
// Owner-authorized identity load. Never emits private keys, passwords, DN or VID values.
import fs from 'node:fs';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
const require=createRequire(new URL('../../../package.json',import.meta.url));
const forge=require('node-forge');
const {readCertificatePassword}=await import('../../../src/keychain.js');
// Reuse the reviewed decryption implementation without editing the released package.
const sourceUrl=new URL('../../../src/krPbe.js',import.meta.url);
let source=fs.readFileSync(sourceUrl,'utf8');
if(!source.includes('function decryptEpki(epkiAsn1, password)'))throw Error('key API changed');
source=source.replace('import forge from "node-forge";',`import forge from ${JSON.stringify(pathToFileURL(require.resolve('node-forge')).href)};`)
 .replace('import "./seed.js";',`import ${JSON.stringify(new URL('../../../src/seed.js',import.meta.url).href)};`)
 .replace('function decryptEpki(epkiAsn1, password)','export function decryptEpki(epkiAsn1, password)');
const {decryptEpki}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
export function loadIdentity(){
 const root=os.homedir()+'/Library/Preferences/NPKI/KICA/USER';
 const pairs=fs.readdirSync(root,{withFileTypes:true}).filter(e=>e.isDirectory()).map(e=>root+'/'+e.name).filter(p=>fs.existsSync(p+'/signCert.der')&&fs.existsSync(p+'/signPri.key'));
 if(pairs.length!==1)throw Error('Expected exactly one certificate pair');
 const certDer=fs.readFileSync(pairs[0]+'/signCert.der').toString('binary');
 const cert=forge.pki.certificateFromAsn1(forge.asn1.fromDer(certDer));
 if(Date.now()<cert.validity.notBefore || Date.now()>cert.validity.notAfter)throw Error('Certificate not currently valid');
 let pw=readCertificatePassword();let der;
 try{der=decryptEpki(forge.asn1.fromDer(fs.readFileSync(pairs[0]+'/signPri.key').toString('binary')),pw);}finally{pw=undefined;}
 const raw=forge.asn1.fromDer(der),key=forge.pki.privateKeyFromAsn1(raw);
 if(!key.n.equals(cert.publicKey.n)||!key.e.equals(cert.publicKey.e))throw Error('Certificate/key mismatch');
 const attrs=raw.value.find(n=>n.tagClass===128&&n.type===0);
 const values=(attrs?.value||[]).map(n=>({oid:forge.asn1.derToOid(n.value[0].value),node:n.value[1]}));
 return {certDer,cert,values};
}
if(process.argv.includes('--inspect')){
 try{const i=loadIdentity();console.log(JSON.stringify({certificatePairs:1,passwordAndKeyMatch:true,certificateValid:true,privateKeyAttributeOids:i.values.map(v=>v.oid)}));}
 catch{console.error('IDENTITY_CHECK_FAILED: certificate/password/key access or match');process.exitCode=1;}
}
