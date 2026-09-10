"""
Pruebas de Aceptación — Agente de Cumplimiento (agents/compliance.py)
Referencia: implementation_plan.md v2, §16.2 (CMP-01 a CMP-08).
"""

import unittest
from marketing.agents.compliance import run_compliance_check
from marketing.claims_matrix import DISCLAIMER_TEXT


class TestComplianceAgent(unittest.TestCase):

    def test_cmp_01_blocked_100_garantizado(self):
        content = {
            "title": "Prueba",
            "body": "Nuestro servicio de Diario Oficial es 100% garantizado para tu pyme.",
            "channel": "instagram",
            "destination_url": "https://quantuschile.cl/do?utm_source=instagram&utm_medium=social&utm_campaign=test",
        }
        res = run_compliance_check(content, "diario_oficial")
        self.assertEqual(res["overall_status"], "BLOCKED")
        self.assertIn("100% garantizado", res["claims_blocked"])

    def test_cmp_02_blocked_somos_plataforma_oficial(self):
        content = {
            "title": "Prueba",
            "body": "Somos la plataforma oficial para remates en Chile. Quantus Chile SpA.",
            "channel": "facebook",
            "destination_url": "https://quantuschile.cl/remates?utm_source=facebook&utm_medium=social&utm_campaign=test",
        }
        res = run_compliance_check(content, "remates")
        self.assertEqual(res["overall_status"], "BLOCKED")

    def test_cmp_03_blocked_cumplimiento_certificado(self):
        content = {
            "title": "Prueba",
            "body": "Ofrecemos cumplimiento certificado en protección de datos con Quantus Chile SpA.",
            "channel": "linkedin",
            "destination_url": "https://quantuschile.cl/ley-21719?utm_source=linkedin&utm_medium=social&utm_campaign=test",
        }
        res = run_compliance_check(content, "ley_21719")
        self.assertEqual(res["overall_status"], "BLOCKED")

    def test_cmp_04_blocked_adjudicacion_licitacion(self):
        content = {
            "title": "Prueba",
            "body": "Quantus Chile SpA garantiza adjudicación de licitaciones a nuestros clientes.",
            "channel": "linkedin",
            "destination_url": "https://quantuschile.cl/licitaciones?utm_source=linkedin&utm_medium=social&utm_campaign=test",
        }
        res = run_compliance_check(content, "licitaciones")
        self.assertEqual(res["overall_status"], "BLOCKED")

    def test_cmp_pass_valid_content(self):
        content = {
            "title": "Monitoreo Diario Oficial",
            "body": f"Quantus Chile SpA monitorea publicaciones con agentes de IA configurados. {DISCLAIMER_TEXT}",
            "channel": "instagram",
            "destination_url": "https://quantuschile.cl/do?utm_source=instagram&utm_medium=social&utm_campaign=test",
        }
        res = run_compliance_check(content, "diario_oficial")
        self.assertEqual(res["overall_status"], "PASS")

    def test_cmp_08_visual_blocked_official_doc_prompt(self):
        content = {
            "title": "Test Visual",
            "body": f"Quantus Chile SpA. {DISCLAIMER_TEXT}",
            "channel": "instagram",
            "destination_url": "https://quantuschile.cl/do?utm_source=instagram&utm_medium=social&utm_campaign=test",
        }
        assets = [{"prompt_text": "Genera una imagen que simule un decreto oficial del diario oficial con firmas"}]
        res = run_compliance_check(content, "diario_oficial", assets=assets)
        self.assertEqual(res["overall_status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
