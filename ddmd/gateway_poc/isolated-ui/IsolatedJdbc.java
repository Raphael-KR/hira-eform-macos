import java.sql.*;import java.util.*;
public class IsolatedJdbc extends org.sqlite.JDBC {
 static {try{DriverManager.registerDriver(new IsolatedJdbc());}catch(SQLException e){throw new RuntimeException(e);}}
 public boolean acceptsURL(String u){return u.startsWith("jdbc:isolated-sqlite:");}
 public Connection connect(String u,Properties p)throws SQLException{
  if(!acceptsURL(u))return null;
  Connection c=super.connect(u.replace("jdbc:isolated-sqlite:","jdbc:sqlite:"),p);
  try(Statement s=c.createStatement()){s.execute("PRAGMA temp_store=MEMORY");}catch(SQLException e){c.close();throw e;}
  System.err.println("ISOLATED_JDBC_MEMORY_TEMP_READY");return c;
 }
}
