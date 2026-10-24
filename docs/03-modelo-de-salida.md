# 03 · Modelo de salida del cuestionario

> Contrato de datos entre el cuestionario (paso 1) y los pasos 2, 3 y 4. El esquema formal está en [`schemas/resultado-cuestionario.schema.json`](../schemas/resultado-cuestionario.schema.json).

## 1. Principio

El cuestionario no produce texto libre: produce un **registro estructurado** con tres partes.

1. `perfil`: lo que la persona respondió, normalizado.
2. `recomendaciones`: lo que el motor sugiere, cada elemento con puntaje desglosado y evidencia.
3. `semillas_busqueda`: lo que el loop semanal (paso 3) debe vigilar para esta persona.

Siguiendo el contrato de datos de career-ops, el formato canónico es un archivo legible (YAML o JSON); cualquier base de datos del prototipo es un índice derivado.

## 2. Qué consume cada paso

| Campo | Paso 2 · Base de conocimiento | Paso 3 · Loop semanal | Paso 4 · Prototipo web |
|---|---|---|---|
| `perfil.familias_interes`, `perfil.industrias` | Prioriza qué familias completar primero en el catálogo | Filtra vacantes y convocatorias | Muestra perfil |
| `perfil.habilidades`, `perfil.herramientas` | — | Calcula brecha contra vacantes (`skill-extract`) | Gráfica de brecha |
| `recomendaciones[].id_catalogo` | **Debe existir** en el catálogo o el directorio | Revisa vigencia (`check-liveness`) | Tarjeta de recomendación |
| `recomendaciones[].evidencia` | Fuente y fecha de verificación | Actualiza cifras de demanda | "¿Por qué te lo recomendamos?" |
| `semillas_busqueda.empresas` | — | Lista de empresas a escanear (`portals.yml`) | — |
| `semillas_busqueda.palabras_clave` | — | Consultas a OCC, Computrabajo y ATS | — |
| `semillas_busqueda.alertas` | — | Avisos de vouchers, retos y cierres | Notificaciones |
| `privacidad` | — | Excluye menores de alertas de vacantes | Consentimiento y retención |

## 3. Identificadores que el paso 2 debe respetar

Para que las recomendaciones apunten a algo verificable, el catálogo y el directorio usarán estos prefijos:

| Prefijo | Entidad | Ejemplo |
|---|---|---|
| `car-` | Carrera (licenciatura o TSU) | `car-ingenieria-en-computacion` |
| `bach-` | Tipo de bachillerato o especialidad técnica | `bach-tecnologico-mecatronica` |
| `cert-` | Certificación | `cert-aws-clf-c02` |
| `prep-` | Curso o bootcamp de preparación | `prep-generation-java-fullstack` |
| `opo-` | Beca, voucher, reto, voluntariado o prácticas | `opo-ms-virtual-training-day-az900` |
| `org-` | Organización o socio | `org-ja-mexico`, `org-generation-mexico` |
| `fam-` | Familia ocupacional STEM | `fam-datos-ia`, `fam-manufactura-avanzada` |

Cada entidad del paso 2 debe incluir como mínimo `fuente_url` y `fecha_verificacion`.

## 4. Ejemplo: estudiante de bachillerato

```yaml
version_esquema: 1
id_respuesta: 6f1c...            # aleatorio; sin nombre ni correo
fecha: 2026-10-24
ruta: estudiante
privacidad:
  menor_de_edad: true
  consentimiento_tutor: false     # sin consentimiento no se guarda en servidor
  almacenamiento: dispositivo
perfil:
  rango_edad: "15-17"
  estado: "Nuevo León"
  nivel: bachillerato_en_curso
  horas_semana: "3-5"
  presupuesto_6m: "nada"
  familias_interes: [fam-manufactura-avanzada, fam-datos-ia]
  industrias: [automotriz, energia]
  empresas_objetivo: ["Ternium", "KIA"]
  ingles: intermedio
  valores: [salario, estabilidad, impacto]
recomendaciones:
  - tipo: carrera
    id_catalogo: car-ingenieria-mecatronica
    puntaje: 82
    desglose: {demanda: 30, ajuste: 27, accesibilidad: 13, senal_regional: 12}
    evidencia:
      - dato: "Programas de educación dual en Nuevo León vinculados a la industria automotriz"
        fuente: "IMCO, Compara Carreras 2025, sección IMCO Propone"
        fecha_verificacion: 2026-10-24
  - tipo: extracurricular
    id_catalogo: opo-ja-desafio-innova
    puntaje: 74
    desglose: {demanda: 18, ajuste: 28, accesibilidad: 20, senal_regional: 8}
    evidencia:
      - dato: "Reto para jóvenes de 15 a 18 años con fundamentos STEM"
        fuente: "JA Americas, 2025"
        fecha_verificacion: 2026-10-24
semillas_busqueda:
  empresas: []                    # menor de edad: sin vacantes
  palabras_clave: ["educación dual mecatrónica Nuevo León"]
  alertas: [becas_licenciatura, retos_stem_15_18]
```

## 5. Ejemplo: cambio de carrera

```yaml
version_esquema: 1
id_respuesta: a92e...
fecha: 2026-10-24
ruta: cambio_carrera
privacidad: {menor_de_edad: false, consentimiento_tutor: null, almacenamiento: servidor}
perfil:
  rango_edad: "30-39"
  estado: "Jalisco"
  nivel: licenciatura_terminada
  situacion_laboral: empleado_tiempo_completo
  area_actual: finanzas_contabilidad
  anios_experiencia: "5-9"
  roles_objetivo: [analisis-datos]
  habilidades: {pensamiento_analitico: 4, tecnologia_ia: 2, excel_datos: 4, programacion: 1}
  herramientas: [excel, sap]
  portafolio: []
  certificaciones_actuales: []
  plazo_meses: 6
  ingles: intermedio
recomendaciones:
  - tipo: certificacion
    id_catalogo: cert-microsoft-pl-300
    nivel_escalera: 2
    puntaje: 78
    costo: {monto: null, moneda: USD, verificado: false}   # el paso 2 lo completa
    vigencia_meses: 12
    renovacion: "evaluación en línea gratuita"            # a verificar en paso 2
    via_ahorro: []
    evidencia:
      - dato: "Analistas y científicos de datos: +47% de crecimiento neto proyectado en México 2025-2030"
        fuente: "WEF, Future of Jobs Report 2025, perfil México"
        fecha_verificacion: 2026-10-24
      - dato: "Auxiliares de contabilidad: −20% de crecimiento neto proyectado en México"
        fuente: "WEF, Future of Jobs Report 2025, perfil México"
        fecha_verificacion: 2026-10-24
  - tipo: proyecto_portafolio
    descripcion: "Tablero de conciliación financiera con datos públicos"
semillas_busqueda:
  empresas: []
  palabras_clave: ["analista de datos", "analista financiero power bi", "Guadalajara"]
  alertas: [vouchers_microsoft, cert-microsoft-pl-300]
```

## 6. Reglas de validación

1. Ninguna recomendación sin al menos una `evidencia` con `fuente` y `fecha_verificacion`.
2. `costo.verificado: false` impide mostrar el monto al usuario como dato firme.
3. Si `privacidad.menor_de_edad` es verdadero, `semillas_busqueda.empresas` debe estar vacío y `almacenamiento` sólo puede ser `servidor` con `consentimiento_tutor: true`.
4. Los `id_catalogo` que no existan en el catálogo generan una tarea para el paso 2, no un error visible al usuario.
