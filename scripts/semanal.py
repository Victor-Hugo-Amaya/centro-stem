#!/usr/bin/env python3
"""Prepara la revisión semanal de oportunidades (paso 3, docs/07-loop-semanal.md).

Uso:
    python3 scripts/semanal.py                       # imprime la agenda de esta semana
    python3 scripts/semanal.py --hoy 2026-10-26      # agenda para otra fecha
    python3 scripts/semanal.py --escribir            # guarda reportes/semanal/AAAA-MM-DD.md
    python3 scripts/semanal.py --vacantes v.json     # agrega el análisis de vacantes escaneadas

La agenda contiene:
  1. Registros del directorio cuyo `revisar_antes` vence en los próximos 7 días (o ya venció).
  2. Convocatorias abiertas que cierran en los próximos 30 días.
  3. Lista de vigilancia (recurrentes y cerradas) y cursos de preparación por confirmar.
  4. Consultas de búsqueda web de la semana: las familias rotan para que cada semana
     se revisen tres y el ciclo completo dure tres semanas.

`--vacantes` recibe una lista JSON de vacantes con la forma `Job` de career-ops
(title, url, company, location, description opcional). Se filtran a México o remoto
LatAm, se clasifican (prácticas o vacante de entrada), se asignan a una familia y se
cuentan las certificaciones del catálogo que mencionan (demanda observada).
"""
import argparse
import datetime as dt
import json
import re
import sys
import unicodedata
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "data"
REPORTES = RAIZ / "reportes" / "semanal"
HORIZONTE_REVISION = 7
HORIZONTE_CIERRE = 30
FAMILIAS_POR_SEMANA = 3
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


def leer(nombre):
    return yaml.safe_load((DATOS / nombre).read_text(encoding="utf-8"))


def como_fecha(valor):
    if isinstance(valor, dt.date):
        return valor
    try:
        return dt.date.fromisoformat(str(valor))
    except ValueError:
        return None


def normalizar(texto):
    """Minúsculas y sin acentos, para comparar patrones."""
    texto = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return texto.lower()


def contiene(texto, patron):
    """Coincidencia de palabra completa; `texto` ya viene normalizado."""
    return re.search(r"(?<![a-z0-9])" + re.escape(normalizar(patron)) + r"(?![a-z0-9])", texto) is not None


# ---------------------------------------------------------------- agenda

def agenda_directorio(oportunidades, preparacion, hoy):
    limite = hoy + dt.timedelta(days=HORIZONTE_REVISION)
    por_revisar = sorted(
        (o for o in oportunidades if como_fecha(o.get("revisar_antes")) and como_fecha(o["revisar_antes"]) <= limite),
        key=lambda o: como_fecha(o["revisar_antes"]))
    por_cerrar = sorted(
        (o for o in oportunidades
         if o.get("estado") == "abierta" and como_fecha(o.get("fecha_cierre"))
         and hoy <= como_fecha(o["fecha_cierre"]) <= hoy + dt.timedelta(days=HORIZONTE_CIERRE)),
        key=lambda o: como_fecha(o["fecha_cierre"]))
    vigilancia = [o for o in oportunidades if o.get("estado") in ("recurrente", "cerrada")]
    prep = [p for p in preparacion if (p.get("convocatoria") or {}).get("estado") in ("abierta", "por_confirmar")]
    return por_revisar, por_cerrar, vigilancia, prep


def familias_de_la_semana(familias, hoy):
    """Rotación determinista: la semana ISO elige un bloque de familias."""
    ids = list(familias)
    bloques = [ids[i:i + FAMILIAS_POR_SEMANA] for i in range(0, len(ids), FAMILIAS_POR_SEMANA)]
    return bloques[hoy.isocalendar()[1] % len(bloques)]


