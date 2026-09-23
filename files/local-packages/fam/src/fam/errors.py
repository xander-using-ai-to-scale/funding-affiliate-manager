"""Error types for the Funding Affiliate Manager core."""


class FamError(Exception):
    """A rule, validation, or upstream failure the caller should see verbatim."""


class ApprovalRequired(FamError):
    """The requested action is outbound and must go through the approvals surface."""
