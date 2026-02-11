def test_config_manager_import():
    import core.config.config_manager as m

    assert hasattr(m, "ConfigManager")
