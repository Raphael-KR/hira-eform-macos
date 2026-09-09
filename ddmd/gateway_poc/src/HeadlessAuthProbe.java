import java.io.*;
import java.nio.file.*;
import java.security.*;
import java.security.cert.*;
import java.security.spec.PKCS8EncodedKeySpec;
import java.util.*;
import java.awt.GraphicsEnvironment;
import hira.ddmd.jmc.agent.auth.*;
import hira.ddmd.jmc.common.crypto.*;
import hira.ddmd.jmc.common.crypto.jcaos.JCAOSSecurityProvider;
import hira.ddmd.jmc.common.crypto.magicline.MagicLineKeyInfo;
import hira.ddmd.jmc.common.crypto.spec.*;

/** Offline synthetic protocol-shape test, not a HIRA server/client implementation. */
public final class HeadlessAuthProbe {
  static int passes=0;
  static final class Guard extends SecurityManager {
    int blocked=0;
    void record(String kind){blocked++;System.out.println("BLOCK "+kind);for(StackTraceElement s:Thread.currentThread().getStackTrace()){String n=s.getClassName();if(n.startsWith("ksign.")||n.startsWith("com.ksign.")||n.startsWith("hira."))System.out.println("BLOCK_CALLER "+n+"."+s.getMethodName());}}
    public void checkPermission(Permission p) {
      if (p instanceof RuntimePermission && (p.getName().equals("setSecurityManager") || p.getName().startsWith("loadLibrary.") || p.getName().equals("setIO"))) {record("runtime "+p.getName());throw new SecurityException("blocked runtime capability");}
      if (p instanceof java.awt.AWTPermission) {record("AWT "+p.getName());throw new SecurityException("blocked AWT capability");}
    }
    public void checkConnect(String h,int p){record("network connect");throw new SecurityException("network blocked");}
    public void checkListen(int p){record("network listen");throw new SecurityException("network blocked");}
    public void checkAccept(String h,int p){record("network accept");throw new SecurityException("network blocked");}
    public void checkExec(String cmd){record("process");throw new SecurityException("process blocked");}
    public void checkLink(String lib){record("native "+lib);throw new SecurityException("native library blocked");}
  }
  static void ok(boolean b,String label){if(!b)throw new AssertionError(label);passes++;System.out.println("PASS "+label);}
  static byte[] serialize(Object o)throws Exception{ByteArrayOutputStream b=new ByteArrayOutputStream();try(ObjectOutputStream s=new ObjectOutputStream(b)){s.writeObject(o);}return b.toByteArray();}
  // Deserialize only locally generated synthetic data. Never use this helper for server input.
  static Object deserialize(byte[] b)throws Exception{try(ObjectInputStream s=new ObjectInputStream(new ByteArrayInputStream(b))){return s.readObject();}}
  static void blocked(Runnable r,String label){boolean b=false;try{r.run();}catch(SecurityException e){b=true;}ok(b,label);}
  public static void main(String[] args)throws Exception {
    if(args.length!=1 || !args[0].contains("hira-headless-poc-"))throw new IllegalArgumentException("dedicated synthetic fixture directory required");
    ok("true".equals(System.getProperty("java.awt.headless")) && GraphicsEnvironment.isHeadless(),"strict Java headless enabled");
    Path root=Paths.get(args[0]);
    X509Certificate cert=(X509Certificate)CertificateFactory.getInstance("X.509").generateCertificate(new ByteArrayInputStream(Files.readAllBytes(root.resolve("signCert.der"))));
    cert.checkValidity();cert.verify(cert.getPublicKey());
    ok(cert.getSubjectX500Principal().getName().contains("OU=SYNTHETIC-ONLY"),"self-signed synthetic-only certificate");
    byte[] pk8=Files.readAllBytes(root.resolve("private.pk8"));
    PrivateKey key=KeyFactory.getInstance("RSA").generatePrivate(new PKCS8EncodedKeySpec(pk8));
    // Prime only the JRE entropy source before the guard: Windows JRE initializes
    // NetworkInterface native support while gathering entropy; no socket is opened.
    byte[] random=new byte[20];new SecureRandom().nextBytes(random);
    // Initialize standard JRE providers (including SunEC/SunMSCAPI) without
    // opening any keystore. DDMD/KSign classes are still loaded after the guard.
    Security.getProviders();
    Guard guard=new Guard();System.setSecurityManager(guard);
    blocked(()->guard.checkConnect("network-is-disabled.invalid",443),"network deny guard");
    blocked(()->guard.checkExec("disabled"),"process deny guard");
    blocked(()->guard.checkLink("disabled"),"native deny guard");
    blocked(()->guard.checkPermission(new java.awt.AWTPermission("showWindowWithoutWarningBanner")),"AWT deny guard");
    int expectedBlocks=guard.blocked;
    // Jars exclude ddmd-client, bootstrap and all GUI controllers.
    boolean noLauncher=false;try{Class.forName("hira.ddmd.jmc.client.presentation.Launcher",false,HeadlessAuthProbe.class.getClassLoader());}catch(ClassNotFoundException e){noLauncher=true;}
    ok(noLauncher,"Launcher absent from classpath");
    KeyInfo info=new MagicLineKeyInfo(cert,key);
    KeyInfoSet keyset=new KeyInfoSet(info,info,random);
    ok(keyset.getSignatureKeyInfo().getPrivateKey()!=null && keyset.getEncipherKeyInfo().getPrivateKey()!=null,"original KeyInfoSet supplied without certificate UI");
    Credentials credentials=new Credentials("00000000",keyset.getSignatureKeyInfo().getX509Certificate(),keyset.getRandom());
    credentials.setAttribute("long-term","true");
    byte[] request=serialize(credentials);
    ok(request[0]==(byte)0xac && request[1]==(byte)0xed,"original Credentials Java serialization");
    JCAOSSecurityProvider provider=new JCAOSSecurityProvider();provider.init(new Properties());
    EnvelopedDataCipher envelope=provider.openEnvelopedDataCipher();envelope.initEncrypt(cert.getEncoded());
    byte[] encrypted=envelope.process(request);
    SecretKeyWithIV requestKey=envelope.getProcessingKey();
    EnvelopedDataCipher peer=provider.openEnvelopedDataCipher();peer.initDecrypt(cert.getEncoded(),pk8);
    byte[] recovered=peer.process(encrypted);
    ok(Arrays.equals(request,recovered),"original DDMD SEED envelope request roundtrip");
    Credentials parsed=(Credentials)deserialize(recovered);
    ok("00000000".equals(parsed.getYkiho()) && Arrays.equals(parsed.getRandom(),random),"synthetic peer recovered original Credentials");
    // Node provider also verifies the exact Java-emitted envelope offline in the fixture directory.
    Files.write(root.resolve("request.bin"),request);Files.write(root.resolve("request.cms"),encrypted);
    AuthToken token=new AuthToken("SYNTHETIC-NOT-A-SERVER-TOKEN",new Date(System.currentTimeMillis()+60000));
    byte[] response=serialize(token);
    DataSymmetricCipher encryptResponse=provider.openDataSymmetricCipher();encryptResponse.init(1,peer.getProcessingKey());
    byte[] responseWire=encryptResponse.cipher(response);
    DataSymmetricCipher decryptResponse=provider.openDataSymmetricCipher();decryptResponse.init(2,requestKey);
    AuthToken decoded=(AuthToken)deserialize(decryptResponse.cipher(responseWire));
    ok(decoded.getTokenId().equals(token.getTokenId()) && !decoded.isExpired(),"synthetic encrypted response recovered original AuthToken");
    AuthToken expired=new AuthToken("SYNTHETIC-EXPIRED",new Date(System.currentTimeMillis()-60000));
    ok(expired.isExpired(),"original token expiry detection");
    Date old=decoded.getExpired();decoded.updateExpiredTime(new AuthToken(token.getTokenId(),new Date(old.getTime()+60000)));
    ok(decoded.getExpired().after(old),"original token expiry extension using synthetic response");
    decoded.setAttribute("verifier",Base64.getEncoder().encodeToString(new byte[]{1,2,3}));
    decoded.setAttribute("digestAlgorithm","SHA-256");decoded.setAttribute("nonce",new byte[]{4,5});
    String verifier=decoded.updateAndGetVerifier(provider);
    // AuthToken concatenates nonce first, then decoded prior verifier (offsets 68..91).
    byte[] expectedVerifier=MessageDigest.getInstance("SHA-256").digest(new byte[]{4,5,1,2,3});
    ok(verifier!=null && Arrays.equals(Base64.getDecoder().decode(verifier),expectedVerifier),"original token verifier matches independent SHA-256 calculation");
    boolean malformed=false;try{peer.process(new byte[]{0,1,2});}catch(Exception e){malformed=true;}ok(malformed,"malformed envelope rejected without UI");
    ok(guard.blocked==expectedBlocks,"no unexpected network, process, native or AWT attempt");
    Arrays.fill(pk8,(byte)0);
    System.out.println("RESULT PASS checks="+passes+" actualServerAuthentication=false tokenIssuance=false");
  }
}
