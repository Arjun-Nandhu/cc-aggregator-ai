"""Initial migration - create all tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('first_name', sa.String(), nullable=True),
        sa.Column('last_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create institutions table
    op.create_table('institutions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plaid_institution_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('country', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('primary_color', sa.String(), nullable=True),
        sa.Column('logo', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_institutions_plaid_institution_id'), 'institutions', ['plaid_institution_id'], unique=True)

    # Create plaid_items table
    op.create_table('plaid_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plaid_item_id', sa.String(), nullable=False),
        sa.Column('plaid_access_token', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('institution_id', sa.Integer(), nullable=False),
        sa.Column('cursor', sa.String(), nullable=True),
        sa.Column('webhook_url', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_sync', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plaid_items_plaid_item_id'), 'plaid_items', ['plaid_item_id'], unique=True)

    # Create accounts table
    op.create_table('accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plaid_account_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('institution_id', sa.Integer(), nullable=False),
        sa.Column('plaid_item_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('official_name', sa.String(), nullable=True),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('subtype', sa.String(), nullable=False),
        sa.Column('mask', sa.String(), nullable=True),
        sa.Column('available_balance', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('current_balance', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('limit_balance', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('iso_currency_code', sa.String(), nullable=True),
        sa.Column('unofficial_currency_code', sa.String(), nullable=True),
        sa.Column('verification_status', sa.String(), nullable=True),
        sa.Column('persistent_account_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ),
        sa.ForeignKeyConstraint(['plaid_item_id'], ['plaid_items.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_accounts_plaid_account_id'), 'accounts', ['plaid_account_id'], unique=True)

    # Create transactions table
    op.create_table('transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plaid_transaction_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('iso_currency_code', sa.String(), nullable=True),
        sa.Column('unofficial_currency_code', sa.String(), nullable=True),
        sa.Column('category', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('category_id', sa.String(), nullable=True),
        sa.Column('merchant_name', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('original_description', sa.String(), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('authorized_date', sa.Date(), nullable=True),
        sa.Column('authorized_datetime', sa.DateTime(timezone=True), nullable=True),
        sa.Column('datetime', sa.DateTime(timezone=True), nullable=True),
        sa.Column('pending', sa.Boolean(), nullable=True),
        sa.Column('pending_transaction_id', sa.String(), nullable=True),
        sa.Column('account_owner', sa.String(), nullable=True),
        sa.Column('transaction_type', sa.String(), nullable=True),
        sa.Column('transaction_code', sa.String(), nullable=True),
        sa.Column('location', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('payment_meta', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('personal_finance_category', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ai_category', sa.String(), nullable=True),
        sa.Column('ai_sentiment', sa.String(), nullable=True),
        sa.Column('ai_tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ai_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transactions_plaid_transaction_id'), 'transactions', ['plaid_transaction_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_transactions_plaid_transaction_id'), table_name='transactions')
    op.drop_table('transactions')
    op.drop_index(op.f('ix_accounts_plaid_account_id'), table_name='accounts')
    op.drop_table('accounts')
    op.drop_index(op.f('ix_plaid_items_plaid_item_id'), table_name='plaid_items')
    op.drop_table('plaid_items')
    op.drop_index(op.f('ix_institutions_plaid_institution_id'), table_name='institutions')
    op.drop_table('institutions')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')