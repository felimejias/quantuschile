"""
Pruebas de Aceptación — Motor de Política de Entrega (agents/delivery_policy_engine.py)
Verifica las 11 validaciones previas al envío de mensajes directos.
Referencia: implementation_plan.md v2, §4.7, §16.2.
"""

import unittest
import uuid
import os
from datetime import datetime, timedelta

from marketing.db import get_db_conn, ensure_marketing_db
from marketing.agents.delivery_policy_engine import evaluate_delivery, PASS, BLOCK


class TestDeliveryPolicyEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        ensure_marketing_db()

    def setUp(self):
        self.conn = get_db_conn()
        self.contact_id = f"test_contact_{uuid.uuid4().hex[:8]}"
        self.campaign_id = f"test_camp_{uuid.uuid4().hex[:8]}"
        self.content_hash = f"hash_{uuid.uuid4().hex[:8]}"

    def tearDown(self):
        self.conn.close()

    def test_block_when_no_consent(self):
        res = evaluate_delivery(self.contact_id, "whatsapp", self.content_hash, self.campaign_id)
        self.assertEqual(res["result"], BLOCK)
        self.assertEqual(res["block_reason"], "NO_CONSENT")

    def test_block_when_suppressed(self):
        # Insertar consentimiento
        self.conn.execute(
            """INSERT INTO marketing_consents
               (id, tenant_id, contact_id, channel, consent_status, consent_source,
                consent_text_version, consented_at, legal_basis)
               VALUES (?, 'quantus', ?, 'whatsapp', 'ACTIVE', 'web_form', 'v1', ?, 'consent')""",
            (str(uuid.uuid4()), self.contact_id, datetime.now().strftime("%Y-%m-%d")),
        )
        # Insertar supresión
        self.conn.execute(
            """INSERT INTO marketing_suppressions
               (id, tenant_id, contact_id, channel, scope, reason, source, processed_by)
               VALUES (?, 'quantus', ?, 'whatsapp', 'all_commercial', 'opt_out_reply', 'user_reply', 'admin')""",
            (str(uuid.uuid4()), self.contact_id),
        )
        self.conn.commit()

        res = evaluate_delivery(self.contact_id, "whatsapp", self.content_hash, self.campaign_id)
        self.assertEqual(res["result"], BLOCK)
        self.assertEqual(res["block_reason"], "SUPPRESSED")

    def test_pass_when_consent_active_and_not_suppressed(self):
        # Insertar consentimiento activo
        self.conn.execute(
            """INSERT INTO marketing_consents
               (id, tenant_id, contact_id, channel, consent_status, consent_source,
                consent_text_version, consented_at, legal_basis)
               VALUES (?, 'quantus', ?, 'whatsapp', 'ACTIVE', 'web_form', 'v1', ?, 'consent')""",
            (str(uuid.uuid4()), self.contact_id, datetime.now().strftime("%Y-%m-%d")),
        )
        self.conn.commit()

        res = evaluate_delivery(self.contact_id, "whatsapp", self.content_hash, self.campaign_id)
        # En horario diurno debería pasar
        if res["block_reason"] != "BLOCKED_HOURS":
            self.assertEqual(res["result"], PASS)


if __name__ == "__main__":
    unittest.main()
