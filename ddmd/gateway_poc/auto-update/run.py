#!/usr/bin/env python3
"""Run with machine-local configuration, excluded from Git."""
from pathlib import Path
import json,subprocess,sys
here=Path(__file__).resolve().parent
repo=here.parents[2]
root=repo/'.local/ddmd'
config=json.loads((root/'config.json').read_text())
subprocess.run([sys.executable,str(here/'auto_update.py'),'--root',str(root),'--source',config['source'],'--institution',str(root/'institution.txt'),'--java',config['java']],check=True)
