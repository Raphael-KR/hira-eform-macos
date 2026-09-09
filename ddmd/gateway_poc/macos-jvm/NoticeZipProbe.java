import java.io.*;
import hira.ddmd.jmc.common.util.Commons;
public class NoticeZipProbe {
 public static void main(String[] a)throws Exception {
  PrintStream report=System.out;System.setOut(new PrintStream(new OutputStream(){public void write(int b){}}));System.setErr(System.out);
  org.apache.log4j.LogManager.resetConfiguration();org.apache.log4j.Logger.getRootLogger().setLevel(org.apache.log4j.Level.OFF);
  try{File[] files=Commons.decompress(new File(a[0]),new File(a[1]));long bytes=0;for(File f:files)bytes+=f.length();report.println("RESULT DDMD_DECOMPRESS_PASS files="+files.length+" bytes="+bytes);}catch(Throwable e){report.println("RESULT FAILED class="+e.getClass().getName());System.exit(1);}
 }
}
