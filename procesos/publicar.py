"""
Republica en Datawrapper el gráfico de un proceso.

Los gráficos leen el CSV de este repositorio desde el servidor de Datawrapper, que solo lo
vuelve a descargar durante los 30 días siguientes a la última publicación. Republicar cada
semana reinicia ese plazo, así que el gráfico no se queda congelado.

El ID de cada gráfico y el nombre del secret con su token están en config/config.json
("datawrapper"). Hay dos tokens porque los gráficos están en dos cuentas distintas.

Uso: python -m procesos.publicar <linea|cuencas|embalses>
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RUTA_CONFIG = Path(__file__).resolve().parent.parent / "config" / "config.json"
URL_PUBLICAR = "https://api.datawrapper.de/v3/charts/{id}/publish"
INTENTOS = 3


def publicar(id_grafico: str, token: str) -> None:
    """Republica un gráfico. Reintenta si falla la red o Datawrapper da un error 5xx."""
    peticion = urllib.request.Request(
        URL_PUBLICAR.format(id=id_grafico),
        method="POST",
        headers={"Authorization": f"Bearer {token}"},
    )
    for intento in range(1, INTENTOS + 1):
        try:
            with urllib.request.urlopen(peticion, timeout=60):
                return
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise RuntimeError(f"Datawrapper rechaza el token ({e.code}): no existe, ha caducado, "
                                   f"le faltan permisos (chart:read, chart:write y theme:read) o el gráfico es de otra cuenta.")
            if e.code == 404:
                raise RuntimeError("Datawrapper no encuentra el gráfico (404): revisa el ID en config/config.json.")
            error = f"error {e.code}"
        except urllib.error.URLError as e:
            error = f"sin conexión ({e.reason})"
        if intento == INTENTOS:
            raise RuntimeError(f"No se ha podido republicar tras {INTENTOS} intentos: {error}.")
        print(f"  Intento {intento} fallido ({error}), reintentando…")
        time.sleep(intento * 10)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    proceso = sys.argv[1]
    conf = json.loads(RUTA_CONFIG.read_text(encoding="utf-8"))["datawrapper"].get(proceso)
    if conf is None:
        sys.exit(f"'{proceso}' no está en la sección \"datawrapper\" de config/config.json.")

    if not conf.get("id"):
        print(f"::warning title={proceso} - Datawrapper::Falta el ID del gráfico en config/config.json. No se republica.")
        return
    token = os.environ.get(conf["token"])
    if not token:
        print(f"::error title={proceso} - Datawrapper::Falta el secret {conf['token']} en el repositorio.")
        sys.exit(1)

    print(f"Republicando {proceso} ({conf['id']}) en Datawrapper…")
    try:
        publicar(conf["id"], token)
    except RuntimeError as e:
        print(f"::error title={proceso} - Datawrapper::{e}")
        sys.exit(1)
    print(f"[{proceso}] Republicado: https://datawrapper.dwcdn.net/{conf['id']}/")


if __name__ == "__main__":
    main()
