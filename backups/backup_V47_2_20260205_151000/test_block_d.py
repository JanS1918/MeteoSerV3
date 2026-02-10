"""
Lanzador profesional para el smoke_test de meteoser_ia.block_d
Permite ejecutar el test sin modificar imports ni lógica interna del paquete.
"""
import sys
import os

# Añadir la raíz del proyecto y meteoser_ia al sys.path
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
IA_DIR = os.path.join(ROOT, "meteoser_ia")
if IA_DIR not in sys.path:
    sys.path.insert(0, IA_DIR)

from meteoser_ia import block_d

if __name__ == "__main__":
    block_d.smoke_test()
