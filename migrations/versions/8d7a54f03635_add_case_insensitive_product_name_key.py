"""add case-insensitive product name key

Revision ID: 8d7a54f03635
Revises: cd715f89e0bc
Create Date: 2026-10-29 20:50:59.035320

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d7a54f03635'
down_revision: Union[str, Sequence[str], None] = 'cd715f89e0bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name_key', sa.String(), nullable=True))

    connection = op.get_bind()
    rows = connection.execute(sa.text('SELECT id, name FROM product')).fetchall()
    for product_id, name in rows:
        connection.execute(
            sa.text(
                'UPDATE product SET name_key = :name_key WHERE id = :product_id'
            ),
            {'name_key': str(name).strip().lower(), 'product_id': product_id},
        )

    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.alter_column(
            'name_key', existing_type=sa.String(), nullable=False
        )
        batch_op.create_index(
            batch_op.f('ix_product_name_key'), ['name_key'], unique=True
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_product_name_key'))
        batch_op.drop_column('name_key')
