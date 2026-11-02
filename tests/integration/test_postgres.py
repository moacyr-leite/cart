import os

import pytest
from sqlalchemy import inspect

pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)


def test_integration_database_is_postgresql(engine):
    assert engine.dialect.name == "postgresql"


def test_integration_database_has_alembic_version(engine):
    assert inspect(engine).has_table("alembic_version")
