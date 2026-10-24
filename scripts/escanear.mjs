// Escáner semanal de vacantes (fase B, docs/07-loop-semanal.md §6).
//
// Usa los proveedores de career-ops (licencia MIT, ver THIRD_PARTY_NOTICES.md), que la
// tarea de GitHub Actions descarga fijados al commit indicado en CAREER_OPS_SHA. El código
// de career-ops no se copia a este repositorio.
//
// Uso:
//   python3 scripts/semanal.py --entradas-escaner > entradas.json
//   CAREER_OPS_DIR=/ruta/a/career-ops node scripts/escanear.mjs entradas.json vacantes.json
//
// Salida: {generado, fuentes: [{nombre, proveedor, ok, total, error}], vacantes: [Job]}.
// Una fuente que falla no detiene el resto; queda registrada para el reporte semanal.
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const [entradasPath, salidaPath] = process.argv.slice(2);
const dir = process.env.CAREER_OPS_DIR;
if (!entradasPath || !salidaPath || !dir) {
  console.error('Uso: CAREER_OPS_DIR=... node scripts/escanear.mjs entradas.json vacantes.json');
  process.exit(2);
}
const importar = (rel) => import(pathToFileURL(resolve(dir, rel)).href);

const MAX_DESCRIPCION = 4000;
const { makeHttpCtx } = await importar('providers/_http.mjs');
const ctx = makeHttpCtx();
const entradas = JSON.parse(readFileSync(entradasPath, 'utf8'));
const fuentes = [];
const vacantes = [];

for (const entrada of entradas) {
  const registro = { nombre: entrada.name, proveedor: entrada.provider, ok: false, total: 0 };
  try {
    const proveedor = (await importar(`providers/${entrada.provider}.mjs`)).default;
    const jobs = await proveedor.fetch(entrada, ctx);
    for (const job of jobs) {
      let location = job.location || '';
      // Las bolsas de un solo país (Computrabajo México) no repiten el país en cada vacante.
      if (entrada.pais && !location.toLowerCase().includes(entrada.pais.toLowerCase())) {
        location = location ? `${location}, ${entrada.pais}` : entrada.pais;
      }
      vacantes.push({
        title: job.title,
        url: job.url,
        company: job.company || entrada.name,
        location,
        description: (job.description || '').slice(0, MAX_DESCRIPCION),
        fuente: entrada.name,
        ...(job.postedAt ? { postedAt: job.postedAt } : {}),
      });
    }
    registro.ok = true;
    registro.total = jobs.length;
  } catch (err) {
    registro.error = String(err?.message || err).slice(0, 300);
  }
  fuentes.push(registro);
  console.log(`${registro.ok ? 'OK   ' : 'FALLA'} ${entrada.name} (${entrada.provider}): ${registro.ok ? registro.total : registro.error}`);
}

writeFileSync(salidaPath, JSON.stringify({ generado: new Date().toISOString(), fuentes, vacantes }, null, 1));
console.log(`${vacantes.length} vacantes de ${fuentes.filter((f) => f.ok).length}/${fuentes.length} fuentes.`);
