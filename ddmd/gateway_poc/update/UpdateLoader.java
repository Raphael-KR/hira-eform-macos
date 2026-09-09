import java.lang.reflect.*;
public class UpdateLoader {
 public static void main(String[] a)throws Exception{
  System.setProperty("client.home",a[0]);System.setProperty("resource.container","hira.ddmd.jmc.client.resources.ClientResourceContainer");System.setSecurityManager(new GuiBootstrap.Guard(a[0]));
  GuiBootstrap.normalizeDesktopHints();Class<?> b=hira.ddmd.jmc.client.ApplicationBootstrap.class;Object o=b.newInstance();Method shared=b.getDeclaredMethod("createSharedClassLoader");shared.setAccessible(true);ClassLoader s=(ClassLoader)shared.invoke(o);Method app=b.getDeclaredMethod("createClassLoader",ClassLoader.class);app.setAccessible(true);ClassLoader c=(ClassLoader)app.invoke(o,s);Thread.currentThread().setContextClassLoader(c);c.loadClass("ApplyUpdateProbe").getMethod("main",String[].class).invoke(null,(Object)a);
 }
}
