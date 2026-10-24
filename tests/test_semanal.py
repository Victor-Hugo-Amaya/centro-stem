"""Pruebas de scripts/semanal.py. Ejecutar: python3 -m unittest discover tests"""
import datetime as dt
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import semanal  # noqa: E402

BUSQUEDA = semanal.leer("busqueda.yaml")


def vacante(title, location="Guadalajara, Jalisco, México", description="", url=None):
    return {"title": title, "location": location, "description": description,
            "url": url or f"https://ejemplo.com/{title}", "company": "Ejemplo"}


class Vacantes(unittest.TestCase):
    def test_filtra_ubicacion(self):
        self.assertTrue(semanal.ubicacion_valida(vacante("x"), BUSQUEDA))
        self.assertTrue(semanal.ubicacion_valida(vacante("x", "Remote - LATAM"), BUSQUEDA))
        self.assertFalse(semanal.ubicacion_valida(vacante("x", "Madrid, Spain"), BUSQUEDA))
        self.assertFalse(semanal.ubicacion_valida(vacante("x", "Remote"), BUSQUEDA))
        # "Nuevo León" con acento debe coincidir con el patrón sin acento.
        self.assertTrue(semanal.ubicacion_valida(vacante("x", "Monterrey, Nuevo León"), BUSQUEDA))

    def test_clasifica_tipo(self):
        self.assertEqual(semanal.clasificar(vacante("Becario de Ingeniería"), BUSQUEDA), "practicas")
        self.assertEqual(semanal.clasificar(vacante("Data Analyst Jr"), BUSQUEDA), "vacante_entrada")
        self.assertEqual(semanal.clasificar(vacante("Senior Staff Engineer"), BUSQUEDA), "senior")
        self.assertEqual(semanal.clasificar(vacante("Ingeniero de procesos"), BUSQUEDA), "otra")

    def test_asigna_familia(self):
        self.assertEqual(semanal.familia_de(vacante("Analista de Ciberseguridad"), BUSQUEDA), "fam-ciberseguridad")
        self.assertEqual(semanal.familia_de(vacante("Técnico en Automatización PLC"), BUSQUEDA), "fam-manufactura-avanzada")

    def test_cuenta_certificaciones(self):
        v = vacante("Analista SOC", description="Deseable Security+ o CCNA; no pedimos CCNP.")
        self.assertEqual(semanal.certificaciones_mencionadas(v, BUSQUEDA),
                         ["cert-cisco-ccna", "cert-comptia-security-plus"])
        # "ccna" no debe coincidir dentro de otra palabra.
        self.assertEqual(semanal.certificaciones_mencionadas(vacante("x", description="ccnax"), BUSQUEDA), [])

    def test_deduplica_y_resume(self):
        lote = [vacante("Analista SOC", description="CCNA", url="https://a"),
                vacante("Analista SOC", description="CCNA", url="https://a"),
                vacante("Analista de datos", "Berlin", url="https://b")]
        filtradas, demanda = semanal.analizar_vacantes(lote, BUSQUEDA)
        self.assertEqual(len(filtradas), 1)
        self.assertEqual(demanda, {"cert-cisco-ccna": 1})


class Escaner(unittest.TestCase):
    def test_entradas_escaner(self):
        entradas = semanal.entradas_escaner(semanal.leer("portales.yaml"))
        proveedores = {e["provider"] for e in entradas}
        self.assertLessEqual(proveedores, {"greenhouse", "lever", "ashby", "workable", "computrabajo", "getonbrd"})
        self.assertNotIn("occ", proveedores)  # bloqueado fuera de México
        self.assertTrue(all(e["pais"] == "México" for e in entradas if e["provider"] == "computrabajo"))

    def test_acepta_salida_del_escaner(self):
        lote = [vacante("Analista SOC", description="CCNA", url="https://a")]
        filtradas, demanda = semanal.analizar_vacantes(lote, BUSQUEDA)
        datos = (semanal.leer("oportunidades.yaml"), semanal.leer("preparacion.yaml"), semanal.leer("portales.yaml"), BUSQUEDA)
        texto = semanal.reporte(dt.date(2026, 10, 26), datos,
                                (filtradas, demanda, [{"nombre": "Get on Board", "ok": False, "error": "HTTP 503"}]))
        self.assertIn("Get on Board: HTTP 503", texto)
        self.assertIn("`cert-cisco-ccna`: 1", texto)


NIVELES = {c["id"]: c["nivel_escalera"] for c in semanal.leer("certificaciones.yaml")}


