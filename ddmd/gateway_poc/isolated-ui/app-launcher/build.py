from pathlib import Path
import json,plistlib,subprocess,zipfile,argparse
parser=argparse.ArgumentParser()
parser.add_argument('--home',required=True)
parser.add_argument('--bundle-id',default='local.hira.ddmd.isolated')
options=parser.parse_args()
home=Path(options.home).resolve();app=home/'DDMD Computer Use.app';mac=app/'Contents/MacOS';mac.mkdir(parents=True,exist_ok=True)
cmd=json.loads((home/'gui-command.json').read_text());j=Path(cmd[0]).parents[1];lib=j/'jre/lib/jli/libjli.dylib'
# Compile the isolated adapters with the same Java 8 runtime used by the app.
sources=Path(__file__).resolve().parent.parent
subprocess.run([str(j/'bin/javac'),'-XDignore.symbol.file','-cp',str(home/'data/bootstrap.jar'),
 '-d',str(home/'probe'),str(sources/'GuiBootstrap.java'),str(sources/'SamViewArgumentsAgent.java')],check=True)
agent=home/'samview-arguments-agent.jar'
with zipfile.ZipFile(agent,'w') as archive:
 archive.writestr('META-INF/MANIFEST.MF','Manifest-Version: 1.0\nPremain-Class: SamViewArgumentsAgent\n\n')
 for compiled in (home/'probe').glob('SamViewArgumentsAgent*.class'):
  archive.write(compiled,compiled.name)
agent_option='-javaagent:'+str(agent)
if agent_option not in cmd:cmd.insert(1,agent_option)
# Keep JVM in the application process so Launch Services and the UI agree on identity.
s='''#import <Foundation/Foundation.h>
#include <dlfcn.h>
#include <stdio.h>
#include <unistd.h>
#include <pthread.h>
#include <string.h>
typedef int (*Launch)(int,char**,int,const char**,int,const char**,const char*,const char*,const char*,const char*,unsigned char,unsigned char,unsigned char,int);
static void *show_when_ready(void *ignored){
 for(int i=0;i<300;i++){
  FILE *f=fopen(LOG_PATH,"r");int ready=0;
  if(f){char line[8192];while(fgets(line,sizeof(line),f))if(strstr(line,"Application started"))ready=1;fclose(f);}
  if(ready){ FILE *request=fopen("work/in/cmd_app_show","w");if(!request)return NULL;
 fputs("command = showpanel\\narguments = standalone\\n",request);fclose(request);
 FILE *marker=fopen("work/in/cmd_app_show.end","w");if(!marker)return NULL;fclose(marker);
 return NULL;}usleep(100000);
 }fprintf(stderr,"APP_SHOW_TIMEOUT\\n");return NULL;
}
int main(int argc,char **argv){@autoreleasepool {
 chdir(HOME_PATH);
 FILE *pidFile=fopen("native-app.pid","w");if(pidFile){fprintf(pidFile,"%d\\n",getpid());fclose(pidFile);}
 freopen(LOG_PATH,"w",stdout);freopen(LOG_PATH,"a",stderr);
 pthread_t readyThread;pthread_create(&readyThread,NULL,show_when_ready,NULL);pthread_detach(readyThread);
 fprintf(stderr,"NATIVE_BUNDLE=%s\\n",[[[NSBundle mainBundle] bundleIdentifier] UTF8String]);
 void *lib=dlopen(LIB_PATH,RTLD_NOW|RTLD_GLOBAL);if(!lib){fprintf(stderr,"DLOPEN=%s\\n",dlerror());return 2;}
 Launch launch=(Launch)dlsym(lib,"JLI_Launch");if(!launch)return 3;
 char *args[]={ARGS};
 return launch(sizeof(args)/sizeof(args[0]),args,0,NULL,0,NULL,"1.8.0_504","1.8","java","openjdk",0,1,0,0);
}}
'''
for key,val in [('HOME_PATH',str(home)),('LOG_PATH',str(home/'gui-app-bundle.log')),('LIB_PATH',str(lib))]:s=s.replace(key,json.dumps(val))
s=s.replace('ARGS',','.join(json.dumps(x) for x in cmd));source=home/'launcher.m';source.write_text(s)
subprocess.run(['xcrun','clang','-framework','Foundation',str(source),'-o',str(mac/'DDMDTrial')],check=True)
d={'CFBundleIdentifier':options.bundle_id,'CFBundleName':'DDMD Computer Use','CFBundleDisplayName':'DDMD Computer Use','CFBundleExecutable':'DDMDTrial','CFBundlePackageType':'APPL','CFBundleVersion':'1','NSHighResolutionCapable':True}
(app/'Contents/Info.plist').write_bytes(plistlib.dumps(d));subprocess.run(['codesign','--force','--sign','-',str(app)],check=True)
print(app)
