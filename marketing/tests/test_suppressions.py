"""
Pruebas de Aceptación — Lista de Supresión Global (marketing_suppressions)
Verifica que las supresiones bloqueen envíos y soporten distintos ámbitos (scopes) y razones.
Referencia: implementation_plan.md v2, §4.3, §5, §16.3.
"""

import unittest
import uuid
from datetime import datetime

from marketing.db import get_db_conn, ensure_marketing_db


class TestSuppressions(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        ensure_marketing_db()

    def setUp(self):
        self.conn = get_db_conn()
        self.contact_id = f"contact_{uuid.uuid4().hex[:8]}"

    def tearDown(self):
        self.conn.close()

    def test_add_and_query_suppression_by_phone(self):
        phone = "+56912345678"
        self.conn.execute(
            """INSERT INTO marketing_suppressions
               (id, tenant_id, contact_id, normalized_phone, channel, scope, reason, source, processed_by)
               VALUES (?, 'quantus', ?, ?, 'whatsapp', 'all_commercial', 'opt_out_reply', 'user_reply', 'system')""",
            (str(uuid.uuid4()), self.contact_id, phone),
        )
        self.conn.commit()

        row = self.conn.execute(
            "SELECT * FROM marketing_suppressions WHERE normalized_phone = ? AND revoked_at IS NULL",
            (phone,),
        ).fetchone()

        self.assertIsNotNone(row)
        self.assertEqual(row["scope"], "all_commercial")
        self.assertEqual(row["reason"], "opt_out_reply")

    def test_revoked_suppression_is_not_active(self):
        phone = "+56987654321"
        supp_id = str(uuid.uuid4())
        self.conn.execute(
            """INSERT INTO marketing_suppressions
               (id, tenant_id, contact_id, normalized_phone, channel, scope, reason, source, processed_by)
               VALUES (?, 'quantus', ?, ?, 'all', 'all_commercial', 'opt_out_link', 'web_form', 'admin')""",
            (supp_id, self.contact_id, phone),
        )
        self.conn.commit()

        # Revocar la supresión
        self.conn.execute(
            "UPDATE marketing_suppressions SET revoked_at = ? WHERE id = ?",
            (datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), supp_id),
        )
        self.conn.commit()

        row = self.conn.execute(
            "SELECT * FROM marketing_suppressions WHERE normalized_phone = ? AND revoked_at IS NULL",
            (phone,),
        ).fetchone()

        self.assertIsNone(row)


if __name__ == "__main__":
    unittest.main()
