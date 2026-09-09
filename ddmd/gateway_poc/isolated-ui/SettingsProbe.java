import hira.ddmd.jmc.client.presentation.controller.mng.SystemInfoController;
public class SettingsProbe {
 public static void main(String[] a)throws Exception{
  String h=a[0];System.setProperty("client.home",h);System.setSecurityManager(new GuiBootstrap.Guard(h));
  if(a[1].equals("save"))SystemInfoController.saveProperties("00000000",h+"/sam/in",h+"/sam/out",3,false,true);
  if(!SystemInfoController.getYkiho().equals("00000000"))throw new Exception("ykiho persistence");
  if(!SystemInfoController.getDmdIfDirectoryPath().equals(h+"/sam/in"))throw new Exception("input path persistence");
  if(!SystemInfoController.getNtcIfDirectoryPath().equals(h+"/sam/out"))throw new Exception("output path persistence");
  if(SystemInfoController.getBackupMonth()!=3||!SystemInfoController.isSecurityEnable())throw new Exception("options persistence");
  System.out.println("SETTINGS_"+a[1].toUpperCase()+"_PASS");
 }
}
