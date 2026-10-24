# 06 · Directorio de becas, vouchers, retos y voluntariados

> Paso 2 del plan aprobado. Datos en [`data/oportunidades.yaml`](../data/oportunidades.yaml) y [`data/preparacion.yaml`](../data/preparacion.yaml); tabla legible en [`generado/directorio.md`](generado/directorio.md). Verificación: 24-oct-2026.

## 1. Alcance

17 oportunidades y 7 programas de preparación para México y América Latina, en ocho tipos: voucher, descuento, beca, apoyo económico, reto, voluntariado, prácticas y programa. Cada registro indica público (edad, nivel, género, región), costo para la persona, estado, fuente y la fecha en que el loop semanal debe volver a revisarlo.

## 2. Socios prioritarios

| Socio | Qué quedó registrado | Calidad de la información |
|---|---|---|
| **Generation México** | Cuatro bootcamps STEM gratuitos (Java Full Stack, AWS re/Start con IA, HelpDesk, Unity), con edad, duración y requisitos. Java Full Stack tiene grupo con inicio el 2-nov-2026. | Buena. AWS re/Start muestra fechas incongruentes en su página. |
| **JA Americas** | Mujer Digital: formación técnica becada para mujeres de 18 a 29 años en México, Brasil y Costa Rica. | Media. El sitio dice a la vez "lista de espera" y "convocatoria abierta". |
| **JA México** | Desafío Innova, Yo puedo programar, Socios por un día, servicio social y prácticas, voluntariado. | Baja. Las fichas oficiales no publican edad, duración ni fechas; quedan como pendientes para confirmar por WhatsApp (55 5211 9444). |
| **BioCiencia Wild** y **Regeni** | Registrados como `org-` con `estado: pendiente`. | Sin enlace oficial. No se muestran al usuario hasta que Victor comparta su fuente. |

**Recomendación práctica:** el catálogo de JA México lista 28 programas, pero la información pública es insuficiente para recomendar con fecha. Conviene pedir a JA México su calendario 2027 y la edad por programa; una sola conversación resolvería la mitad de los pendientes del directorio.

## 3. Estados y reglas

| Estado | Significado | Qué hace el prototipo |
|---|---|---|
| `abierta` | Convocatoria con fecha vigente | Mostrar con fecha de cierre |
| `recurrente` | Se repite; la siguiente edición no tiene fecha | Ofrecer "avísame cuando abra" |
| `permanente` | Disponible siempre | Mostrar |
| `por_confirmar` | La fuente es ambigua o incompleta | No mostrar como opción firme |
| `cerrada` | Cerró; se conserva para vigilar reapertura | Ocultar, salvo historial |

Reglas que el validador comprueba:

1. Una **fuente secundaria nunca basta** para marcar una oportunidad como `abierta`.
2. Toda oportunidad tiene `revisar_antes`. Pasada esa fecha, el registro se reporta como vencido (`--estricto` lo convierte en error).
3. Una oportunidad `abierta` cuya `fecha_cierre` ya pasó se reporta.
4. Las referencias a certificaciones (`aplica_a`) y organizaciones deben existir.

## 4. Lo más útil hoy (24-oct-2026)

- **NASA Space Apps Challenge**, 14 y 15 de noviembre de 2026, presencial o virtual, gratuito. Buen primer proyecto de portafolio para la ruta A3 y la ruta B.
- **Generation México Java Full Stack**, grupo del 2 de noviembre, gratuito, para personas de 18 a 29 años sin empleo.
- **ISC2 CC en español por USD 199** con curso, dos intentos y primera cuota anual incluida. El programa gratuito *One Million Certified* ya cerró.
- **Jóvenes Construyendo el Futuro**: $9,582 mensuales en 2026 para personas de 18 a 29 años que no estudian ni trabajan; próximas postulaciones por anunciar.

## 5. Uso por el loop semanal (paso 3)

El loop debe recorrer los registros ordenados por `revisar_antes`, abrir `fuente_url`, actualizar `estado`, `fecha_cierre` y `fecha_verificacion`, y ejecutar `python3 scripts/catalogo.py --generar`. Los registros `recurrente` y `cerrada` son la lista de vigilancia: Becas Google + SEP (edición 2025 cerrada), Virtual Training Days de Microsoft y Mujer Digital.
