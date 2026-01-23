from core.system.system_core import SystemCore

s = SystemCore()
print('System EWMA state present:', isinstance(getattr(s, '_sensor_ewma_state', None), dict))
