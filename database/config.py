"""
config.py — Gestión centralizada de configuración del sistema.
Lee y escribe en config.json en la raíz del proyecto.
"""
import json
import os

CONFIG_FILE = "config.json"

DEFAULTS = {
    "pharmacy": {
        "name":      "FarmaFactura Pro",
        "address":   "",
        "phone":     "",
        "rnc":       "",
        "logo_path": ""
    },
    "billing": {
        "footer":    "Gracias por su compra. ¡Vuelva pronto!",
        "currency":  "RD$",
        "tax_rate":  18.0
    },
    "inventory": {
        "low_stock_threshold": 10,
        "expiry_alert_days":   30
    },
    "notifications": {
        "alert_low_stock": True,
        "alert_expiry":    True
    }
}


def load() -> dict:
    """Carga la configuración. Si no existe el archivo, devuelve los valores por defecto."""
    if not os.path.exists(CONFIG_FILE):
        return json.loads(json.dumps(DEFAULTS))   # deep copy
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Mezclar con defaults para cubrir claves nuevas
        for section, values in DEFAULTS.items():
            if section not in data:
                data[section] = values
            else:
                for key, val in values.items():
                    if key not in data[section]:
                        data[section][key] = val
        return data
    except Exception:
        return json.loads(json.dumps(DEFAULTS))


def save(data: dict) -> bool:
    """Guarda la configuración en config.json."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error al guardar config: {e}")
        return False


def get(section: str, key: str):
    """Atajo para leer un valor específico."""
    return load().get(section, {}).get(key, DEFAULTS.get(section, {}).get(key))
