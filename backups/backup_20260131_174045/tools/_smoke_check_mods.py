from core.sensors import sensor_aliases
from core.context import fallback_universal
from core.indices import environmental_indices

print('SENSOR_ALIASES contains sensacion_calor:', 'sensacion_calor' in sensor_aliases.SENSOR_ALIASES)
print('CASCADA_SATURACION:', fallback_universal.CascadaDegradacion.CASCADA_SATURACION)
print('EnvironmentalIndices present:', hasattr(environmental_indices, 'EnvironmentalIndices'))

# Instantiate EnvironmentalIndices minimally if possible
try:
    ei = environmental_indices.EnvironmentalIndices(None)
    print('EnvironmentalIndices OK')
except Exception as e:
    print('EnvironmentalIndices init error:', e)
