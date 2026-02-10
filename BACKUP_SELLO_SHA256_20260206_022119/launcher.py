#!/usr/bin/env python
"""Wrapper para iniciar main_asgi.py con buffering deshabilitado"""

import subprocess
import sys
import os

os.chdir(r'c:\Users\kioko\Desktop\MeteoSerV3')

# Ejecutar con buffering deshabilitado
proc = subprocess.Popen(
    [sys.executable, 'main_asgi.py'],
    stdout=sys.stdout,
    stderr=sys.stderr,
    bufsize=0,  # Sin buffering
    text=True
)

try:
    proc.wait()
except KeyboardInterrupt:
    proc.terminate()
    proc.wait()
