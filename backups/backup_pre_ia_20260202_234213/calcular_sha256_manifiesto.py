#!/usr/bin/env python3
"""Script para calcular SHA256 correcto del MANIFIESTO_PREDICCIONES_V20"""
import sys
sys.path.insert(0, '.')

import json
import hashlib
from core.indices.environmental_indices import MANIFIESTO_PREDICCIONES_V20

payload = json.dumps(MANIFIESTO_PREDICCIONES_V20, ensure_ascii=False, sort_keys=True)
sha256_correcto = hashlib.sha256(payload.encode("utf-8")).hexdigest()

print(f"SHA256 correcto: {sha256_correcto}")
