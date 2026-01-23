from core.system.singleton import get_manager

def launch_system():
    """Return the shared manager (does not create a second instance)."""
    manager = get_manager()
    return manager