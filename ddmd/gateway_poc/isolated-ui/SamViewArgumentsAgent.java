import java.lang.instrument.*;
import java.security.ProtectionDomain;
import jdk.internal.org.objectweb.asm.*;

/** Java 8-only isolated adapter: preserve original JAR bytes and fallback value. */
public class SamViewArgumentsAgent {
 public static void premain(String args, Instrumentation instrumentation) {
  instrumentation.addTransformer(new ClassFileTransformer() {
   public byte[] transform(ClassLoader loader, String name, Class<?> type,
       ProtectionDomain domain, byte[] bytes) {
    if (!"hira/ddmd/jmc/client/presentation/controller/samview/ViewSAMFileController".equals(name)) return null;
    ClassReader reader = new ClassReader(bytes);
    ClassWriter writer = new ClassWriter(reader, ClassWriter.COMPUTE_MAXS);
    reader.accept(new ClassVisitor(Opcodes.ASM5, writer) {
     public MethodVisitor visitMethod(int access, String name, String desc, String signature, String[] exceptions) {
      MethodVisitor original = super.visitMethod(access, name, desc, signature, exceptions);
      if (!name.equals("main") || !desc.equals("([Ljava/lang/String;)V")) return original;
      return new MethodVisitor(Opcodes.ASM5, original) {
       public void visitCode() {
        super.visitCode();
        // Helper preserves supplied arguments; only absent arguments use original fallback.
        super.visitVarInsn(Opcodes.ALOAD, 0);
        super.visitMethodInsn(Opcodes.INVOKESTATIC, "SamViewArgumentsAgent", "normalize", "([Ljava/lang/String;)[Ljava/lang/String;", false);
        super.visitVarInsn(Opcodes.ASTORE, 0);
       }
      };
     }
    }, 0);
    System.out.println("SAMVIEW_ARGUMENT_ADAPTER_INSTALLED");
    return writer.toByteArray();
   }
  });
 }
 public static String[] normalize(String[] args) {
  return args == null || args.length == 0 ? new String[]{"0"} : args;
 }
}
