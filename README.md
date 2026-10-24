# centro-stem
Proyecto que recopila y centraliza oportunidades STEM y crea comunidad para los trabajos del futuro.

## Plan de trabajo

| Paso | Entregable | Estado |
|---|---|---|
| 1 | Diagnóstico de career-ops y cuestionario vocacional de dos rutas | En revisión |
| 2 | Base de conocimiento: catálogo de carreras y certificaciones; directorio de becas, vouchers y voluntariados (con fuente y fecha de verificación) | En revisión |
| 3 | Búsqueda de oportunidades como loop semanal de revisión | Pendiente |
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