def consultas_de_la_semana(portales, busqueda, hoy):
    valores = {"mes": MESES[hoy.month - 1], "anio": str(hoy.year)}
    familias = familias_de_la_semana(busqueda["familias"], hoy)
    salida = []
    for bolsa in portales["bolsas"]:
        if bolsa.get("estado") != "activa" or "busqueda_web" not in (bolsa.get("metodo"), bolsa.get("metodo_respaldo")):
            continue
        for fam in familias:
            semillas = busqueda["familias"][fam]
            # Las bolsas de empleo sólo reciben semillas de la ruta de cambio y prácticas
            # universitarias; nunca se buscan vacantes para menores.
            for palabra in semillas["ruta_cambio"][:1] + semillas["ruta_estudiante"][:1]:
                for plantilla in bolsa.get("consultas", []):
                    salida.append((bolsa["nombre"], fam, plantilla.format(palabra=palabra, **valores)))
    for grupo in ("empresas", "convocatorias"):
        for fuente in portales[grupo]:
            if fuente.get("estado") != "activa":
                continue
            for plantilla in fuente.get("consultas", []):
                salida.append((fuente["nombre"], "-", plantilla.format(**valores)))
    return familias, salida


# ---------------------------------------------------------------- vacantes

def ubicacion_valida(vacante, busqueda):
    texto = normalizar(vacante.get("location", ""))
    if any(contiene(texto, u) for u in busqueda["ubicaciones"]["mexico"]):
        return True
    return any(contiene(texto, u) for u in busqueda["ubicaciones"]["remoto_latam"])


def clasificar(vacante, busqueda):
    titulo = normalizar(vacante.get("title", ""))
    for tipo, patrones in busqueda["tipos"].items():
        if any(contiene(titulo, p) for p in patrones):
            return tipo
    return "otra"


def familia_de(vacante, busqueda):
    titulo = normalizar(vacante.get("title", ""))
    mejor, puntos = None, 0
    for fam, semillas in busqueda["familias"].items():
        palabras = {w for frase in semillas["ruta_cambio"] + semillas["ruta_estudiante"] for w in normalizar(frase).split()
                    if len(w) > 3 and w not in ("becario", "practicante", "tecnico", "junior", "trainee", "estudiantes")}
        coincidencias = sum(contiene(titulo, w) for w in palabras)
        if coincidencias > puntos:
            mejor, puntos = fam, coincidencias
    return mejor


def certificaciones_mencionadas(vacante, busqueda):
    texto = normalizar(vacante.get("title", "") + " " + (vacante.get("description") or ""))
    return sorted(cid for cid, patrones in busqueda["certificaciones"].items()
                  if any(contiene(texto, p) for p in patrones))


def analizar_vacantes(vacantes, busqueda):
    vistas, filtradas = set(), []
    for v in vacantes:
        if not v.get("title") or not v.get("url") or v["url"] in vistas:
            continue
        vistas.add(v["url"])
        if not ubicacion_valida(v, busqueda):
            continue
        filtradas.append({**v, "tipo": clasificar(v, busqueda), "familia": familia_de(v, busqueda),
                          "certificaciones": certificaciones_mencionadas(v, busqueda)})
    demanda = {}
    for v in filtradas:
        for cid in v["certificaciones"]:
            demanda[cid] = demanda.get(cid, 0) + 1
    return filtradas, dict(sorted(demanda.items(), key=lambda kv: (-kv[1], kv[0])))


# ---------------------------------------------------------------- reporte

def fila_opo(o, campo):
    return f"| `{o['id']}` | {o['nombre']} | {o.get('estado')} | {o.get(campo)} | <{o['fuente_url']}> |"


