#!/usr/bin/env python3
"""Valida la base de conocimiento (data/*.yaml) y genera sus tablas legibles.

Uso:
    python3 scripts/catalogo.py              # valida; avisa de registros por revisar
    python3 scripts/catalogo.py --estricto   # los registros vencidos cuentan como error
    python3 scripts/catalogo.py --generar    # valida y reescribe docs/generado/*.md
    python3 scripts/catalogo.py --hoy 2026-12-01   # fecha de referencia (por defecto, hoy)

Reglas: docs/03-modelo-de-salida.md §3 y §6, y docs/05-catalogo.md §3.
"""
import argparse
import datetime as dt
import re
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "data"
GENERADO = RAIZ / "docs" / "generado"

# archivo -> (clave dentro del YAML o None si es lista, prefijos permitidos)
ARCHIVOS = {
    "familias.yaml": (None, ("fam-",)),
    "carreras.yaml": ("carreras", ("car-",)),
    "carreras.yaml#bachilleratos": ("bachilleratos", ("bach-",)),
    "certificaciones.yaml": (None, ("cert-",)),
    "preparacion.yaml": (None, ("prep-",)),
    "organizaciones.yaml": (None, ("org-",)),
    "oportunidades.yaml": (None, ("opo-",)),
}
NIVELES_DEMANDA = {"muy_alta", "alta", "media", "descenso"}
TIPOS_OPO = {"voucher", "descuento", "beca", "apoyo_economico", "reto", "voluntariado", "practicas", "programa"}
ESTADOS_OPO = {"abierta", "permanente", "recurrente", "cerrada", "por_confirmar"}
ESTADOS_CONV = {"abierta", "cerrada", "permanente", "por_confirmar"}
CAMPOS_REFERENCIA = ("familias", "organizacion", "organizaciones_aliadas", "aplica_a",
                     "prepara_para", "vias_ahorro", "preparacion")


def cargar():
    registros = {}
    for nombre, (clave, prefijos) in ARCHIVOS.items():
        archivo = DATOS / nombre.split("#")[0]
        contenido = yaml.safe_load(archivo.read_text(encoding="utf-8"))
        lista = contenido[clave] if clave else contenido
        registros[nombre] = (lista, prefijos)
    fuentes = yaml.safe_load((DATOS / "fuentes.yaml").read_text(encoding="utf-8"))
    return registros, {f["clave"]: f for f in fuentes}


def como_fecha(valor):
    if isinstance(valor, dt.date):
        return valor
    if isinstance(valor, str):
        try:
            return dt.date.fromisoformat(valor)
        except ValueError:
            return None
    return None


