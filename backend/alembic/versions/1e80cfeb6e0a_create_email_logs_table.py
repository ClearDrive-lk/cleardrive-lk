"""create email_logs table

Revision ID: 1e80cfeb6e0a
Revises: a7837696f581
Create Date: 2026-01-29 00:19:56.867887

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1e80cfeb6e0a'
down_revision: Union[str, None] = 'a7837696f581'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# backend/alembic/versions/XXXXX_create_email_logs.py
"""create email_logs table

Revision ID: create_email_logs_v1
Revises: 
Create Date: 2026-01-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_email_logs_v1'
down_revision = None  # Update this to the previous migration ID
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create email_status enum
    email_status_enum = postgresql.ENUM(
        'PENDING', 'QUEUED', 'SENDING', 'SENT', 'FAILED', 'RETRY',
        name='emailstatus',
        create_type=False
    )
    email_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create email_logs table
    op.create_table(
        'email_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recipient_email', sa.String(length=255), nullable=False),
        sa.Column('recipient_name', sa.String(length=255), nullable=True),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('template_name', sa.String(length=100), nullable=False),
        sa.Column('status', email_status_enum, nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('last_attempt_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('template_data_summary', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_email_logs_recipient_email', 'email_logs', ['recipient_email'])
    op.create_index('idx_email_logs_status', 'email_logs', ['status'])
    op.create_index('idx_email_status_created', 'email_logs', ['status', 'created_at'])
    op.create_index('idx_email_recipient_created', 'email_logs', ['recipient_email', 'created_at'])
    
    # Add trigger for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_email_logs_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    op.execute("""
        CREATE TRIGGER update_email_logs_updated_at
            BEFORE UPDATE ON email_logs
            FOR EACH ROW
            EXECUTE FUNCTION update_email_logs_updated_at();
    """)


def downgrade() -> None:
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_email_logs_updated_at ON email_logs;")
    op.execute("DROP FUNCTION IF EXISTS update_email_logs_updated_at();")
    
    # Drop indexes
    op.drop_index('idx_email_recipient_created', table_name='email_logs')
    op.drop_index('idx_email_status_created', table_name='email_logs')
    op.drop_index('idx_email_logs_status', table_name='email_logs')
    op.drop_index('idx_email_logs_recipient_email', table_name='email_logs')
    
    # Drop table
    op.drop_table('email_logs')
    
    # Drop enum
    sa.Enum(name='emailstatus').drop(op.get_bind(), checkfirst=True)
