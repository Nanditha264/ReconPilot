from decimal import Decimal

# Default monetary discrepancy tolerance in currency units (e.g. ₹1.00)
DEFAULT_AMOUNT_TOLERANCE = Decimal("1.00")

# Matching score threshold for high-confidence exact matches
STAGE1_CONFIDENCE = Decimal("1.0000")
STAGE2_CONFIDENCE = Decimal("0.9000")
STAGE3_CONFIDENCE = Decimal("0.7500")

# Default settlement window before a missing settlement is considered delayed (in days)
DEFAULT_SETTLEMENT_DELAY_DAYS = 2

# Max candidate window in days for controlled candidate matching
MAX_CANDIDATE_DATE_WINDOW_DAYS = 7
