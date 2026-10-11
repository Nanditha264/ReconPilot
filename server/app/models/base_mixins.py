import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated

from sqlalchemy import DateTime, Numeric, String, Uuid
from sqlalchemy.orm import mapped_column

# Primary key UUID column generator
uuid_pk = Annotated[
    uuid.UUID,
    mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4),
]

# Standard UTC datetime columns
timestamp_utc = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    ),
]

# Standard financial currency code column
currency_code = Annotated[
    str,
    mapped_column(String(3), nullable=False, default="INR"),
]

# Standard financial amount column (Numeric 20, 2)
money_amount = Annotated[
    Decimal,
    mapped_column(Numeric(20, 2), nullable=False),
]
