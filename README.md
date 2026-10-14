# Embalses automático

Actualiza cada semana los datos de los tres gráficos de embalses de Datawrapper a partir de los
boletines del Ministerio para la Transición Ecológica (MITECO). Lo ejecuta GitHub Actions los
**martes a las 15:00 UTC** (17:00 en Madrid en verano, 16:00 en invierno) y, como respaldo por si
el MITECO aún no ha publicado el boletín, los **miércoles a las 08:00 UTC** (10:00 en verano, 09:00 en
invierno). Si el martes ya se actualizó, la ejecución del miércoles no encuentra novedades y no cambia
nada. También se puede lanzar a mano.

Cada gráfico lee de este repositorio dos archivos: su `datos.csv` y un `metadata.json` con la nota al pie.

## Los tres procesos

Son independientes: si uno falla, los otros dos se actualizan con normalidad.

| Proceso | Gráfico | Fuente | Qué guarda |
|---|---|---|---|
| `linea` | Línea con el % de la reserva peninsular | Boletín semanal (documento 40), página 5, fila TOTAL | Acumula el histórico desde 2022. Añade todos los boletines nuevos desde el último dato. |
| `cuencas` | Mapa por cuencas | Boletín semanal (documento 40), página 7 | Solo el último boletín. |
| `embalses` | Mapa de símbolos | Desglose por embalses (documento 60), páginas 4 a final | Solo el último informe, con las coordenadas de `referencias/embalses_coordenadas.csv`. |

Se ejecutan por separado:

```
python -m procesos.linea
python -m procesos.cuencas
python -m procesos.embalses
```

Los PDF se descargan de `https://sede.miteco.gob.es/BoleHWeb/accion/cargador_archivo.htm?file=cache/pdf/AAAASS/AAAASS{40|60}_es.pdf`
en una carpeta temporal que se borra al terminar. No se guardan en el repositorio.

La fecha de cada dato es la que figura en la portada del boletín ("hasta el 5 de octubre de 2026"),
que es el lunes de cierre.

## Qué comprueba antes de publicar

Cada proceso sigue cuatro pasos y se detiene en cuanto uno falla: **descarga → procesamiento → validación → escritura**.
Solo si todo pasa se escriben los archivos, y se sustituyen de golpe. Si algo falla no cambia ninguno,
y el gráfico sigue mostrando el último dato válido con su fecha.

Si no hay boletín más nuevo que el último dato guardado, el proceso termina sin tocar nada. No es un error.

Validaciones (los límites están en `config/config.json`):

- **Todos**: la fecha de la portada es posterior al último dato guardado y como mucho 14 días anterior a hoy.
  Todos los porcentajes entre 0 y 100.
- **linea**: ningún valor se aleja más de 12 puntos del anterior.
- **cuencas**: están los 19 ámbitos esperados, y el TOTAL PENINSULAR coincide con el % de la página 5
  (diferencia máxima de 0,5 puntos).
- **embalses**: no hay embalses repetidos. El número de embalses del mapa no baja más de un 5 %
  respecto a la ejecución anterior. No hay coordenadas fuera de España; las de la lista
  `embalses_coordenadas_conocidas_mal` solo dan aviso. Los embalses del PDF sin coordenadas
  dan aviso y no salen en el mapa.

## Archivos

```
graficos/<proceso>/datos.csv        ← lo que lee Datawrapper (punto decimal, fechas AAAA-MM-DD)
graficos/<proceso>/metadata.json    ← nota al pie: {"annotate": {"notes": "..."}}
historicos/<proceso>.csv            ← registro de todo lo procesado (nunca se sobrescriben fechas)
config/config.json                  ← textos de las notas al pie y límites de la validación
referencias/embalses_coordenadas.csv
migracion/migracion_inicial.py      ← se usó una vez para importar los datos del proyecto anterior
```

**Nota al pie.** El texto de cada nota está en `config/config.json` (`"notas"`). `{fecha}` se sustituye
por la fecha del dato en español, por ejemplo "5 de octubre de 2026". Para cambiar el texto basta con
editar ese archivo. El cambio se verá la próxima vez que haya un boletín nuevo.

**Semanas perdidas.** En `linea` hay 10 semanas sin datos, porque el MITECO ya no sirve esos boletines:
2022-52, 2023-18, 2024-51, 2024-52 y de la 2025-01 a la 2025-06. Están como filas con fecha y valores
vacíos, para que la línea del gráfico se corte en esas semanas.

## URL para Datawrapper

| Gráfico | Datos | Nota al pie |
|---|---|---|
| Línea | https://raw.githubusercontent.com/SarahIshtar/embalses_automatico/main/graficos/linea/datos.csv | https://raw.githubusercontent.com/SarahIshtar/embalses_automatico/main/graficos/linea/metadata.json |
| Cuencas | https://raw.githubusercontent.com/SarahIshtar/embalses_automatico/main/graficos/cuencas/datos.csv | https://raw.githubusercontent.com/SarahIshtar/embalses_automatico/main/graficos/cuencas/metadata.json |
| Embalses | https://raw.githubusercontent.com/SarahIshtar/embalses_automatico/main/graficos/embalses/datos.csv | https://raw.githubusercontent.com/SarahIshtar/embalses_automatico/main/graficos/embalses/metadata.json |

## Si llega un correo de error

GitHub manda un correo cuando un job termina en rojo. Mientras tanto, ese gráfico sigue con el último dato válido.

1. Abre el enlace del correo, o la pestaña **Actions** del repositorio. Entra en la ejecución fallida
   y en el job en rojo (`linea`, `cuencas` o `embalses`).
2. Al final del paso "Actualizar …" aparece una línea `FALLO en el paso '<paso>': <motivo>`:
   - **descarga**: el servidor del MITECO no responde o ha devuelto algo que no es un PDF.
     Suele ser temporal: vuelve a lanzarlo más tarde con **Re-run failed jobs**.
   - **procesamiento**: ha cambiado el formato del PDF (otra página, otras columnas…). Hay que adaptar el código.
   - **validación**: los datos leídos no son creíbles. En el log aparecen todas las comprobaciones
     con `[OK]` o `[FALLO]`. Compara con el PDF del MITECO. Si el dato es correcto (por ejemplo, una
     subida real de más de 12 puntos tras lluvias fuertes), cambia el límite en `config/config.json`
     y vuelve a lanzarlo. Si es un error de lectura, hay que corregir el código.
   - **escritura** o **push**: problema de GitHub o de permisos. Vuelve a lanzarlo.
3. Para lanzarlo a mano: **Actions → Embalses → Run workflow**.

## Ejecutar en local

```
python -m venv venv
venv\Scripts\activate            (Windows)   ·   source venv/bin/activate (Mac/Linux)
pip install -r requirements.txt
python -m procesos.linea
```

Hace falta Java 8 o superior instalado (lo usa tabula).
