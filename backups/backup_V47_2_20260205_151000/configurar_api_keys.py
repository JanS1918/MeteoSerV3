"""
Script de configuración de API Keys para MeteoSer
Guarda todas las claves de forma cifrada y permanente
"""
import os
import sys
from pathlib import Path

# Añadir el directorio raíz al path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from core.config.secrets_vault import get_vault
from meteoser_ia.block_e import SECRETS_MANAGER
from cryptography.fernet import Fernet

def print_banner():
    print("\n" + "="*70)
    print("  CONFIGURACIÓN DE API KEYS - METEOSER v3")
    print("  Sistema de almacenamiento cifrado y permanente")
    print("="*70 + "\n")

def configure_master_key():
    """Configura o carga la clave maestra para cifrado"""
    print("📌 CONFIGURACIÓN DE CLAVE MAESTRA")
    print("-" * 70)
    
    master_key_file = Path(ROOT_DIR) / "meteoser_ia" / "ia_security" / "master.key"
    master_key_file.parent.mkdir(parents=True, exist_ok=True)
    
    if master_key_file.exists():
        print("✓ Clave maestra encontrada en disco")
        with open(master_key_file, "rb") as f:
            master_key = f.read()
    else:
        print("⚠ No se encontró clave maestra. Generando nueva...")
        master_key = Fernet.generate_key()
        with open(master_key_file, "wb") as f:
            f.write(master_key)
        # Permisos restrictivos en Windows (solo lectura para el propietario)
        try:
            os.chmod(master_key_file, 0o600)
        except:
            pass
        print(f"✓ Clave maestra generada y guardada en: {master_key_file}")
        print("  ⚠ IMPORTANTE: Haz backup de este archivo. Sin él, no podrás recuperar las claves.")
    
    # Configurar en el SecretsManager
    SECRETS_MANAGER.set_master_key(master_key)
    
    # Intentar cargar secretos existentes
    try:
        SECRETS_MANAGER.load_from_disk()
        print("✓ Secretos existentes cargados desde disco\n")
    except Exception as e:
        print(f"ℹ No hay secretos previos (esto es normal en la primera ejecución)\n")
    
    return True

def configure_openrouter():
    """Configura la API key de OpenRouter"""
    print("\n📌 OPENROUTER API KEY (usada por IA de MeteoSer)")
    print("-" * 70)
    
    vault = get_vault()
    current = vault.get_openrouter_key()
    
    if current:
        print(f"✓ Ya existe una clave configurada: {current[:20]}...")
        replace = input("¿Quieres reemplazarla? (s/N): ").strip().lower()
        if replace != 's':
            print("  Manteniendo clave actual\n")
            return current
    
    print("\n  Obtén tu clave en: https://openrouter.ai/keys")
    key = input("  Introduce tu API key de OpenRouter: ").strip()
    
    if not key:
        print("  ⚠ No se introdujo ninguna clave\n")
        return None
    
    if vault.set_openrouter_key(key):
        print("  ✓ Clave guardada de forma segura y cifrada\n")
        return key
    else:
        print("  ✗ Error al guardar la clave\n")
        return None

def configure_srtm():
    """Configura la API key de SRTM (opcional)"""
    print("\n📌 SRTM API KEY (elevación - OPCIONAL)")
    print("-" * 70)
    
    vault = get_vault()
    current = vault.get_srtm_key()
    
    if current:
        print(f"✓ Ya existe una clave configurada: {current[:20]}...")
        replace = input("¿Quieres reemplazarla? (s/N): ").strip().lower()
        if replace != 's':
            print("  Manteniendo clave actual\n")
            return current
    
    print("\n  Si usas un servicio de elevación que requiere API key, introdúcela aquí.")
    print("  Si usas el servicio gratuito open-elevation.com, puedes dejarlo en blanco.")
    key = input("  API key de SRTM (Enter para omitir): ").strip()
    
    if not key:
        print("  ℹ Sin clave SRTM (usarás servicio gratuito)\n")
        return None
    
    if vault.set_srtm_key(key):
        print("  ✓ Clave guardada de forma segura y cifrada\n")
        return key
    else:
        print("  ✗ Error al guardar la clave\n")
        return None

def configure_openweather():
    """Configura la API key de OpenWeather (opcional)"""
    print("\n📌 OPENWEATHER API KEY (OPCIONAL)")
    print("-" * 70)
    
    vault = get_vault()
    current = vault.get_openweather_key()
    
    if current:
        print(f"✓ Ya existe una clave configurada: {current[:20]}...")
        replace = input("¿Quieres reemplazarla? (s/N): ").strip().lower()
        if replace != 's':
            print("  Manteniendo clave actual\n")
            return current
    
    print("\n  Obtén tu clave en: https://openweathermap.org/api")
    key = input("  API key de OpenWeather (Enter para omitir): ").strip()
    
    if not key:
        print("  ℹ Sin clave OpenWeather\n")
        return None
    
    if vault.set_openweather_key(key):
        print("  ✓ Clave guardada de forma segura y cifrada\n")
        return key
    else:
        print("  ✗ Error al guardar la clave\n")
        return None

def show_summary(keys_configured):
    """Muestra un resumen de las claves configuradas"""
    print("\n" + "="*70)
    print("  RESUMEN DE CONFIGURACIÓN")
    print("="*70)
    
    vault = get_vault()
    
    configs = [
        ("OpenRouter (IA)", vault.get_openrouter_key()),
        ("SRTM (Elevación)", vault.get_srtm_key()),
        ("OpenWeather", vault.get_openweather_key()),
    ]
    
    for name, key in configs:
        status = "✓ CONFIGURADA" if key else "✗ No configurada"
        print(f"  {name:25} {status}")
    
    print("\n" + "="*70)
    print("  ARCHIVOS GENERADOS:")
    print("="*70)
    
    security_dir = Path(ROOT_DIR) / "meteoser_ia" / "ia_security"
    
    files = [
        ("Clave maestra", security_dir / "master.key"),
        ("Secretos cifrados", security_dir / "secrets.enc"),
    ]
    
    for name, path in files:
        if path.exists():
            print(f"  ✓ {name:25} → {path}")
        else:
            print(f"  ℹ {name:25} → (se creará al guardar)")
    
    print("\n" + "="*70)
    print("  ⚠ IMPORTANTE:")
    print("  - Haz BACKUP del archivo master.key")
    print("  - Sin él, NO podrás recuperar las claves guardadas")
    print("  - Las claves están CIFRADAS y son PERSISTENTES")
    print("  - Todos los componentes de MeteoSer usarán estas claves automáticamente")
    print("="*70 + "\n")

def main():
    """Función principal del configurador"""
    try:
        print_banner()
        
        # Paso 1: Configurar clave maestra
        if not configure_master_key():
            print("✗ Error al configurar la clave maestra")
            return 1
        
        # Paso 2: Configurar API keys
        keys_configured = []
        
        openrouter_key = configure_openrouter()
        if openrouter_key:
            keys_configured.append("OpenRouter")
        
        srtm_key = configure_srtm()
        if srtm_key:
            keys_configured.append("SRTM")
        
        openweather_key = configure_openweather()
        if openweather_key:
            keys_configured.append("OpenWeather")
        
        # Mostrar resumen
        show_summary(keys_configured)
        
        if not keys_configured:
            print("⚠ No se configuró ninguna clave API")
            return 1
        
        print("✓ Configuración completada exitosamente\n")
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠ Configuración cancelada por el usuario\n")
        return 1
    except Exception as e:
        print(f"\n✗ Error durante la configuración: {e}\n")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
