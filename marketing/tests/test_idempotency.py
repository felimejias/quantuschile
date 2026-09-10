"""
Pruebas de Aceptación — Idempotencia (marketing_schedules)
Verifica que el idempotency_key prevenga publicaciones duplicadas.
Referencia: implementation_plan.md v2, §12, §16.3 (S-07).
"""

import unittest
import hashlib
import uuid
import sqlite3

from marketing.db import get_db_conn, ensure_marketing_db


class TestIdempotency(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        ensure_marketing_db()

    def setUp(self):
        self.conn = get_db_conn()
        self.campaign_id = str(uuid.uuid4())
        self.content_id = str(uuid.uuid4())

        # Insertar campaña y contenido dummy
        self.conn.execute(
            """INSERT INTO marketing_campaigns
               (id, tenant_id, name, service_category, flow_type, created_by)
               VALUES (?, 'quantus', 'Idempotency Test', 'diario_oficial', 'ORGANIC', 'admin')""",
            (self.campaign_id,),
        )
        self.conn.execute(
            """INSERT INTO marketing_contents
               (id, campaign_id, channel, flow_type, content_type, body, content_hash)
               VALUES (?, ?, 'instagram', 'ORGANIC', 'post', 'Test body', 'hash123')""",
            (self.content_id, self.campaign_id),
        )
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_s_07_idempotency_key_blocks_duplicates(self):
        scheduled_at = "2026-08-10T10:00:00"
        idempotency_key = hashlib.sha256(
            f"{self.campaign_id}{self.content_id}instagramquantus{scheduled_at}".encode()
        ).hexdigest()

        # Primer insert -> Exitoso
        self.conn.execute(
            """INSERT INTO marketing_schedules
               (id, content_id, flow_type, channel, scheduled_at, idempotency_key, content_hash)
               VALUES (?, ?, 'ORGANIC', 'instagram', ?, ?, 'hash123')""",
            (str(uuid.uuid4()), self.content_id, scheduled_at, idempotency_key),
        )
        self.conn.commit()

        # Segundo insert con la misma idempotency_key -> Debe fallar por UNIQUE constraint
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                """INSERT INTO marketing_schedules
                   (id, content_id, flow_type, channel, scheduled_at, idempotency_key, content_hash)
                   VALUES (?, ?, 'ORGANIC', 'instagram', ?, ?, 'hash123')""",
                (str(uuid.uuid4()), self.content_id, scheduled_at, idempotency_key),
            )


if __name__ == "__main__":
    unittest.main()
