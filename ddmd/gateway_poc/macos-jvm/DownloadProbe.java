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

/** Read-only public-recipient metadata query; no document or attachment API. */
public final class DownloadProbe {
 static Object request(AuthToken token,String action,Object body)throws Exception {
  HeadlessGateway.require(!token.isExpired(),"expired token");
  EnvelopedDataCipher cipher=HeadlessGateway.crypto.openEnvelopedDataCipher();cipher.initEncrypt(HeadlessGateway.center.getEncoded());
  byte[] encrypted=cipher.process(HeadlessGateway.serialize(body));SecretKeyWithIV responseKey=cipher.getProcessingKey();
  DdmdMessage request=new DdmdMessage();request.setAction(action);if(action.equals("CLT_NTC_REQ"))request.setHeader("km_cert",Base64.getEncoder().encodeToString(HeadlessGateway.downloadCert.getEncoded()));
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
  HeadlessGateway.stage=action.equals("CLT_NTC_REQ")?"notice-download":"notice-list-query";HeadlessGateway.requestCount++;
  DdmdMessage response=agent.send(request);
  HeadlessGateway.require(response.getBody() instanceof byte[],"unexpected response");
  DataSymmetricCipher dec=HeadlessGateway.crypto.openDataSymmetricCipher();dec.init(2,responseKey);byte[] plain=dec.cipher((byte[])response.getBody());
  HeadlessGateway.require(plain.length<=1048576,"response too large");
  Object result;try(ObjectInputStream in=new ObjectInputStream(new ByteArrayInputStream(plain)){protected Class<?> resolveClass(ObjectStreamClass d)throws IOException,ClassNotFoundException{if(d.getName().matches("[A-Za-z0-9_.$;\\[\\]]+"))HeadlessGateway.REPORT.println("RESPONSE_CLASS "+d.getName());return super.resolveClass(d);}}){result=in.readObject();}finally{Arrays.fill(plain,(byte)0);}
  token.updateAndGetVerifier(HeadlessGateway.crypto);
  boolean authenticatedResponse=false; if(result instanceof Map){Map values=(Map)result;authenticatedResponse=values.get("authToken") instanceof AuthToken;if(values.get("authToken") instanceof AuthToken)token.updateExpiredTime((AuthToken)values.get("authToken"));result=values.get("body");}
  if(result instanceof Exception)throw (Exception)result;
  if(action.equals("CLT_NTC_REQ")){
   HeadlessGateway.require(result instanceof NtcDoc,"unexpected downloaded document metadata");
   HeadlessGateway.require(!response.getFiles().isEmpty(),"download returned no attachments");
   HeadlessGateway.stage="save-download";
   java.nio.file.Path output=java.nio.file.Paths.get(System.getProperty("hira.output"));int index=0;long bytes=0;
   for(Map.Entry<String,File> entry:response.getFiles().entrySet()){
    File file=entry.getValue();HeadlessGateway.require(file.isFile(),"missing attachment");
    java.nio.file.Path target=output.resolve(String.format("attachment-%02d.bin",++index));
    java.nio.file.Files.copy(file.toPath(),target);java.nio.file.Files.setPosixFilePermissions(target,java.nio.file.attribute.PosixFilePermissions.fromString("rw-------"));bytes+=java.nio.file.Files.size(target);
   }
   HeadlessGateway.REPORT.println("CHECK downloaded=true attachments="+index+" bytes="+bytes+" decrypted=false signatureVerified=false");
  }else{HeadlessGateway.require(result instanceof Collection&&response.getFiles().isEmpty(),"unexpected list");for(Object x:(Collection)result)HeadlessGateway.require(x instanceof NtcDoc,"unexpected list item");}
  return result;
 }
 public static void main(String[] args){try{
  HeadlessGateway.initialize();AuthToken token=HeadlessGateway.authenticate();
  NtcRef query=new NtcRef();query.setYkiho(HeadlessGateway.ykiho);Calendar start=Calendar.getInstance();start.add(Calendar.DAY_OF_YEAR,-90);java.text.SimpleDateFormat fmt=new java.text.SimpleDateFormat("yyyy-MM-dd");query.setBrokerRcvFromDT(fmt.format(start.getTime()));query.setBrokerRcvToDT(fmt.format(new Date()));query.setDmdTpCd("0");query.setHbrCd("");query.setInsuTpCd("Y");
  Collection docs=(Collection)request(token,"CLT_NTC_LIST_REQ",query);HeadlessGateway.require(!docs.isEmpty(),"no documents");
  NtcDoc selected=null;for(Object x:docs){NtcDoc d=(NtcDoc)x;if(selected==null||(d.getBrokerRcvDT()!=null&&(selected.getBrokerRcvDT()==null||d.getBrokerRcvDT().after(selected.getBrokerRcvDT()))))selected=d;}
  NtcRef ref=new NtcRef();ref.setYkiho(HeadlessGateway.ykiho);ref.setNtcDocId(selected.getNtcDocId());ref.setHbrCd(selected.getHbrCd());ref.setDmdTpCd(selected.getDmdTpCd());ref.setInsuTpCd(selected.getInsuTpCd());ref.setBrokerRcvDT(selected.getBrokerRcvDT());
  request(token,"CLT_NTC_REQ",ref);
  HeadlessGateway.require(HeadlessGateway.guard.denied==0,"unexpected denial");
  HeadlessGateway.REPORT.println("RESULT GATEWAY_PASS mode=download headless=true requests="+HeadlessGateway.requestCount);
 }catch(Throwable e){
  HeadlessGateway.REPORT.println("RESULT FAILED stage="+HeadlessGateway.stage+" requests="+HeadlessGateway.requestCount);
  for(int i=0;e!=null&&i<5;i++,e=e.getCause()){
   HeadlessGateway.REPORT.println("ERROR_CLASS "+e.getClass().getName());if(e instanceof DdmdException)HeadlessGateway.REPORT.println("DDMD_CODE "+((DdmdException)e).getErrorCode());
  }System.exit(1);
 }finally{if(HeadlessGateway.random!=null)Arrays.fill(HeadlessGateway.random,(byte)0);}}
}
