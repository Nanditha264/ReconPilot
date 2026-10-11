from decimal import Decimal

import pytest
from app.db.seed import seed_database
from app.db.session import SessionLocal, check_db_connection
from app.models import (
    Payment,
    SettlementItem,
)
from sqlalchemy import text


@pytest.fixture(scope="module")
def db_session():
    """Yields a database session connected to live PostgreSQL if available."""
    connected, _ = check_db_connection()
    if not connected:
        pytest.skip("Live PostgreSQL database is not connected.")
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_postgresql_live_connection(db_session):
    """Verify live PostgreSQL 18 connection and version query."""
    version = db_session.execute(text("SELECT version()")).scalar()
    assert "PostgreSQL" in version
    assert "18" in version


def test_postgresql_tables_and_seed_data_counts(db_session):
    """Query live PostgreSQL database and confirm seeded record counts."""
    # Merchant
    merchants_count = db_session.execute(text("SELECT count(*) FROM merchants")).scalar()
    assert merchants_count >= 1

    # Payments
    payments_count = db_session.execute(text("SELECT count(*) FROM payments")).scalar()
    assert payments_count == 260

    # Settlements and Items
    settlements_count = db_session.execute(text("SELECT count(*) FROM settlements")).scalar()
    assert settlements_count == 63

    items_count = db_session.execute(text("SELECT count(*) FROM settlement_items")).scalar()
    assert items_count == 258

    # Benchmarks
    benchmarks_count = db_session.execute(text("SELECT count(*) FROM benchmark_cases")).scalar()
    assert benchmarks_count == 50


def test_postgresql_monetary_precision_and_decimal_types(db_session):
    """Query payment and settlement items from PostgreSQL and verify Decimal arithmetic precision."""
    sample_payment = db_session.query(Payment).first()
    assert sample_payment is not None
    assert isinstance(sample_payment.amount, Decimal)
    assert sample_payment.currency == "INR"

    sample_item = db_session.query(SettlementItem).first()
    assert sample_item is not None
    assert isinstance(sample_item.gross_amount, Decimal)
    assert isinstance(sample_item.net_amount, Decimal)


def test_postgresql_nullable_payment_id_for_missing_payment_exception(db_session):
    """Verify that settlement items can represent missing payments with NULL payment_id."""
    missing_payment_item = (
        db_session.query(SettlementItem).filter(SettlementItem.payment_id.is_(None)).first()
    )
    assert missing_payment_item is not None
    assert missing_payment_item.external_payment_id == "pay_missing_external"


def test_postgresql_seeder_idempotency(db_session):
    """Verify that re-running the seeder against live PostgreSQL does not insert duplicates."""
    counts = seed_database(db_session, verbose=False)
    for table_name, inserted_count in counts.items():
        assert inserted_count == 0, (
            f"Table {table_name} inserted {inserted_count} unexpected duplicate records"
        )