def reporte(hoy, datos, analisis=None):
    oportunidades, preparacion, portales, busqueda = datos
    por_revisar, por_cerrar, vigilancia, prep = agenda_directorio(oportunidades, preparacion, hoy)
    familias, consultas = consultas_de_la_semana(portales, busqueda, hoy)
    anio, semana, _ = hoy.isocalendar()
    l = [f"# Revisión semanal {anio}-S{semana:02d} ({hoy.isoformat()})", "",
         "> Generado por `scripts/semanal.py`. La sesión semanal completa las secciones marcadas "
         "*Por completar* siguiendo [docs/07-loop-semanal.md](../../docs/07-loop-semanal.md).", ""]

    l += ["## 1. Registros del directorio por verificar", "",
          f"Vencen en los próximos {HORIZONTE_REVISION} días o ya vencieron. Abrir la fuente oficial, "
          "actualizar `estado`, `fecha_cierre`, `fecha_verificacion` y `revisar_antes`.", ""]
    if por_revisar:
        l += ["| Id | Nombre | Estado | Revisar antes | Fuente |", "|---|---|---|---|---|"]
        l += [fila_opo(o, "revisar_antes") for o in por_revisar]
    else:
        l.append("Ninguno esta semana.")
    l.append("")

    l += [f"## 2. Convocatorias abiertas que cierran en {HORIZONTE_CIERRE} días", ""]
    if por_cerrar:
        l += ["| Id | Nombre | Estado | Cierre | Fuente |", "|---|---|---|---|---|"]
        l += [fila_opo(o, "fecha_cierre") for o in por_cerrar]
    else:
        l.append("Ninguna.")
    l.append("")

    l += ["## 3. Lista de vigilancia", "",
          "Recurrentes y cerradas: confirmar si abrió una nueva edición.", ""]
    l += [f"- `{o['id']}`: {o['nombre']} ({o['estado']}) <{o['fuente_url']}>" for o in vigilancia]
    l += [f"- `{p['id']}`: {p['nombre']} (convocatoria {p['convocatoria']['estado']}) <{p['fuente_url']}>" for p in prep]
    l.append("")

    l += ["## 4. Búsqueda de oportunidades nuevas", "",
          f"Familias de esta semana: {', '.join(f'`{f}`' for f in familias)}. "
          "Cada resultado se abre y se acepta sólo si la página oficial confirma fecha y requisitos.", "",
          "| Fuente | Familia | Consulta |", "|---|---|---|"]
    l += [f"| {fuente} | {fam} | `{consulta}` |" for fuente, fam, consulta in consultas]
    l.append("")

    if analisis is not None:
        filtradas, demanda = analisis
        l += ["## 5. Vacantes escaneadas (México y remoto LatAm)", "",
              f"{len(filtradas)} vacantes después de filtrar por ubicación.", ""]
        conteo = {}
        for v in filtradas:
            clave = (v["familia"] or "sin familia", v["tipo"])
            conteo[clave] = conteo.get(clave, 0) + 1
        l += ["| Familia | Tipo | Vacantes |", "|---|---|---|"]
        l += [f"| {f} | {t} | {n} |" for (f, t), n in sorted(conteo.items())]
        l += ["", "**Demanda observada de certificaciones** (vacantes que la mencionan):", ""]
        l += [f"- `{cid}`: {n}" for cid, n in demanda.items()] or ["- Ninguna mención esta semana."]
        l.append("")

    l += ["## Hallazgos nuevos", "", "*Por completar.* Oportunidades agregadas a `data/oportunidades.yaml` "
          "con id, fuente oficial y `revisar_antes`.", "",
          "## Cambios aplicados", "", "*Por completar.* Registros actualizados y motivo.", "",
          "## Pendientes para Victor", "", "*Por completar.* Sólo lo que requiere una decisión o un contacto humano.", ""]
    return "\n".join(l)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--hoy", type=dt.date.fromisoformat, default=dt.date.today())
    parser.add_argument("--vacantes", type=Path, help="JSON con vacantes en forma Job de career-ops")
    parser.add_argument("--escribir", action="store_true", help="guarda el reporte en reportes/semanal/")
    args = parser.parse_args()

    busqueda = leer("busqueda.yaml")
    datos = (leer("oportunidades.yaml"), leer("preparacion.yaml"), leer("portales.yaml"), busqueda)
    analisis = None
    if args.vacantes:
        vacantes = json.loads(args.vacantes.read_text(encoding="utf-8"))
        analisis = analizar_vacantes(vacantes, busqueda)
    texto = reporte(args.hoy, datos, analisis)
    if args.escribir:
        REPORTES.mkdir(parents=True, exist_ok=True)
        destino = REPORTES / f"{args.hoy.isoformat()}.md"
        destino.write_text(texto, encoding="utf-8")
        if analisis is not None:
            destino.with_suffix(".json").write_text(
                json.dumps({"vacantes": analisis[0], "demanda": analisis[1]}, ensure_ascii=False, indent=1),
                encoding="utf-8")
        print(f"Escrito: {destino.relative_to(RAIZ)}")
    else:
        print(texto)
    return 0


if __name__ == "__main__":
    sys.exit(main())
