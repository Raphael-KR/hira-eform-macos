import java.io.*;
import java.security.Key;
import java.util.*;
import hira.ddmd.jmc.agent.auth.AuthToken;
import hira.ddmd.jmc.agent.spi.bizframe.msi.MsiAgent;
import hira.ddmd.jmc.common.*;
import hira.ddmd.jmc.common.dto.*;
import hira.ddmd.jmc.common.crypto.*;
import hira.ddmd.jmc.common.crypto.spec.*;
import kr.co.bizframe.msi.protocol.DefaultMessageProtocol;
import kr.co.bizframe.msi.registry.SimpleAttachmentReferenceRegistry;
import kr.co.bizframe.msi.support.http.SimpleHttpMessageSender;
import org.apache.commons.httpclient.*;

/** Isolated HIRA module-update trial; no SAM submission action. */
public final class UpdateDownloadProbe {
 static Object lookup(AuthToken token)throws Exception {
  HeadlessGateway.require(!token.isExpired(),"expired token");
  ModUpdReq body=new ModUpdReq();body.setYkiho(HeadlessGateway.ykiho);body.setNChk("Y");
  java.util.List<ModUpdInf> modules=new ArrayList<ModUpdInf>();
  for(String line:java.nio.file.Files.readAllLines(HeadlessGateway.base.resolve("modules.tsv"),java.nio.charset.StandardCharsets.UTF_8)){
   String[] f=line.split("\t",-1);ModUpdInf m=new ModUpdInf();m.setModId(f[0]);m.setModTpCd(ModUpdInf.Type.typeOf(f[1]).getValue());m.setModVer(Integer.parseInt(f[2]));
   if(!f[3].isEmpty())m.setModUpdDt(new java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss").parse(f[3]));m.setFndtPth(f[4]);m.setChecksum(f[5]);modules.add(m);
  }body.setModUpdInfs(modules);
  EnvelopedDataCipher cipher=HeadlessGateway.crypto.openEnvelopedDataCipher();cipher.initEncrypt(HeadlessGateway.center.getEncoded());
  byte[] encrypted=cipher.process(HeadlessGateway.serialize(body));SecretKeyWithIV responseKey=cipher.getProcessingKey();
  DdmdMessage request=new DdmdMessage();request.setAction("CLT_MOD_UPT");
  request.setHeader("From","Client");request.setHeader("userId",HeadlessGateway.ykiho);request.setHeader("ddmd-secure","true");request.setBody(encrypted);
  String id=token.getTokenId(),verifier=(String)token.getAttribute("verifier"),timestamp=Long.toString(System.currentTimeMillis());
  HeadlessGateway.require(verifier!=null,"missing verifier");
  request.setHeader("ddmd-authentication-token-identifier",id);request.setHeader("ddmd-authentication-token-verifier",verifier);request.setHeader("ddmd-authentication-timestamp",timestamp);
  DataMessageAuthenticationCode mac=HeadlessGateway.crypto.openDataMessageAuthenticationCode((String)token.getAttribute("macAlgorithm"));mac.init((Key)token.getAttribute("key"));
  request.setHeader("ddmd-authentication-mac",Base64.getEncoder().encodeToString(mac.calculate((id+verifier+timestamp).getBytes("US-ASCII"))));
  HttpClient http=new HttpClient();http.getHttpConnectionManager().getParams().setConnectionTimeout(15000);http.getHttpConnectionManager().getParams().setSoTimeout(30000);
  SimpleAttachmentReferenceRegistry registry=new SimpleAttachmentReferenceRegistry();registry.setDirectory(HeadlessGateway.base.resolve("parts").toFile());
  DefaultMessageProtocol protocol=new DefaultMessageProtocol();protocol.setAttachmentReferenceRegistry(registry);
  SimpleHttpMessageSender sender=new SimpleHttpMessageSender();sender.setHttpClient(http);sender.setMessageProtocol(protocol);sender.setAttachmentReferenceRegistry(registry);sender.setHttpMethodRetryHandler(new DefaultHttpMethodRetryHandler(0,false));sender.afterPropertiesSet();
  MsiAgent agent=new MsiAgent();agent.setEndpoint(HeadlessGateway.ENDPOINT);agent.setMessageSender(sender);agent.setResumableAttachmentEnable(false);
  HeadlessGateway.stage="update-query";HeadlessGateway.requestCount++;
  DdmdMessage response=agent.send(request);
  HeadlessGateway.require(response.getBody() instanceof byte[],"unexpected response");
  DataSymmetricCipher dec=HeadlessGateway.crypto.openDataSymmetricCipher();dec.init(2,responseKey);byte[] plain=dec.cipher((byte[])response.getBody());
  HeadlessGateway.require(plain.length<=1048576,"response too large");
  Object result;try(ObjectInputStream in=new ObjectInputStream(new ByteArrayInputStream(plain)){protected Class<?> resolveClass(ObjectStreamClass d)throws IOException,ClassNotFoundException{if(d.getName().matches("[A-Za-z0-9_.$;\\[\\]]+"))HeadlessGateway.REPORT.println("RESPONSE_CLASS "+d.getName());return super.resolveClass(d);}}){result=in.readObject();}finally{Arrays.fill(plain,(byte)0);}
  token.updateAndGetVerifier(HeadlessGateway.crypto);
  boolean authenticatedResponse=false; if(result instanceof Map){Map values=(Map)result;authenticatedResponse=values.get("authToken") instanceof AuthToken;if(values.get("authToken") instanceof AuthToken)token.updateExpiredTime((AuthToken)values.get("authToken"));result=values.get("body");}
  if(result instanceof Exception)throw (Exception)result;
  HeadlessGateway.require(result instanceof ModUpdRes,"unexpected update type");
  ModUpdRes update=(ModUpdRes)result;
  java.util.List<String> rows=new ArrayList<String>();
  for(Map.Entry<ModUpdInf,String> entry:update.getModUpdInfs().entrySet()){
   ModUpdInf m=entry.getKey();rows.add(m.getModId()+"\t"+m.getModVer()+"\t"+m.getFndtPth()+"\t"+m.getChecksum()+"\t"+entry.getValue()+"\t"+response.getFile(entry.getValue()).getCanonicalPath()+"\t"+ModUpdInf.Type.typeOf(m.getModTpCd()).getName());
  }
  java.nio.file.Files.write(HeadlessGateway.base.resolve("downloaded-modules.tsv"),rows,java.nio.charset.StandardCharsets.UTF_8);
  HeadlessGateway.REPORT.println("CHECK updateQuery=true installedModules="+modules.size()+" offeredModules="+rows.size()+" authenticatedResponse="+authenticatedResponse+" attachments="+response.getFiles().size());
  return result;
 }
 public static void main(String[] args){try{
  final sun.misc.ObjectInputFilter filter=sun.misc.ObjectInputFilter.Config.createFilter(System.getProperty("hira.update.serialFilter"));
  sun.misc.ObjectInputFilter.Config.setSerialFilter(info->{sun.misc.ObjectInputFilter.Status status=filter.checkInput(info);if(status==sun.misc.ObjectInputFilter.Status.REJECTED)HeadlessGateway.REPORT.println("CHECK rejectedClass="+(info.serialClass()==null?"null":info.serialClass().getName())+" bytes="+info.streamBytes()+" array="+info.arrayLength()+" depth="+info.depth()+" refs="+info.references());return status;});
  HeadlessGateway.initialize();AuthToken token=HeadlessGateway.authenticate();lookup(token);
  HeadlessGateway.require(HeadlessGateway.guard.denied==0,"unexpected denial");
  HeadlessGateway.REPORT.println("RESULT GATEWAY_PASS mode=update-download headless=true requests="+HeadlessGateway.requestCount);
 }catch(Throwable e){
  HeadlessGateway.REPORT.println("RESULT FAILED stage="+HeadlessGateway.stage+" requests="+HeadlessGateway.requestCount);
  for(int i=0;e!=null&&i<5;i++,e=e.getCause()){
   HeadlessGateway.REPORT.println("ERROR_CLASS "+e.getClass().getName());if(e instanceof DdmdException)HeadlessGateway.REPORT.println("DDMD_CODE "+((DdmdException)e).getErrorCode());
  }System.exit(1);
 }finally{if(HeadlessGateway.random!=null)Arrays.fill(HeadlessGateway.random,(byte)0);}}
}
