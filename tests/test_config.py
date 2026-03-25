import os

from lib.config import load_config


def test_load_config_returns_credentials_and_conf(config_file):
    config = load_config(config_file)
    assert "credentials" in config
    assert "conf" in config
    assert config["credentials"]["helloasso"]["id"] == "test-client-id"


def test_load_config_injects_dir(config_file):
    config = load_config(config_file)
    expected_dir = os.path.dirname(os.path.realpath(config_file))
    assert config["conf"]["dir"] == expected_dir


def test_conf_get_navigates_nested_keys(sample_config):
    from lib.config import conf_get
    result = conf_get(sample_config["conf"], "helloasso", "api_url")
    assert result == "https://api.helloasso.com"


def test_conf_get_returns_last_valid_on_missing_key(sample_config):
    from lib.config import conf_get
    # When a key doesn't exist, returns the last valid value before the missing key
    result = conf_get(sample_config["conf"], "helloasso", "nonexistent_key")
    assert result == sample_config["conf"]["helloasso"]
