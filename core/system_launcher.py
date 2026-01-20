from .system_manager import SystemManager


def launch_system():
    manager = SystemManager()
    manager.start()
    return manager
