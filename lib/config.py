import json
import os


def load_config(path):
    """Load configuration from a JSON file.

    Returns dict with 'credentials' and 'conf' keys.
    Injects 'dir' into conf as the directory of the config file.
    """
    with open(path, "r") as f:
        config = json.load(f)
    config["conf"]["dir"] = os.path.dirname(os.path.realpath(path))
    return config


def conf_get(conf, *keys):
    """Navigate nested dict keys, returning last valid value if key is missing.

    Mirrors the original HelloAsso.ConfGet behavior.
    """
    obj = conf
    for k in keys:
        try:
            obj = obj[k]
        except (IndexError, KeyError):
            return obj
        if not isinstance(obj, (dict, list)):
            break
    return obj
