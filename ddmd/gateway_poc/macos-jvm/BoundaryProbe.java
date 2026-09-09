import java.sql.*;
import java.security.*;
public class BoundaryProbe {
 static class Guard extends SecurityManager {
  public void checkPermission(Permission p) {if(p instanceof RuntimePermission && p.getName().equals("setSecurityManager"))throw new SecurityException("guard removal");}
  public void checkConnect(String h,int p){throw new SecurityException("network disabled");}
  public void checkExec(String s){throw new SecurityException("process disabled");}
 }
 static void result(String label,Throwable e){System.out.println("BOUNDARY "+label+" "+e.getClass().getName());for(int i=0;e!=null&&i<4;i++,e=e.getCause()){System.out.println("CAUSE "+e.getClass().getName()+" "+e.getMessage());for(StackTraceElement f:e.getStackTrace())if(f.getClassName().startsWith("hira.")||f.getClassName().startsWith("BoundaryProbe"))System.out.println("FRAME "+f.getClassName()+"."+f.getMethodName()+":"+f.getLineNumber());}}
 public static void main(String[] a)throws Exception {
  System.setSecurityManager(new Guard());
  try{Class.forName("org.sqlite.JDBC");try(Connection c=DriverManager.getConnection("jdbc:sqlite::memory:")){c.createStatement().execute("select 1");System.out.println("BOUNDARY originalSqlite PASS");}}catch(Throwable e){result("originalSqlite",e);}
  for(String n:new String[]{"hira.ddmd.jmc.client.presentation.Launcher","hira.ddmd.jmc.client.presentation.controller.exam.CExamController","hira.ddmd.jmc.client.presentation.controller.exam.CExamChineseSpec091"})try{Class.forName(n);System.out.println("BOUNDARY "+n+" INITIALIZED_ONLY");}catch(Throwable e){result(n,e);}
 }
}
