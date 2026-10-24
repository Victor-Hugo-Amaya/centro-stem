# centro-stem
Proyecto que recopila y centraliza oportunidades STEM y crea comunidad para los trabajos del futuro.

## Plan de trabajo

| Paso | Entregable | Estado |
|---|---|---|
| 1 | Diagnóstico de career-ops y cuestionario vocacional de dos rutas | Terminado |
| 2 | Base de conocimiento: catálogo de carreras y certificaciones; directorio de becas, vouchers y voluntariados (con fuente y fecha de verificación) | Terminado |
| 3 | Búsqueda de oportunidades como loop semanal de revisión, más revisión mensual de reportes | En revisión |
| 4 | Prototipo web | Pendiente |

## Documentación del paso 1

- [01 · Diagnóstico de career-ops](docs/01-diagnostico-career-ops.md): qué hace, licencia, qué se reutiliza y qué falta.
- [02 · Cuestionario vocacional](docs/02-cuestionario-vocacional.md): bloque común, ruta de estudiantes, ruta de cambio de carrera, motor de recomendación y socios.
- [03 · Modelo de salida](docs/03-modelo-de-salida.md): contrato de datos para los pasos 2 a 4, con su [esquema JSON](schemas/resultado-cuestionario.schema.json).
- [04 · Evidencia de los reportes](docs/04-evidencia-reportes.md): cifras del WEF, Coursera, IMCO y la OIT usadas por el motor.

## Documentación del paso 2

- [05 · Catálogo de carreras y certificaciones](docs/05-catalogo.md): método de orden por demanda, reglas de calidad y hallazgos. Tabla completa en [docs/generado/catalogo.md](docs/generado/catalogo.md).
- [06 · Directorio de becas, vouchers, retos y voluntariados](docs/06-directorio.md): socios prioritarios, estados y uso por el loop semanal. Tabla completa en [docs/generado/directorio.md](docs/generado/directorio.md).
- Datos en [`data/`](data) (YAML). Para validar y regenerar las tablas:

```bash
pip install pyyaml
python3 scripts/catalogo.py --generar
```


## Documentación del paso 3

- [07 · Loop semanal de oportunidades y revisión mensual de reportes](docs/07-loop-semanal.md): ciclo, fuentes, reglas de aceptación, fase B con career-ops y tareas programadas.
- Configuración en [`data/portales.yaml`](data/portales.yaml) (fuentes) y [`data/busqueda.yaml`](data/busqueda.yaml) (semillas por familia y ruta, patrones de certificaciones).
- Escáner de vacantes en GitHub Actions con proveedores de career-ops fijados a una versión ([avisos de terceros](THIRD_PARTY_NOTICES.md)).
- Instrucciones de las tareas programadas: [semanal](docs/prompts/loop-semanal.md) y [mensual](docs/prompts/revision-mensual.md). Los reportes quedan en `reportes/semanal/`.

```bash
python3 scripts/semanal.py                 # agenda de la semana
python3 -m unittest discover tests         # pruebas
```
