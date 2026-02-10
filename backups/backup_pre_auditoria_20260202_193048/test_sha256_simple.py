"""Test rápido de SHA256"""
import sys
sys.path.insert(0, 'C:/Users/kioko/Desktop/MeteoSerV3')

from protocolo_certificacion_arranque_v26 import ProtocoloCertificacionV26

protocolo = ProtocoloCertificacionV26()
resultado = protocolo.verificar_integridad_sha256()

print(f"\nModulos verificados: {len(resultado['hashes_modulos'])}")
print(f"Integridad valida: {resultado['integridad_valida']}")

if resultado['integridad_valida']:
    print("RESULTADO: SHA256 VALIDO - VERDE")
else:
    print("RESULTADO: SHA256 INVALIDO - ROJO")
    print("\nDetalles:")
    for modulo, hash_val in resultado['hashes_modulos'].items():
        if hash_val is None:
            print(f"  - {modulo}: NO ENCONTRADO")
        else:
            print(f"  - {modulo}: OK")
