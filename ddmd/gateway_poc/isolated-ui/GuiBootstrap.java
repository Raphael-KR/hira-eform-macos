import java.security.*;import java.io.*;
public class GuiBootstrap {
 static class Guard extends SecurityManager {
  final String home;Guard(String h){home=h+File.separator;}
  public void checkPermission(Permission p){if(p instanceof RuntimePermission&&p.getName().equals("setSecurityManager"))throw new SecurityException("guard removal");}
  public void checkConnect(String h,int p){throw new SecurityException("isolated network denied");}
  public void checkExec(String s){throw new SecurityException("isolated process denied");}
  public void checkWrite(String f){String p=new File(f).getAbsolutePath();if(!p.startsWith(home))throw new SecurityException("outside trial write denied: "+p);}
  public void checkDelete(String f){checkWrite(f);}
 }
 // JIDE 2.11.2 casts this Map to RenderingHints during static initialization.
 // Normalize only this JVM's cached value; leave the original JAR and OS intact.
 static void normalizeDesktopHints() throws Exception {
  if (!System.getProperty("os.name", "").startsWith("Mac")) return;
  java.awt.Toolkit toolkit = java.awt.Toolkit.getDefaultToolkit();
  String key = "awt.font.desktophints";
  Object value = toolkit.getDesktopProperty(key);
  if (value instanceof java.util.Map && !(value instanceof java.awt.RenderingHints)) {
   java.awt.RenderingHints hints = new java.awt.RenderingHints(null);
   hints.putAll((java.util.Map<?, ?>) value);
   java.lang.reflect.Method setter = java.awt.Toolkit.class.getDeclaredMethod(
       "setDesktopProperty", String.class, Object.class);
   setter.setAccessible(true);
   setter.invoke(toolkit, key, hints);
   if (!(toolkit.getDesktopProperty(key) instanceof java.awt.RenderingHints))
    throw new IllegalStateException("Desktop hints normalization failed");
   System.out.println("JIDE_HINTS_NORMALIZED=" + value.getClass().getName());
  }
 }
 public static void main(String[] a)throws Exception {System.setSecurityManager(new Guard(System.getProperty("client.home")));normalizeDesktopHints();hira.ddmd.jmc.client.ApplicationBootstrap.main(new String[]{"start"});}
}
