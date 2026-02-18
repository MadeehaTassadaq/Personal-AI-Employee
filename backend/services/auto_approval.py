"""Auto-approval rules for healthcare communications.

Defines which healthcare communications can be sent automatically
without requiring human approval via the vault workflow.
"""

import os
from enum import Enum
from typing import Optional


class AutoApprovalRule(Enum):
    """Auto-approval rules for healthcare communications.

    Rules marked as AUTO_APPROVED will bypass the vault approval workflow.
    Rules marked as REQUIRES_APPROVAL must go through Pending_Approval.
    """

    # Auto-approved: Routine administrative messages
    APPOINTMENT_CONFIRMATION = "appointment_confirmation"  # Auto-approve
    APPOINTMENT_REMINDER = "appointment_reminder"          # Auto-approve
    PATIENT_WELCOME = "patient_welcome"                    # Auto-approve
    APPOINTMENT_RESCHEDULE_CONFIRMATION = "appointment_reschedule_confirmation"  # Auto-approve

    # Requires approval: Clinical communications
    PRESCRIPTION_SEND = "prescription_send"                # Requires approval
    DIAGNOSIS_SEND = "diagnosis_send"                      # Requires approval
    TREATMENT_PLAN_SEND = "treatment_plan_send"            # Requires approval
    LAB_RESULTS_SEND = "lab_results_send"                  # Requires approval
    MEDICAL_ADVICE_SEND = "medical_advice_send"            # Requires approval

    # Requires approval: Sensitive communications
    EMERGENCY_SEND = "emergency_send"                      # Requires approval
    BILLING_INVOICE_SEND = "billing_invoice_send"          # Requires approval
    PAYMENT_REQUEST_SEND = "payment_request_send"          # Requires approval


class AutoApprovalConfig:
    """Configuration for auto-approval system."""

    def __init__(self):
        """Load configuration from environment variables."""
        self.auto_confirm_appointments = os.getenv("AUTO_CONFIRM_APPOINTMENTS", "true").lower() == "true"
        self.auto_onboard_patients = os.getenv("AUTO_ONBOARD_PATIENTS", "true").lower() == "true"
        self.auto_reminders_enabled = os.getenv("AUTO_REMINDERS_ENABLED", "true").lower() == "true"
        self.reminder_hours_24 = os.getenv("REMINDER_HOURS_24", "true").lower() == "true"
        self.reminder_hours_2 = os.getenv("REMINDER_HOURS_2", "true").lower() == "true"

        # Safety limits
        self.auto_approve_max_per_hour = int(os.getenv("AUTO_APPROVE_MAX_PER_HOUR", "50"))
        self.auto_approve_urgency_override = os.getenv("AUTO_APPROVE_URGENCY_OVERRIDE", "false").lower() == "true"

    def is_auto_approval_enabled(self, rule: AutoApprovalRule) -> bool:
        """Check if auto-approval is enabled for a specific rule.

        Args:
            rule: AutoApprovalRule to check

        Returns:
            True if auto-approval is enabled for this rule
        """
        # Global override - if set, everything requires approval
        if not self.auto_approve_urgency_override and _is_urgency_context():
            return False

        # Check specific feature flags
        if rule == AutoApprovalRule.APPOINTMENT_CONFIRMATION:
            return self.auto_confirm_appointments
        elif rule == AutoApprovalRule.PATIENT_WELCOME:
            return self.auto_onboard_patients
        elif rule == AutoApprovalRule.APPOINTMENT_REMINDER:
            return self.auto_reminders_enabled

        # For other rules, check if they're auto-approved by definition
        return rule in _AUTO_APPROVED_RULES


# Rules that are auto-approved by default
_AUTO_APPROVED_RULES = {
    AutoApprovalRule.APPOINTMENT_CONFIRMATION,
    AutoApprovalRule.APPOINTMENT_REMINDER,
    AutoApprovalRule.PATIENT_WELCOME,
    AutoApprovalRule.APPOINTMENT_RESCHEDULE_CONFIRMATION,
}


def is_auto_approved(
    message_type: str,
    urgency: str = "normal",
    patient_risk_category: str = "low"
) -> bool:
    """Check if a healthcare message should be auto-approved.

    Args:
        message_type: Type of message (e.g., "appointment_confirmation", "prescription_send")
        urgency: Message urgency (normal, urgent, emergency)
        patient_risk_category: Patient risk category (low, medium, high)

    Returns:
        True if message should be auto-approved

    Examples:
        >>> is_auto_approved("appointment_confirmation")
        True
        >>> is_auto_approved("prescription_send")
        False
        >>> is_auto_approved("appointment_confirmation", urgency="emergency")
        False
    """
    config = AutoApprovalConfig()

    # Emergency/urgent messages always require approval
    if urgency in ("urgent", "emergency"):
        return False

    # High-risk patients may require additional approval
    if patient_risk_category == "high" and message_type in ("APPOINTMENT_REMINDER",):
        # Still auto-send reminders but consider additional logging
        pass

    try:
        rule = AutoApprovalRule(message_type)
        return config.is_auto_approval_enabled(rule)
    except ValueError:
        # Unknown message type - require approval for safety
        return False


def _is_urgency_context() -> bool:
    """Check if current context requires urgency override.

    This could be expanded to check time of day, clinic status, etc.
    For now, returns False (no override).
    """
    return False


def get_auto_approval_rule(message_type: str) -> Optional[AutoApprovalRule]:
    """Get AutoApprovalRule enum for message type string.

    Args:
        message_type: Message type string

    Returns:
        AutoApprovalRule enum or None if not found
    """
    try:
        return AutoApprovalRule(message_type)
    except ValueError:
        return None


def can_auto_send_to_patient(patient_phone: str, patient_email: str) -> bool:
    """Check if we have valid contact info for auto-sending.

    Args:
        patient_phone: Patient phone number
        patient_email: Patient email address

    Returns:
        True if at least one valid contact method exists
    """
    return bool(patient_phone or patient_email)


# Global configuration instance
auto_approval_config = AutoApprovalConfig()


if __name__ == "__main__":
    # Test auto-approval rules
    print("Testing Auto-Approval Rules:")
    print(f"appointment_confirmation: {is_auto_approved('appointment_confirmation')}")
    print(f"appointment_reminder: {is_auto_approved('appointment_reminder')}")
    print(f"patient_welcome: {is_auto_approved('patient_welcome')}")
    print(f"prescription_send: {is_auto_approved('prescription_send')}")
    print(f"diagnosis_send: {is_auto_approved('diagnosis_send')}")
    print(f"emergency_send: {is_auto_approved('emergency_send')}")
    print(f"appointment_confirmation (urgent): {is_auto_approved('appointment_confirmation', urgency='urgent')}")
