import hira.ddmd.jmc.client.presentation.controller.mod.UpdController;
import hira.ddmd.jmc.client.presentation.form.mod.UpdateDialog;
public class ApplyUpdateProbe {
 public static void main(String[] args)throws Exception {
  UpdateDialog dialog=new UpdateDialog(null);
  UpdController.getInstance().updateModules(dialog);
  dialog.dispose();System.out.println("UPDATE_APPLY_RETURNED");System.exit(0);
 }
}
