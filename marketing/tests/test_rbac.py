"""
Pruebas de Aceptación — Control de Acceso RBAC (rbac.py)
Verifica roles, matriz de permisos y separación de funciones.
Referencia: implementation_plan.md v2, §10, §16.3.
"""

import unittest
from marketing.rbac import (
    has_permission, check_permission, can_approve_own_content,
    can_lift_compliance_block, validate_flow_b_permissions,
    MARKETING_VIEWER, MARKETING_EDITOR, MARKETING_APPROVER,
    MARKETING_PUBLISHER, COMPLIANCE_REVIEWER, MARKETING_ADMIN,
)


class TestRBAC(unittest.TestCase):

    def test_s_02_editor_cannot_approve(self):
        self.assertFalse(has_permission(MARKETING_EDITOR, "approve"))
        with self.assertRaises(PermissionError):
            check_permission(MARKETING_EDITOR, "approve")

    def test_s_02_approver_can_approve(self):
        self.assertTrue(has_permission(MARKETING_APPROVER, "approve"))

    def test_s_02_approver_cannot_publish(self):
        self.assertFalse(has_permission(MARKETING_APPROVER, "publish"))

    def test_s_03_editor_cannot_approve_own_content(self):
        allowed, msg = can_approve_own_content("user_123", "user_123", MARKETING_APPROVER)
        self.assertFalse(allowed)
        self.assertIn("separación de funciones", msg)

    def test_approver_can_approve_other_user_content(self):
        allowed, _ = can_approve_own_content("user_456", "user_123", MARKETING_APPROVER)
        self.assertTrue(allowed)

    def test_s_04_editor_cannot_lift_compliance_block(self):
        allowed, msg = can_lift_compliance_block(MARKETING_EDITOR)
        self.assertFalse(allowed)
        self.assertIn("COMPLIANCE_REVIEWER", msg)

    def test_compliance_reviewer_can_lift_block(self):
        allowed, _ = can_lift_compliance_block(COMPLIANCE_REVIEWER)
        self.assertTrue(allowed)

    def test_flow_b_requires_compliance_reviewer(self):
        allowed, _ = validate_flow_b_permissions(MARKETING_EDITOR)
        self.assertFalse(allowed)
        allowed, _ = validate_flow_b_permissions(COMPLIANCE_REVIEWER)
        self.assertTrue(allowed)


if __name__ == "__main__":
    unittest.main()