def validar(registros, fuentes, hoy, estricto):
    errores, avisos = [], []
    ids = {}

    for archivo, (lista, prefijos) in registros.items():
        for r in lista:
            rid = r.get("id", "<sin id>")
            donde = f"{archivo}:{rid}"
            if not rid.startswith(prefijos):
                errores.append(f"{donde}: el id debe empezar con {prefijos}")
            if rid in ids:
                errores.append(f"{donde}: id duplicado (también en {ids[rid][0]})")
            ids[rid] = (archivo, r)
            if not r.get("nombre"):
                errores.append(f"{donde}: falta 'nombre'")

            fecha = como_fecha(r.get("fecha_verificacion"))
            if fecha is None:
                errores.append(f"{donde}: 'fecha_verificacion' falta o no es AAAA-MM-DD")
            elif fecha > hoy:
                errores.append(f"{donde}: 'fecha_verificacion' está en el futuro")

            url = r.get("fuente_url")
            pendiente_org = rid.startswith("org-") and r.get("estado") == "pendiente"
            if url is None and not pendiente_org:
                errores.append(f"{donde}: falta 'fuente_url'")
            elif url is not None and not str(url).startswith(("http://", "https://")):
                errores.append(f"{donde}: 'fuente_url' no es una URL")

            revisar = como_fecha(r.get("revisar_antes"))
            if revisar and revisar < hoy:
                (errores if estricto else avisos).append(f"{donde}: vencido, revisar antes de {revisar}")

    for rid, (archivo, r) in ids.items():
        donde = f"{archivo}:{rid}"
        for campo in CAMPOS_REFERENCIA:
            valor = r.get(campo)
            for ref in ([valor] if isinstance(valor, str) else valor or []):
                if ref not in ids:
                    errores.append(f"{donde}: '{campo}' apunta a '{ref}', que no existe")

        if rid.startswith("fam-"):
            if r.get("nivel_demanda") not in NIVELES_DEMANDA:
                errores.append(f"{donde}: 'nivel_demanda' inválido")
            for s in r.get("senales", []):
                if s.get("fuente") not in fuentes:
                    errores.append(f"{donde}: la señal cita la fuente desconocida '{s.get('fuente')}'")

        if rid.startswith("cert-"):
            costo = r.get("costo") or {}
            if not isinstance(costo.get("verificado"), bool):
                errores.append(f"{donde}: 'costo.verificado' debe ser true o false")
            if costo.get("verificado") and (costo.get("monto") is None or not costo.get("fuente_url")):
                errores.append(f"{donde}: un costo verificado necesita 'monto' y 'costo.fuente_url'")
            if r.get("vigencia_meses") is None and r.get("no_caduca") is not True:
                avisos.append(f"{donde}: vigencia sin confirmar")
            if not costo.get("verificado"):
                avisos.append(f"{donde}: costo sin verificar en fuente oficial")

        if rid.startswith("opo-"):
            if r.get("tipo") not in TIPOS_OPO:
                errores.append(f"{donde}: 'tipo' inválido")
            if r.get("estado") not in ESTADOS_OPO:
                errores.append(f"{donde}: 'estado' inválido")
            if r.get("fuente_tipo") not in ("oficial", "secundaria"):
                errores.append(f"{donde}: 'fuente_tipo' debe ser oficial o secundaria")
            if r.get("fuente_tipo") == "secundaria" and r.get("estado") == "abierta":
                errores.append(f"{donde}: una fuente secundaria no basta para marcar 'abierta'")
            if r.get("estado") == "cerrada" and not r.get("fecha_cierre") and not r.get("nota"):
                errores.append(f"{donde}: una oportunidad cerrada necesita 'fecha_cierre' o 'nota'")
            cierre = como_fecha(r.get("fecha_cierre"))
            if r.get("estado") == "abierta" and cierre and cierre < hoy:
                (errores if estricto else avisos).append(f"{donde}: marcada abierta pero cerró el {cierre}")
            if not r.get("revisar_antes"):
                errores.append(f"{donde}: falta 'revisar_antes' (lo usa el loop semanal)")

        if rid.startswith("prep-"):
            conv = r.get("convocatoria") or {}
            if conv.get("estado") not in ESTADOS_CONV:
                errores.append(f"{donde}: 'convocatoria.estado' inválido")

    # Los id_catalogo usados como ejemplo en el contrato deben existir.
    contrato = (RAIZ / "docs" / "03-modelo-de-salida.md").read_text(encoding="utf-8")
    for ref in re.findall(r"id_catalogo:\s*([a-z]+-[a-z0-9-]+)", contrato):
        if ref not in ids:
            errores.append(f"docs/03: el ejemplo usa '{ref}', que no existe en el catálogo")

    return ids, errores, avisos


def puntaje_familias(ids, familias):
    return max((ids[f][1]["puntaje_demanda"] for f in familias if f in ids), default=0)


def fmt_costo(c):
    costo = c.get("costo") or {}
    if costo.get("monto") is None:
        return "Sin confirmar"
    texto = f"{costo['moneda']} {costo['monto']:,}"
    if costo.get("periodicidad") == "mensual":
        texto += "/mes"
    return texto if costo.get("verificado") else f"{texto} (no verificado)"


def fmt_vigencia(c):
    if c.get("no_caduca"):
        return "No caduca"
    if c.get("vigencia_meses"):
        meses = c["vigencia_meses"]
        return f"{meses // 12} años" if meses % 12 == 0 and meses >= 24 else f"{meses} meses"
    return "Sin confirmar"


