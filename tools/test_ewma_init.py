from core.indices.environmental_indices import EnvironmentalIndices
from core.system.system_core import SystemCore
s=SystemCore()
e=EnvironmentalIndices(s)
print('EWMA loaded', isinstance(e._ewma_state, dict), e._ewma_state)
