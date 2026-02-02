#!/usr/bin/env python3
"""
Genera un passwordfile para Mosquitto usando bcrypt y lo instala en C:\mosquitto\conf\passwordfile

Uso (PowerShell elevado, desde la raíz del proyecto):
  python .\scripts\generate_passwordfile_py.py

El script intentará instalar 'bcrypt' si no está disponible.
"""
import os
import sys
import subprocess

CONF_DIR = r"C:\mosquitto\conf"
PW_GENERATED = os.path.join(CONF_DIR, "generated_password.txt")
PW_FILE = os.path.join(CONF_DIR, "passwordfile")
NSSM = os.path.join(os.path.dirname(__file__), '..', 'tools', 'nssm', 'nssm-2.24', 'win64', 'nssm.exe')

def ensure_bcrypt():
    try:
        import bcrypt
        return bcrypt
    except Exception:
        print("bcrypt no encontrado. Intentando instalarlo con pip...")
        cmd = [sys.executable, '-m', 'pip', 'install', 'bcrypt']
        r = subprocess.run(cmd)
        if r.returncode != 0:
            print("Error instalando bcrypt. Ejecuta: python -m pip install bcrypt")
            sys.exit(1)
        import bcrypt
        return bcrypt

def read_password():
    if os.path.exists(PW_GENERATED):
        with open(PW_GENERATED, 'r', encoding='utf-8') as f:
            return f.read().strip()
    # generar uno si no existe
    import base64, secrets
    pw = base64.b64encode(secrets.token_bytes(18)).decode('ascii')
    os.makedirs(CONF_DIR, exist_ok=True)
    with open(PW_GENERATED, 'w', encoding='ascii') as f:
        f.write(pw)
    return pw

def write_passwordfile(bcrypt, pw):
    hashed = bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt())
    line = f"meteoser:{hashed.decode('utf-8')}\n"
    tmp = PW_FILE + ".tmp"
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(line)
    os.replace(tmp, PW_FILE)
    print(f"Wrote {PW_FILE}")

def set_acls():
    icacls = os.path.join(os.environ.get('SystemRoot','C:\\Windows'), 'System32', 'icacls.exe')
    cmds = [
        [icacls, PW_FILE, '/grant', 'NT AUTHORITY\\SYSTEM:F', '/grant', 'BUILTIN\\Administradores:F', '/grant', 'BUILTIN\\Usuarios:M'],
        [icacls, 'C:\\mosquitto', '/grant', 'NT AUTHORITY\\SYSTEM:(OI)(CI)F', '/grant', 'BUILTIN\\Administradores:(OI)(CI)F', '/grant', 'BUILTIN\\Usuarios:(OI)(CI)M', '/T']
    ]
    for cmd in cmds:
        subprocess.run(cmd)

def restart_service():
    nssm_path = os.path.abspath(NSSM)
    if not os.path.exists(nssm_path):
        print(f"nssm no encontrado en {nssm_path}. Reinicia el servicio manualmente.")
        return
    subprocess.run([nssm_path, 'restart', 'MeteoSerMosquitto'])

def main():
    if not os.name == 'nt':
        print('Este script está diseñado para Windows.')
        sys.exit(1)
    bcrypt = ensure_bcrypt()
    pw = read_password()
    print('Using password from', PW_GENERATED)
    write_passwordfile(bcrypt, pw)
    set_acls()
    restart_service()
    print('Hecho. Comprueba estado del servicio y logs.')

if __name__ == '__main__':
    main()
