# 01 · Diagnóstico de career-ops para Centro STEM

> Paso 1 del plan aprobado (2026-10-24). Repositorio revisado: [career-ops-hq/career-ops](https://github.com/career-ops-hq/career-ops), versión `1.38.0`, commit `b564412` (24-oct-2026).

## 1. Conclusión ejecutiva

career-ops **no es una plataforma de orientación vocacional**: es un agente local, de un solo usuario, para personas que ya buscan empleo y quieren filtrar vacantes, adaptar su CV y dar seguimiento a candidaturas. Su valor para Centro STEM está en tres piezas de infraestructura (escaneo de portales, extracción canónica de habilidades y verificación de vigencia de enlaces), no en su experiencia de usuario.

**Recomendación:** no hacer *fork* del proyecto. Reutilizar módulos concretos con atribución en el paso 3 (loop semanal de oportunidades) y construir el cuestionario, la base de conocimiento y el prototipo web como producto propio. Así se evita heredar más de 150 scripts orientados a candidaturas que este proyecto no necesita.

## 2. Qué hace career-ops

| Función | Mecanismo | Archivo o modo de referencia |
|---|---|---|
| Evaluar una vacante (bloques A a G, puntaje de 1 a 5, legitimidad de la oferta) | Prompt en Markdown ejecutado por un CLI de IA | `modes/oferta.md`, `modes/_shared.md` |
| Escanear portales y páginas de carrera de empresas | Proveedores por ATS (Greenhouse, Lever, Ashby, Workday, SuccessFactors y otros) y *parsers* por portal | `scan.mjs`, `providers/`, `templates/portals.example.yml` |
| Cobertura de México y LatAm | Proveedores **OCC Mundial** y **Computrabajo**; empresas LatAm precargadas (Nubank, Clara, Platzi, Wiz, etc.) | `docs/SUPPORTED_JOB_BOARDS.md` |
| Verificar si una vacante sigue abierta | API pública primero y Playwright como respaldo | `check-liveness.mjs`, `liveness-*.mjs` |
| Brecha de habilidades por vacante y agregada | Vocabulario canónico de habilidades, sin LLM | `skill-extract.mjs`, `jd-skill-gap.mjs`, `upskill.mjs` |
| Evaluar cursos y certificaciones | Rúbrica de 6 dimensiones con veredicto *HACER / NO HACER / HACER CON LÍMITE DE TIEMPO* | `modes/training.md` |
| Perfil a partir de CV, LinkedIn y constancias | Ingesta local con aprobación humana | `intake.mjs`, `modes/intake.md` |
| Seguimiento de candidaturas, tablero, PDF de CV | Archivos Markdown y YAML como fuente de verdad; tablero en Go | `data/`, `dashboard/` |

Principios de arquitectura (`ARCHITECTURE.md`): **local-first**, **agnóstico de modelo de IA** y **humano en el circuito** (nunca envía una candidatura por el usuario). Los archivos legibles y versionables en git son la fuente de verdad; las bases de datos son índices derivados. El contenido externo (vacantes, resultados de búsqueda) se trata siempre como dato no confiable.

Requisitos técnicos: Node.js 22.13 o superior, Playwright 1.64 y un CLI de IA (Claude Code, Codex, Gemini, etc.).

## 3. Licencia y marca

- **Código: licencia MIT** (© 2026 Santiago Fernández de Valderrama). Se puede usar, modificar y redistribuir, conservando el aviso de copyright y la licencia en las partes copiadas.
- **Marca: `TRADEMARK.md` la reserva.** Está permitido decir "basado en career-ops" o "usa módulos de career-ops" con atribución. **No** está permitido nombrar el producto "career-ops …", usar su logotipo ni afirmar "Powered by career-ops" o una alianza oficial sin permiso escrito.
- **Implicación práctica:** Centro STEM conserva su nombre propio, incluye un archivo `THIRD_PARTY_NOTICES.md` cuando se copie código (paso 3) y cita el origen en la documentación.

## 4. Qué se puede reutilizar o adaptar

| Prioridad | Componente | Uso en Centro STEM | Paso |
|---|---|---|---|
| Alta | Esquema `portals.yml` y proveedores OCC Mundial, Computrabajo, Workday, Greenhouse y Lever | Fuente del loop semanal de vacantes para extraer qué certificaciones y habilidades piden las empresas objetivo | 3 |
| Alta | `skill-extract.mjs` (vocabulario canónico de habilidades) | Normalizar "AWS", "Amazon Web Services" y "AWS CCP" a una sola entidad para contar demanda real | 2 y 3 |
| Alta | `check-liveness.mjs` | Marcar becas, convocatorias y vacantes vencidas en cada ciclo semanal | 3 |
| Media | Rúbrica de `modes/training.md` (alineación, señal para reclutadores, tiempo, costo de oportunidad, riesgos, entregable de portafolio) | Base para la ficha de evaluación de cada certificación del catálogo | 2 |
| Media | Lógica agregada de `upskill.mjs` (brecha ponderada y explicable por niveles) | Ranking de certificaciones por demanda observada, en vez de por popularidad | 3 |
| Media | Contrato de datos (archivos canónicos, índices derivados) | Catálogo y directorio en YAML o Markdown versionados, con `fuente` y `fecha_verificacion` | 2 |
| Baja | `modes/intake.md` | Importar CV o LinkedIn en la ruta de cambio de carrera (opcional y con consentimiento) | 4 |

**Advertencia operativa verificada en su documentación:** el proveedor de OCC Mundial depende de un reto de Cloudflare **con alcance geográfico**. Responde desde una conexión residencial mexicana y devuelve 403 desde servidores extranjeros. El loop semanal debe ejecutarse con salida de red en México o apoyarse en las API de los ATS de las empresas (Workday, SuccessFactors, Greenhouse, Lever), que sí funcionan desde la nube.

## 5. Qué le falta a career-ops para este proyecto

1. **Orientación vocacional.** No contempla estudiantes, intereses ni elección de bachillerato o carrera. Su usuario ya tiene un rol objetivo.
2. **Menores de edad.** No tiene un modelo de consentimiento ni de minimización de datos para personas de 12 a 17 años (secundaria y prepa).
3. **Directorio de becas, vouchers, retos y voluntariados.** No existe. Sólo evalúa cursos que el usuario ya identificó.
4. **Catálogo de certificaciones con costo, vigencia y renovación.** No existe como dato estructurado.
5. **Datos del mercado mexicano.** No integra IMCO (salarios por carrera, entidades con especialización STEM) ni el perfil México del WEF.
6. **Experiencia web multiusuario.** Es una herramienta de terminal para usuarios técnicos. La audiencia de Centro STEM no instalará Node ni un CLI de IA.
7. **Comunidad y socios.** No tiene un concepto de organizaciones aliadas (Junior Achievement, Generation) ni de mentorías.
8. **Idioma y sesgo de mercado.** El núcleo y la mayoría de las empresas precargadas están orientados a tecnología en EE. UU. y Europa; la cobertura STEM no digital (manufactura, energía, salud, biotecnología) es escasa.

## 6. Riesgos de depender de career-ops

- **Volatilidad:** el proyecto publica versiones con mucha frecuencia (1.38.0 al momento de la revisión). Conviene fijar una versión o copiar módulos puntuales, no seguir `main`.
- **Scraping:** cada portal tiene términos de uso y `robots.txt` propios. career-ops documenta los suyos, pero la responsabilidad de cumplirlos recae en quien opera el loop.
- **Diseño monousuario:** sus scripts asumen un solo `cv.md` y un solo `profile.yml`. Adaptarlos a muchos usuarios requiere reescribir la capa de datos, no sólo configurarla.

## 7. Decisión propuesta

| Opción | Veredicto |
|---|---|
| *Fork* completo y rebautizar | Descartada: hereda complejidad irrelevante y choca con la política de marca si se comercializa. |
| Usar career-ops tal cual para los usuarios finales | Descartada: la audiencia no es técnica y el producto no orienta. |
| **Reutilizar módulos con atribución y construir producto propio** | **Recomendada.** |
