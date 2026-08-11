"""auditoria de las acciones de la administracion de la plataforma

Revision ID: d5f1a3c7e2b9
Revises: c4e8a1b2d6f7
Create Date: 2026-08-11

Escrita a mano y no con autogenerate, como las demas: autogenerate compara contra la
base a la que apunte la configuracion, y la de desarrollo es SQLite mientras produccion
es Postgres.

`workshop_id` y `target_user_id` van sueltos, sin clave foranea: el registro de lo que
se le hizo a un taller tiene que quedar aunque ese taller ya no exista.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd5f1a3c7e2b9'
down_revision: Union[str, Sequence[str], None] = 'c4e8a1b2d6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'admin_audit',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('actor_user_id', sa.String(length=36), nullable=True),
        sa.Column('action', sa.String(length=40), nullable=False),
        sa.Column('workshop_id', sa.String(length=36), nullable=True),
        sa.Column('target_user_id', sa.String(length=36), nullable=True),
        sa.Column('detail', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], name='fk_admin_audit_actor_users'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_admin_audit_action', 'admin_audit', ['action'])
    op.create_index('ix_admin_audit_workshop_id', 'admin_audit', ['workshop_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_admin_audit_workshop_id', table_name='admin_audit')
    op.drop_index('ix_admin_audit_action', table_name='admin_audit')
    op.drop_table('admin_audit')
