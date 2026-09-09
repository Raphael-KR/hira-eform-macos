import java.io.*;import java.sql.*;
public class VacuumProbe {
 public static void main(String[] a)throws Exception{
  System.setSecurityManager(new GuiBootstrap.Guard(a[0]));
  Class.forName("org.sqlite.JDBC");
  try(Connection c=DriverManager.getConnection("jdbc:sqlite:"+a[0]+"/data/ddmd_data.db3"+(a[1].equals("url")?"?temp_store=MEMORY":""))){
   if(a[1].equals("memory"))c.createStatement().execute("PRAGMA temp_store=MEMORY");
   c.createStatement().execute("VACUUM");
   System.out.println("VACUUM_PASS");
  }
 }
}