def fmt_idioma(valor):
    return {True: "Sí", False: "No"}.get(valor, "Sin confirmar")


def fmt_edad(publico):
    minimo, maximo = publico.get("edad_min"), publico.get("edad_max")
    if minimo and maximo:
        return f"{minimo}–{maximo}"
    if minimo:
        return f"{minimo}+"
    return "—"


def enlace(texto, url):
    return f"[{texto}]({url})" if url else texto


def generar(ids, fuentes, hoy):
    GENERADO.mkdir(parents=True, exist_ok=True)
    por_prefijo = lambda p: [r for (_, r) in ids.values() if r["id"].startswith(p)]
    familias = sorted(por_prefijo("fam-"), key=lambda f: -f["puntaje_demanda"])
    orden_fam = {f["id"]: i for i, f in enumerate(familias)}
    aviso = (f"> Archivo generado por `scripts/catalogo.py --generar` el {hoy.isoformat()}. "
             "No editar a mano: editar `data/*.yaml`.\n")

    lineas = ["# Catálogo de carreras y certificaciones (generado)", "", aviso,
              "## Familias ocupacionales por demanda", "",
              "| # | Familia | Demanda | Puntaje | Señal principal | Fuente |",
              "|---|---|---|---|---|---|"]
    for i, f in enumerate(familias, 1):
        s = f["senales"][0]
        fuente = fuentes[s["fuente"]]
        lineas.append(f"| {i} | {f['nombre']} (`{f['id']}`) | {f['nivel_demanda'].replace('_', ' ')} | "
                      f"{f['puntaje_demanda']} | {s['dato']} | {enlace(fuente['titulo'], fuente['fuente_url'])} |")

    certs = sorted(por_prefijo("cert-"), key=lambda c: (
        -puntaje_familias(ids, c["familias"]),
        min(orden_fam.get(f, 99) for f in c["familias"]),
        c["nivel_escalera"],
        (c.get("costo") or {}).get("monto") or 10**6))
    lineas += ["", "## Certificaciones ordenadas por demanda", "",
               "Orden: puntaje de demanda de la familia, luego nivel de la escalera (1 = fundamentos) y costo.", "",
               "| # | Certificación | Familia | Nivel | Costo | Vigencia | Examen en español | Verificado |",
               "|---|---|---|---|---|---|---|---|"]
    for i, c in enumerate(certs, 1):
        fams = ", ".join(ids[f][1]["nombre"] for f in c["familias"][:1])
        lineas.append(f"| {i} | {enlace(c['nombre'], c['fuente_url'])} (`{c['id']}`) | {fams} | "
                      f"{c['nivel_escalera']} | {fmt_costo(c)} | {fmt_vigencia(c)} | "
                      f"{fmt_idioma(c.get('idioma_es'))} | {c['fecha_verificacion']} |")

    lineas += ["", "### Advertencias por certificación", ""]
    for c in certs:
        if c.get("advertencia"):
            lineas.append(f"- **{c['nombre']}:** {c['advertencia']}")

    carreras = sorted(por_prefijo("car-"), key=lambda c: (
        -puntaje_familias(ids, c["familias"]), -c["imco"]["ingreso_mensual_mxn"]))
    lineas += ["", "## Carreras (licenciatura y TSU)", "",
               "Cifras de la ficha de cada carrera en IMCO Compara Carreras. "
               "Referencia: ingreso promedio de la población ocupada, $14,170.", "",
               "| # | Carrera | Nivel | Ingreso mensual | Desempleo | Informalidad | Mujeres | Demanda de la familia |",
               "|---|---|---|---|---|---|---|---|"]
    for i, c in enumerate(carreras, 1):
        m = c["imco"]
        fam = ids[c["familias"][0]][1]
        lineas.append(f"| {i} | {enlace(c['nombre'], c['fuente_url'])} | {c['nivel'].upper() if c['nivel'] == 'tsu' else 'Licenciatura'} | "
                      f"${m['ingreso_mensual_mxn']:,} | {m['desempleo_pct']}% | {m['informalidad_pct']}% | "
                      f"{m['mujeres_pct']}% | {fam['nivel_demanda'].replace('_', ' ')} |")

    lineas += ["", "## Bachilleratos", ""]
    for b in por_prefijo("bach-"):
        lineas.append(f"- {enlace(b['nombre'], b['fuente_url'])} (`{b['id']}`): {b['nota']}")

    lineas += ["", "## Cursos y bootcamps de preparación", "",
               "| Programa | Organización | Costo para la persona | Duración | Edad | Convocatoria |",
               "|---|---|---|---|---|---|"]
    for p in por_prefijo("prep-"):
        pub = p.get("publico") or {}
        edad = fmt_edad(pub)
        costo = "Gratuito" if p.get("costo_participante") == 0 else "Sin confirmar"
        conv = p["convocatoria"]["estado"].replace("_", " ")
        if p["convocatoria"].get("proxima_fecha"):
            conv += f" (próximo inicio {p['convocatoria']['proxima_fecha']})"
        lineas.append(f"| {enlace(p['nombre'], p['fuente_url'])} | {ids[p['organizacion']][1]['nombre']} | "
                      f"{costo} | {p.get('duracion', '—')} | {edad} | {conv} |")
    (GENERADO / "catalogo.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    orden_estado = {"abierta": 0, "recurrente": 1, "permanente": 2, "por_confirmar": 3, "cerrada": 4}
    opos = sorted(por_prefijo("opo-"), key=lambda o: (
        0 if ids[o["organizacion"]][1].get("prioridad") == "socio" else 1,
        orden_estado[o["estado"]], o["nombre"]))
    lineas = ["# Directorio de oportunidades (generado)", "", aviso,
              "Orden: primero los socios prioritarios; después por estado (abierta, recurrente, permanente, "
              "por confirmar, cerrada).", "",
              "| Oportunidad | Tipo | Organización | Beneficio | Edad | Costo | Estado | Revisar antes de | Fuente |",
              "|---|---|---|---|---|---|---|---|---|"]
    for o in opos:
        pub = o.get("publico") or {}
        edad = fmt_edad(pub)
        if pub.get("genero") == "mujeres":
            edad += " (mujeres)"
        costo = {0: "Gratuito", None: "Sin confirmar"}.get(o.get("costo_participante"), f"USD {o.get('costo_participante')}")
        estado = o["estado"].replace("_", " ")
        if o.get("fecha_cierre"):
            estado += f" ({o['fecha_cierre']})"
        lineas.append(f"| {o['nombre']} (`{o['id']}`) | {o['tipo'].replace('_', ' ')} | "
                      f"{ids[o['organizacion']][1]['nombre']} | {o['beneficio']} | {edad} | {costo} | {estado} | "
                      f"{o['revisar_antes']} | {enlace(o['fuente_tipo'], o['fuente_url'])} |")

    pendientes = [r for (_, r) in ids.values() if r.get("estado") == "pendiente" or r.get("pendiente")]
    lineas += ["", "## Pendientes", ""]
    for r in pendientes:
        lineas.append(f"- `{r['id']}` · {r['nombre']}: {r.get('pendiente') or r.get('descripcion')}")
    (GENERADO / "directorio.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--estricto", action="store_true")
    parser.add_argument("--generar", action="store_true")
    parser.add_argument("--hoy", type=dt.date.fromisoformat, default=dt.date.today())
    args = parser.parse_args()

    registros, fuentes = cargar()
    ids, errores, avisos = validar(registros, fuentes, args.hoy, args.estricto)
    for a in avisos:
        print(f"AVISO  {a}")
    for e in errores:
        print(f"ERROR  {e}")
    conteo = {}
    for rid in ids:
        conteo[rid.split("-")[0]] = conteo.get(rid.split("-")[0], 0) + 1
    print("Registros: " + ", ".join(f"{k}={v}" for k, v in sorted(conteo.items())))
    if errores:
        print(f"{len(errores)} error(es).")
        return 1
    if args.generar:
        generar(ids, fuentes, args.hoy)
        print(f"Generado: {GENERADO.relative_to(RAIZ)}/catalogo.md y directorio.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
