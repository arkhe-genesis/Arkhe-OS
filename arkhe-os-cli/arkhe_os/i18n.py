import gettext
import os
import json

CONFIG_FILE = os.path.expanduser("~/.arkhe_config.json")
LOCALES_DIR = os.path.join(os.path.dirname(__file__), "locales")

def get_locale():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                return config.get("locale", "pt_BR")
        except Exception:
            return "pt_BR"
    return "pt_BR"

def set_locale(locale):
    locale = locale.replace('-', '_')
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
        except Exception:
            pass
    config["locale"] = locale
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def get_translator():
    locale = get_locale().replace('-', '_')
    try:
        lang = gettext.translation('arkhe', localedir=LOCALES_DIR, languages=[locale])
        return lang.gettext
    except FileNotFoundError:
        return gettext.gettext