class Requisitos(unittest.TestCase):
    def test_aws_sin_experiencia_recomienda_cloud_practitioner(self):
        r = semanal.recomendar({"titulo": "Becario de nube", "requisitos": "Conocimientos en AWS"}, BUSQUEDA, NIVELES)
        self.assertEqual(r["sugeridas"], ["cert-aws-clf-c02"])
        self.assertEqual(r["faltantes"], [])

    def test_gcp_con_experiencia_reporta_certificacion_faltante(self):
        r = semanal.recomendar({"titulo": "Cloud Engineer", "requisitos": "Más de 1 año en GCP",
                                "anios_experiencia": 2}, BUSQUEDA, NIVELES)
        self.assertEqual(r["sugeridas"], ["cert-google-cloud-digital-leader"])
        self.assertEqual(r["faltantes"], ["Google Cloud Associate Cloud Engineer"])

    def test_experiencia_sube_de_nivel(self):
        lectura = {"titulo": "Analista SOC", "requisitos": "Monitoreo SIEM"}
        self.assertEqual(semanal.recomendar(lectura, BUSQUEDA, NIVELES)["sugeridas"], ["cert-isc2-cc"])
        lectura["anios_experiencia"] = 1
        self.assertEqual(semanal.recomendar(lectura, BUSQUEDA, NIVELES)["sugeridas"], ["cert-comptia-security-plus"])

    def test_pedida_explicita_no_se_duplica_como_recomendada(self):
        r = semanal.recomendar({"titulo": "Soporte", "requisitos": "AWS Cloud Practitioner deseable"}, BUSQUEDA, NIVELES)
        self.assertEqual(r["explicitas"], ["cert-aws-clf-c02"])
        self.assertEqual(r["sugeridas"], [])

    def test_tecnologias_existen_en_catalogo(self):
        for tec in BUSQUEDA["tecnologias"].values():
            self.assertLessEqual(set(tec["certificaciones"]), set(NIVELES))

    def test_muestra_limita_empresa_y_rota_familias(self):
        lote = [{**vacante(f"Analista de datos {i}", url=f"https://d{i}"), "company": "Una", "tipo": "otra",
                 "familia": "fam-datos-ia"} for i in range(10)]
        lote += [{**vacante("Becario soporte técnico", url="https://s"), "tipo": "practicas", "familia": "fam-soporte-ti-redes"}]
        muestra = semanal.muestra_para_leer(lote, n=5)
        self.assertEqual(sum(v["company"] == "Una" for v in muestra), semanal.MAX_POR_EMPRESA)
        self.assertIn("https://s", [v["url"] for v in muestra])


    def test_reporte_avisa_si_la_muestra_es_pequena(self):
        datos = (semanal.leer("oportunidades.yaml"), semanal.leer("preparacion.yaml"), semanal.leer("portales.yaml"), BUSQUEDA)
        lecturas = [{"titulo": "Becario de nube", "requisitos": "AWS"}]
        texto = semanal.reporte(dt.date(2026, 10, 26), datos, None,
                                (lecturas, semanal.resumir_requisitos(lecturas, BUSQUEDA, NIVELES)))
        self.assertIn("tomar sólo como indicio", texto)
        self.assertIn("| `cert-aws-clf-c02` | 0 | 1 |", texto)


class Agenda(unittest.TestCase):
    def test_vencidos_y_cierres(self):
        hoy = dt.date(2026, 11, 1)
        opos = [
            {"id": "opo-a", "revisar_antes": dt.date(2026, 10, 30), "estado": "recurrente"},
            {"id": "opo-b", "revisar_antes": dt.date(2026, 11, 7), "estado": "permanente"},
            {"id": "opo-c", "revisar_antes": dt.date(2026, 12, 31), "estado": "abierta", "fecha_cierre": dt.date(2026, 11, 20)},
        ]
        por_revisar, por_cerrar, vigilancia, _ = semanal.agenda_directorio(opos, [], hoy)
        self.assertEqual([o["id"] for o in por_revisar], ["opo-a", "opo-b"])
        self.assertEqual([o["id"] for o in por_cerrar], ["opo-c"])
        self.assertEqual([o["id"] for o in vigilancia], ["opo-a"])

    def test_rotacion_cubre_todas_las_familias(self):
        vistas = set()
        for semana in range(3):
            vistas.update(semanal.familias_de_la_semana(BUSQUEDA["familias"], dt.date(2026, 11, 2) + dt.timedelta(weeks=semana)))
        self.assertEqual(vistas, set(BUSQUEDA["familias"]))

    def test_semillas_y_certificaciones_existen(self):
        familias = {f["id"] for f in semanal.leer("familias.yaml")}
        certs = {c["id"] for c in semanal.leer("certificaciones.yaml")}
        self.assertLessEqual(set(BUSQUEDA["familias"]), familias)
        self.assertLessEqual(set(BUSQUEDA["certificaciones"]), certs)

    def test_reporte_real_se_genera(self):
        texto = semanal.reporte(dt.date(2026, 10, 26), (semanal.leer("oportunidades.yaml"), semanal.leer("preparacion.yaml"),
                                                        semanal.leer("portales.yaml"), BUSQUEDA))
        self.assertIn("## 4. Búsqueda de oportunidades nuevas", texto)
        self.assertNotIn("BioCiencia", texto)
        self.assertNotIn("Regeni", texto)


if __name__ == "__main__":
    unittest.main()
