import logging
#!/usr/bin/env python3
"""Genera un passwordfile para Mosquitto usando bcrypt y adapta el prefijo a $2y$.
Escribe también la contraseña en `scripts/generated_password.txt`.

Uso: python scripts/fix_passwordfile.py --user meteoser --out "C:\\mosquitto\\conf\\passwordfile"
"""
import argparse
import os
import secrets
import subprocess
import sys

def ensure_bcrypt():
    try:
        import bcrypt  # type: ignore
        return bcrypt
    except Exception:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "bcrypt"])
        import bcrypt  # type: ignore
        return bcrypt

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--user', default='meteoser')
    p.add_argument('--out', default=r'C:\mosquitto\conf\passwordfile')
    p.add_argument('--plainfile', default=os.path.join('scripts','generated_password.txt'))
    p.add_argument('--password')
    args = p.parse_args()

    bcrypt = ensure_bcrypt()

    password = args.password or secrets.token_urlsafe(16)

    # Create parent dir if needed
    outdir = os.path.dirname(args.out)
    if outdir and not os.path.exists(outdir):
        os.makedirs(outdir, exist_ok=True)

    # Generate bcrypt hash and convert $2b$ -> $2y$ for Mosquitto compatibility
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
    if hashed.startswith('$2b$'):
        hashed = '$2y$' + hashed[4:]

    line = f"{args.user}:{hashed}\n"

    # Write atomically
    tmp = args.out + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        fh.write(line)
    os.replace(tmp, args.out)

    # Save plaintext password for admin (restrict permissions if possible)
    plainpath = args.plainfile
    plain_dir = os.path.dirname(plainpath)
    if plain_dir and not os.path.exists(plain_dir):
        os.makedirs(plain_dir, exist_ok=True)
    with open(plainpath, 'w', encoding='utf-8') as ph:
        ph.write(password + '\n')

    try:
        # Attempt to tighten permissions on the generated files (Windows: use icacls)
        if os.name == 'nt':
            subprocess.call(['icacls', args.out, '/inheritance:r'])
            subprocess.call(['icacls', args.out, '/grant', 'SYSTEM:R'])
            subprocess.call(['icacls', plainpath, '/inheritance:r'])
            subprocess.call(['icacls', plainpath, '/grant', 'SYSTEM:R'])
    except Exception:
        logging.exception("Silent except at 67 - revisar contexto")

    print(f'Wrote passwordfile: {args.out}')
    print(f'Wrote plaintext password: {plainpath}')

if __name__ == '__main__':
    main()
