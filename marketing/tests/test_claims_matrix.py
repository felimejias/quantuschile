"""
Pruebas de Aceptación — Matriz de Claims (claims_matrix.py)
Verifica claims permitidos y prohibidos por servicio, y frases universalmente bloqueadas.
Referencia: implementation_plan.md v2, §8, §16.
"""

import unittest
from marketing.claims_matrix import check_text_compliance, UNIVERSALLY_BLOCKED_PHRASES, DISCLAIMER_TEXT


class TestClaimsMatrix(unittest.TestCase):

    def test_universally_blocked_100_garantizado(self):
        res = check_text_compliance("Servicio con 100% garantizado de éxito", "diario_oficial")
        self.assertEqual(res["status"], "BLOCKED")
        self.assertIn("100% garantizado", res["blocked_phrases"])

    def test_universally_blocked_somos_plataforma_oficial(self):
        res = check_text_compliance("Somos la plataforma oficial del estado", "licitaciones")
        self.assertEqual(res["status"], "BLOCKED")

    def test_universally_blocked_cumplimiento_certificado(self):
        res = check_text_compliance("Ofrecemos cumplimiento certificado en datos", "ley_21719")
        self.assertEqual(res["status"], "BLOCKED")

    def test_blocked_service_claim_licitaciones_adjudicacion(self):
        res = check_text_compliance("Nuestra herramienta garantiza adjudicación de licitaciones", "licitaciones")
        self.assertEqual(res["status"], "BLOCKED")

    def test_blocked_service_claim_inapi_registro(self):
        res = check_text_compliance("Quantus garantiza el registro de la marca ante INAPI", "inapi")
        self.assertEqual(res["status"], "BLOCKED")

    def test_allowed_service_claim_diario_oficial(self):
        text = f"Quantus Chile SpA monitorea criterios configurados y alerta coincidencias. {DISCLAIMER_TEXT}"
        res = check_text_compliance(text, "diario_oficial")
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(len(res["blocked_phrases"]), 0)

    def test_disclaimer_warning_when_mentioning_public_org(self):
        text = "Quantus Chile SpA revisa publicaciones del Diario Oficial para tu empresa."
        res = check_text_compliance(text, "diario_oficial")
        self.assertTrue(res["needs_disclaimer"])
        self.assertEqual(res["status"], "WARNING")


if __name__ == "__main__":
    unittest.main()
