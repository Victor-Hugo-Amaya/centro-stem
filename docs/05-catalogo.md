# 05 · Catálogo de carreras y certificaciones

> Paso 2 del plan aprobado. Los datos viven en [`data/`](../data); las tablas legibles se generan en [`generado/catalogo.md`](generado/catalogo.md). Verificación: 24-oct-2026.

## 1. Qué contiene

| Archivo | Entidad | Registros |
|---|---|---|
| [`data/familias.yaml`](../data/familias.yaml) | Familias ocupacionales (`fam-`) con nivel de demanda y señales citadas | 10 |
| [`data/carreras.yaml`](../data/carreras.yaml) | Carreras de licenciatura y TSU (`car-`) con cifras del IMCO; bachilleratos (`bach-`) | 14 + 3 |
| [`data/certificaciones.yaml`](../data/certificaciones.yaml) | Certificaciones (`cert-`) con costo, vigencia, renovación, idioma y vías de ahorro | 16 |
| [`data/preparacion.yaml`](../data/preparacion.yaml) | Cursos y bootcamps (`prep-`) | 7 |
| [`data/organizaciones.yaml`](../data/organizaciones.yaml) | Socios, certificadores y programas públicos (`org-`) | 20 |
| [`data/fuentes.yaml`](../data/fuentes.yaml) | Reportes citados por las señales de demanda | 6 |

Todos los registros cumplen el contrato de [03-modelo-de-salida.md](03-modelo-de-salida.md): prefijo de ID, `fuente_url` y `fecha_verificacion`. Los tres `id_catalogo` usados como ejemplo en ese contrato existen.

## 2. Cómo se ordena por demanda

El orden no es una opinión: cada familia recibe un nivel según reglas explícitas, y cada nivel cita al menos dos señales de fuentes distintas.

| Nivel | Puntaje | Regla |
|---|---|---|
| Muy alta | 90 | Crecimiento neto ≥ 40% en el perfil México del WEF, o rol en el top global del WEF con escasez documentada en México |
| Alta | 75 | Rol en la lista de mayor crecimiento global del WEF o habilidad de uso creciente ≥ 70% en México, más una señal nacional |
| Media | 55 | Señales mixtas o indirectas |
| Descenso | 30 | El WEF proyecta caída neta del rol en México |

Resultado: **Datos e IA** y **Ciberseguridad** (muy alta); **Software y nube**, **Manufactura avanzada** y **Energía y ambiente** (alta); **Soporte de TI**, **Salud**, **Gestión de proyectos** y **UX** (media); **Administración y contabilidad** (descenso).

Las certificaciones se ordenan por el puntaje de su familia, luego por nivel de escalera (fundamentos primero) y luego por costo. Las carreras, por el puntaje de su familia y luego por ingreso.

**Limitación honesta.** Los puntajes son una hipótesis de partida, igual que los pesos del motor (docs/02 §7). Los reportes miden expectativas de empleadores, no vacantes publicadas. El loop semanal (paso 3) debe reemplazar este componente por la frecuencia observada de cada certificación en vacantes reales.

## 3. Reglas de calidad de los datos

1. **Costo verificado sólo con página oficial.** `costo.verificado: true` exige que el monto aparezca en la página del certificador citada en `costo.fuente_url`. Con `false`, el prototipo no debe mostrar el monto como firme.
2. **Vigencia explícita.** `no_caduca: true` sólo cuando el certificador lo dice; si no se pudo confirmar, `vigencia_meses: null` y el validador lo reporta.
3. **Idioma del examen.** `idioma_es` es obligatorio para el filtro de la pregunta B13; `null` significa no confirmado.
4. **Advertencias visibles.** Los cambios que afectan una decisión (retiro de un examen, programa gratuito cerrado, examen sólo en inglés) van en `advertencia` y aparecen en la tabla generada.

`python3 scripts/catalogo.py` valida todas las reglas y las referencias cruzadas; el flujo de GitHub Actions lo ejecuta en cada cambio de `data/`.

## 4. Hallazgos que cambian recomendaciones del paso 1

| Hallazgo | Fuente oficial | Efecto |
|---|---|---|
| Los Microsoft Virtual Training Days dan **50% de descuento**, no voucher gratuito. Debe usarse en 90 días. | [FAQ de Microsoft](https://arch-center.azureedge.net/Credentials/microsoft-mvtd-cert-faq-en-us.pdf) | Corregida la tabla de docs/02 §6.1 |
| El examen **AI-900 se retiró el 30-jun-2026**; lo sustituye AI-901. | [Microsoft Learn](https://learn.microsoft.com/en-us/credentials/support/retired-certification-exams) | El catálogo usa `cert-microsoft-ai-901` |
| **CCNA sólo se ofrece en inglés y japonés.** | [Cisco](https://www.cisco.com/site/us/en/learn/training-certifications/exams/ccna.html) | Para nivel básico de inglés, ruta CCST (en español, USD 125) |
| **Security+ cambia a V8** alrededor del 17-nov-2026; el descuento académico de CompTIA es sólo para EE. UU. y Canadá. | [CompTIA](https://www.comptia.org/en-gb/certifications/security/v7/) | No recomendar compra de material V7 sin advertir |
| **ISC2 CC**: además del examen de USD 199, existe un paquete en español de USD 199 que incluye curso, dos intentos y la primera cuota anual. | [ISC2](https://www.isc2.org/training/online-self-paced/spanish) | Mejor vía de pago que el examen suelto |
| **NABCEP PV Associate desde México cuesta USD 225**, no 125, por el recargo internacional. | [NABCEP](https://www.nabcep.org/certifications/nabcep-fees/) | Costo real registrado |

## 5. Lectura crítica de las cifras del IMCO

- **Contabilidad tiene hoy 1.9% de desempleo**, menos que Ciencias computacionales (5.2%). La caída que proyecta el WEF (−20%) es de tareas de auxiliar, no de la profesión completa. El sistema debe advertir sin alarmar: recomendar complementar con datos o fintech.
- **Informalidad alta en técnicos.** TSU en Electricidad (0.8% de desempleo) tiene 36.9% de informalidad; TSU en Desarrollo de software, 34.2%. "Empleable" no equivale a "empleo formal": mostrar ambas cifras.
- **"Ambiental" no es sinónimo de demanda.** Tecnología para la protección del medio ambiente está entre las 10 carreras de mayor riesgo (8.9% de desempleo). La demanda verde del WEF se concentra en ingeniería.
- **Brecha de género en ingeniería.** Las mujeres son 10.7% en Electrónica y automatización y 0.9% en TSU de Electricidad. Programas como Mujer Digital y Technovation Girls deben priorizarse para estas familias.
- **Discrepancia de fuentes.** Las fichas de la plataforma Compara Carreras y las gráficas del PDF no coinciden (Medicina general: $27,823 frente a $25,732). El catálogo usa la ficha, que es la que tiene URL por carrera.

## 6. Cobertura pendiente

- **Salud y biotecnología** no tiene certificaciones: las credenciales relevantes son regulatorias (cédula profesional, COFEPRIS, estándares CONOCER).
- **Estándares de competencia CONOCER**, oficiales en México y útiles para técnicos, quedan para la siguiente iteración.
- **Precios en moneda local** de Microsoft, CompTIA y PMI requieren consultar la tienda con sesión; quedan como `verificado: false`.
- **Coursera Global Skills Report 2026** ya está publicado: incorporarlo con el procedimiento de [04-evidencia-reportes.md](04-evidencia-reportes.md) §7.
- **Bachilleratos:** falta la lista de especialidades por plantel (DGETI y CONALEP).
