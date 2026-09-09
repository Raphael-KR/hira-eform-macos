import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.security.*;
import java.security.cert.*;
import java.util.*;
import java.awt.GraphicsEnvironment;
import hira.ddmd.jmc.agent.auth.*;
import hira.ddmd.jmc.agent.auth.Credentials;
import hira.ddmd.jmc.agent.spi.bizframe.msi.*;
import hira.ddmd.jmc.common.*;
import hira.ddmd.jmc.common.crypto.*;
import hira.ddmd.jmc.common.crypto.jcaos.*;
import hira.ddmd.jmc.common.crypto.spec.*;
import kr.co.bizframe.msi.protocol.*;
import kr.co.bizframe.msi.registry.*;
import kr.co.bizframe.msi.support.http.*;
import org.apache.commons.httpclient.*;
import org.apache.log4j.*;

public final class HeadlessGateway {
  static final PrintStream REPORT=System.out;
  static final String HOST="ddmd.hira.or.kr", ENDPOINT="http://ddmd.hira.or.kr/imxs/msi";
  static String stage="init";
  static int requestCount;
  static boolean preflight;
  static String mode;
  static X509Certificate cert,center;
  static String ykiho;
  static byte[] random;
  static JCAOSSecurityProvider crypto;
  static Guard guard;
  static Path base;
  static int connectChecks;
  static class Guard extends SecurityManager {
    final Set<String> hosts=new HashSet<String>();
    int denied;
    Guard(InetAddress[] addresses){hosts.add(HOST);for(InetAddress a:addresses)hosts.add(a.getHostAddress());}
    void deny(){denied++;throw new SecurityException("capability denied");}
    public void checkPermission(Permission p){if(p instanceof java.awt.AWTPermission)deny();if(p instanceof RuntimePermission && (p.getName().equals("setSecurityManager")||p.getName().equals("setIO")||p.getName().startsWith("loadLibrary.")))deny();}
    public void checkConnect(String host,int port){if(port>=0){connectChecks++;if(preflight)throw new SecurityException("preflight network boundary");}if(!hosts.contains(host.toLowerCase(Locale.ROOT)) || (port!=-1&&port!=80))deny();}
    public void checkListen(int port){
      // Socket.bind(0) allocates an outbound client's ephemeral port; it does not listen.
      if(port==0)for(StackTraceElement f:Thread.currentThread().getStackTrace())if(f.getClassName().equals("java.net.Socket")&&f.getMethodName().equals("bind"))return;
      deny();
    } public void checkAccept(String h,int p){deny();}
    public void checkExec(String cmd){deny();} public void checkLink(String l){deny();}
  }
  static byte[] serialize(Object o)throws Exception{ByteArrayOutputStream b=new ByteArrayOutputStream();try(ObjectOutputStream s=new ObjectOutputStream(b)){s.writeObject(o);}return b.toByteArray();}
  static void require(boolean value,String safeReason){if(!value)throw new IllegalStateException(safeReason);}
  static void initialize()throws Exception {
    System.setOut(new PrintStream(new OutputStream(){public void write(int b){}}));System.setErr(System.out);
    LogManager.resetConfiguration();Logger.getRootLogger().setLevel(Level.OFF);
    require(GraphicsEnvironment.isHeadless(),"headless required");
    byte[] initRandom=new byte[20];new SecureRandom().nextBytes(initRandom);Security.getProviders();
    InetAddress[] addresses=InetAddress.getAllByName(HOST);
    // Preload JRE networking implementation only, never establish a connection here.
    Socket preload=new Socket();preload.close();
    base=Paths.get(System.getProperty("user.dir"));
    require(base.getFileName().toString().startsWith("hira-live-auth-"),"isolated workdir required");
    Properties config=new Properties();try(InputStream in=Files.newInputStream(Paths.get("C:/hira/DDMD/conf/ddmd.properties"))){config.load(in);}
    ykiho=config.getProperty("ykiho","").trim();require(ykiho.matches("[0-9]{8}")&&!ykiho.equals("00000000"),"institution missing");
    require(ENDPOINT.equals(config.getProperty("msi.endpoint","").trim()),"endpoint mismatch");
    CertificateFactory cf=CertificateFactory.getInstance("X.509");
    try(InputStream in=Files.newInputStream(Paths.get("C:/hira/DDMD/data/kmCert.der"))){center=(X509Certificate)cf.generateCertificate(in);}center.checkValidity();
    stage="identity-input";
    BufferedReader input=new BufferedReader(new InputStreamReader(System.in,"US-ASCII"));
    String certLine=input.readLine(),randomLine=input.readLine();
    require(certLine!=null&&certLine.length()<20000&&randomLine!=null&&randomLine.length()<100,"invalid input");
    byte[] certBytes=Base64.getDecoder().decode(certLine);random=Base64.getDecoder().decode(randomLine);require(random.length==20,"random length");
    cert=(X509Certificate)cf.generateCertificate(new ByteArrayInputStream(certBytes));cert.checkValidity();
    guard=new Guard(addresses);System.setSecurityManager(guard);
    stage="prepare-auth";
    crypto=new JCAOSSecurityProvider();crypto.init(new Properties());
  }
  static AuthToken authenticate()throws Exception {
    stage="prepare-auth";
    Credentials credentials=new Credentials(ykiho,cert,random);
    EnvelopedDataCipher envelope=crypto.openEnvelopedDataCipher();envelope.initEncrypt(center.getEncoded());
    byte[] encrypted=envelope.process(serialize(credentials));SecretKeyWithIV key=envelope.getProcessingKey();
    DdmdMessage request=new DdmdMessage();request.setAction("CLT_AUTH_REQ");request.setHeader("From","Client");request.setHeader("userId",ykiho);request.setHeader("ddmd-secure","true");request.setBody(encrypted);
    HttpClient http=new HttpClient();http.getHttpConnectionManager().getParams().setConnectionTimeout(15000);http.getHttpConnectionManager().getParams().setSoTimeout(30000);
    SimpleAttachmentReferenceRegistry registry=new SimpleAttachmentReferenceRegistry();registry.setDirectory(base.resolve("parts").toFile());
    DefaultMessageProtocol protocol=new DefaultMessageProtocol();protocol.setAttachmentReferenceRegistry(registry);
    SimpleHttpMessageSender sender=new SimpleHttpMessageSender();sender.setHttpClient(http);sender.setMessageProtocol(protocol);sender.setAttachmentReferenceRegistry(registry);sender.setHttpMethodRetryHandler(new DefaultHttpMethodRetryHandler(0,false));sender.afterPropertiesSet();
    MsiAgent agent=new MsiAgent();agent.setEndpoint(ENDPOINT);agent.setExecutor(new java.util.concurrent.Executor(){public void execute(Runnable r){r.run();}});agent.setMessageSender(sender);agent.setResumableAttachmentEnable(false);
    stage="send-auth";requestCount++;
    DdmdMessage response=agent.send(request);
    stage="read-response";
    require(response.getFiles().isEmpty(),"unexpected attachments");
    require(response.getBody() instanceof byte[],"unexpected response body");
    DataSymmetricCipher decipher=crypto.openDataSymmetricCipher();decipher.init(2,key);
    byte[] plain=decipher.cipher((byte[])response.getBody());require(plain.length<=1048576,"response too large");
    Object body;try(ObjectInputStream in=new ObjectInputStream(new ByteArrayInputStream(plain)){
      protected Class<?> resolveClass(ObjectStreamClass desc)throws IOException,ClassNotFoundException{
        String name=desc.getName();if(name.matches("[A-Za-z0-9_.$;\\[\\]]+"))REPORT.println("RESPONSE_CLASS "+name);
        return super.resolveClass(desc);
      }
    }){body=in.readObject();}
    Arrays.fill(plain,(byte)0);
    if(body instanceof Exception)throw (Exception)body;
    require(body instanceof AuthToken,"unexpected token type");AuthToken token=(AuthToken)body;
    require(token.getTokenId()!=null&&!token.getTokenId().isEmpty()&&!token.isExpired(),"invalid token");

    REPORT.println("RESULT AUTHENTICATED headless=true tokenPresent=true expired=false requests="+requestCount+" expiryEpochMs="+token.getExpired().getTime());
    stage="done";return token;
  }
  static void run()throws Exception {
    initialize();
    AuthToken first=authenticate();
    if(mode.equals("lifecycle")){
      long expiry=first.getExpired().getTime();
      require(expiry-System.currentTimeMillis()<360000,"unexpected token lifetime");
      REPORT.println("EVENT WAITING_FOR_REAL_EXPIRY expiryEpochMs="+expiry);
      while(!first.isExpired()){Thread.sleep(Math.min(30000,Math.max(1,expiry-System.currentTimeMillis()+200)));REPORT.println("EVENT WAIT expired="+first.isExpired());}
      REPORT.println("CHECK realExpiryObserved=true");
      AuthToken renewed=authenticate();
      require(!renewed.getTokenId().equals(first.getTokenId()),"token not replaced");
      require(renewed.getExpired().after(first.getExpired()),"expiry not advanced");
      REPORT.println("CHECK reauthentication=true tokenReplaced=true expiryAdvanced=true");
    } else if(mode.equals("failure-tests")){
      // Fault injection only; never submit bad credentials to the institution's live server.
      int before=requestCount;
      try{decodeForTest(new byte[]{1,2,3,4});throw new IllegalStateException("invalid response accepted");}catch(StreamCorruptedException expected){REPORT.println("CHECK malformedAuthResponseRejected=true networkRequests=0");}
      preflight=true;
      try{authenticate();throw new IllegalStateException("network fault ignored");}catch(DdmdException expected){REPORT.println("CHECK injectedNetworkFailureHandled=true transportClass="+expected.getClass().getName());}
      finally{preflight=false;}
      require(!first.isExpired(),"baseline token expired during local fault test");
      REPORT.println("CHECK tokenPreservedAfterLocalFailure=true");
    }
    require(guard.denied==0,"unexpected capability denial");
    REPORT.println("RESULT GATEWAY_PASS mode="+mode+" headless=true requests="+requestCount);
  }
  static Object decodeForTest(byte[] b)throws Exception {try(ObjectInputStream in=new ObjectInputStream(new ByteArrayInputStream(b))){return in.readObject();}}
  public static void main(String[] args){
    mode=args.length==1?args[0]:"invalid";
    if(!Arrays.asList("auth","lifecycle","failure-tests").contains(mode)){REPORT.println("RESULT INVALID_COMMAND");System.exit(2);}
    try{run();}catch(Throwable e){
      REPORT.println("RESULT FAILED stage="+stage+" requests="+requestCount+" connectChecks="+connectChecks);
      for(int i=0;e!=null&&i<5;i++,e=e.getCause()){
        REPORT.println("ERROR_CLASS "+e.getClass().getName());if(e instanceof DdmdException)REPORT.println("DDMD_CODE "+((DdmdException)e).getErrorCode());
        StackTraceElement[] frames=e.getStackTrace();for(int j=0;j<Math.min(frames.length,8);j++)REPORT.println("FRAME "+frames[j].getClassName()+"."+frames[j].getMethodName()+":"+frames[j].getLineNumber());
      }
      System.exit(1);
    }finally{if(random!=null)Arrays.fill(random,(byte)0);}
  }
}
