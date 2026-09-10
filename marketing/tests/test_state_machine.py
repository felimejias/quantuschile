"""
Pruebas de Aceptación — Máquina de Estados (state_machine.py)
Verifica transiciones permitidas y prohibiciones explícitas.
Referencia: implementation_plan.md v2, §11, §16.4.
"""

import unittest
from marketing.state_machine import (
    can_transition, validate_transition,
    DRAFT, GENERATED, COMPLIANCE_REVIEW, COMPLIANCE_BLOCKED,
    HUMAN_REVIEW, CHANGES_REQUESTED, APPROVED, SCHEDULED,
    PUBLISHING, PUBLISHED, FAILED, CANCELLED, ARCHIVED,
)


class TestStateMachine(unittest.TestCase):

    def test_allowed_full_happy_path(self):
        # DRAFT -> GENERATED -> COMPLIANCE_REVIEW -> HUMAN_REVIEW -> APPROVED -> SCHEDULED -> PUBLISHING -> PUBLISHED -> ARCHIVED
        path = [
            (DRAFT, GENERATED),
            (GENERATED, COMPLIANCE_REVIEW),
            (COMPLIANCE_REVIEW, HUMAN_REVIEW),
            (HUMAN_REVIEW, APPROVED),
            (APPROVED, SCHEDULED),
            (SCHEDULED, PUBLISHING),
            (PUBLISHING, PUBLISHED),
            (PUBLISHED, ARCHIVED),
        ]
        for current, target in path:
            allowed, reason = can_transition(current, target)
            self.assertTrue(allowed, f"Transición {current} -> {target} debió ser permitida ({reason})")

    def test_prohibited_draft_to_published(self):
        allowed, reason = can_transition(DRAFT, PUBLISHED)
        self.assertFalse(allowed)
        self.assertIn("Salta todos los controles", reason)
        with self.assertRaises(ValueError):
            validate_transition(DRAFT, PUBLISHED)

    def test_prohibited_compliance_blocked_to_scheduled(self):
        allowed, reason = can_transition(COMPLIANCE_BLOCKED, SCHEDULED)
        self.assertFalse(allowed)
        self.assertIn("bloqueado por cumplimiento", reason)

    def test_prohibited_compliance_blocked_to_approved(self):
        allowed, reason = can_transition(COMPLIANCE_BLOCKED, APPROVED)
        self.assertFalse(allowed)

    def test_prohibited_changes_requested_to_published(self):
        allowed, reason = can_transition(CHANGES_REQUESTED, PUBLISHED)
        self.assertFalse(allowed)

    def test_prohibited_cancelled_to_publishing(self):
        allowed, reason = can_transition(CANCELLED, PUBLISHING)
        self.assertFalse(allowed)

    def test_archived_is_immutable(self):
        allowed, _ = can_transition(ARCHIVED, DRAFT)
        self.assertFalse(allowed)


if __name__ == "__main__":
    unittest.main()
