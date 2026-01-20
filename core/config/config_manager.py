from ..utils import safe_get


class ConfigManager:
    def __init__(self, config):
        self.config = config

    def get(self, key, default=None):
        return safe_get(self.config, key, default)
