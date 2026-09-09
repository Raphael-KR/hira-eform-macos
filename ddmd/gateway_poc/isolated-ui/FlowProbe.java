import java.io.*;import java.nio.file.*;import java.lang.reflect.*;import java.util.*;
import hira.ddmd.jmc.client.presentation.controller.ntc.ReceiveController;
import hira.ddmd.jmc.client.presentation.controller.mng.SystemInfoController;
import hira.ddmd.jmc.client.model.dto.ResultDocument;
import hira.ddmd.jmc.client.dao.*;
public class FlowProbe {
 public static void main(String[] a)throws Exception{
  PrintStream report=System.out;System.setOut(new PrintStream(new OutputStream(){public void write(int b){}}));System.setErr(System.out);
  System.setProperty("client.home",a[0]);System.setProperty("resource.container","hira.ddmd.jmc.client.resources.ClientResourceContainer");if(System.getSecurityManager()==null)System.setSecurityManager(new GuiBootstrap.Guard(a[0]));
  try{
   ResultDocumentDAO dao=ClientDAOHolder.getResultDocumentDAO();ResultDocument key=new ResultDocument();key.setNtcDocId("ISOLATED-NOTICE-001");key.setYkiho("00000000");key.setDmdTpCd("0");ResultDocument d=dao.getResultDocument(key);
   if(d==null)throw new Exception("fixture absent");
   Path input=Paths.get(SystemInfoController.getNtcDirectoryPath(),d.getNtcDocId(),"zip",hira.ddmd.jmc.common.util.DocumentUtils.asFileName(d.getNtcDocId()));Files.createDirectories(input.getParent());Files.copy(Paths.get(a[0],"sam/out/ISOLATED-NOTICE-001/zip/ISOLATED-NOTICE-001"),input,StandardCopyOption.REPLACE_EXISTING);
   ReceiveController rc=new ReceiveController();org.apache.log4j.Logger.getLogger("NTC").setLevel(org.apache.log4j.Level.OFF);org.apache.log4j.Logger.getRootLogger().setLevel(org.apache.log4j.Level.OFF);Class<?> list=Class.forName("hira.ddmd.jmc.client.presentation.controller.ntc.ReceiveController$NtcGenResultList");Constructor<?> ct=list.getDeclaredConstructors()[0];ct.setAccessible(true);Object results=ct.newInstance(rc,Arrays.asList(d.getNtcDocId()));
   Method m=null;for(Method x:ReceiveController.class.getDeclaredMethods())if(x.getName().equals("zipReleaseCont"))m=x;m.setAccessible(true);
   Object ok=m.invoke(rc,null,d,false,null,results);
   report.println("CONTROLLER_GENERATE_RETURN="+ok);report.println("CONTROLLER_DB_STATE="+dao.getResultDocument(key).getNtcStatCd());report.println("CONTROLLER_FLOW_PASS");System.exit(0);
  }catch(Throwable e){while(e instanceof InvocationTargetException)e=((InvocationTargetException)e).getTargetException();report.println("CONTROLLER_FLOW_FAIL="+e.getClass().getName()+":"+e.getMessage());for(Throwable c=e.getCause();c!=null;c=c.getCause()){report.println("CAUSE="+c.getClass().getName()+":"+c.getMessage());for(StackTraceElement x:c.getStackTrace())report.println(x.toString());}for(StackTraceElement x:e.getStackTrace())report.println(x.toString());System.exit(1);}
 }
}
