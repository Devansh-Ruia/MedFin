"""Initial migration - Create user and data tables

Revision ID: 0001
Revises: 
Create Date: 2025-11-23 23:43:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('hashed_password', sa.String(), nullable=False),
    sa.Column('full_name', sa.String(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create user_insurance table
    op.create_table('user_insurance',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('insurance_type', sa.String(), nullable=False),
    sa.Column('plan_name', sa.String(), nullable=True),
    sa.Column('deductible', sa.Float(), nullable=True),
    sa.Column('deductible_remaining', sa.Float(), nullable=True),
    sa.Column('out_of_pocket_max', sa.Float(), nullable=True),
    sa.Column('out_of_pocket_used', sa.Float(), nullable=True),
    sa.Column('coverage_percentage', sa.Float(), nullable=True),
    sa.Column('copay_primary', sa.Float(), nullable=True),
    sa.Column('copay_specialist', sa.Float(), nullable=True),
    sa.Column('copay_emergency', sa.Float(), nullable=True),
    sa.Column('in_network', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_insurance_id'), 'user_insurance', ['id'], unique=False)
    op.create_index(op.f('ix_user_insurance_user_id'), 'user_insurance', ['user_id'], unique=True)

    # Create saved_bills table
    op.create_table('saved_bills',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('bill_id', sa.String(), nullable=False),
    sa.Column('provider_name', sa.String(), nullable=False),
    sa.Column('service_date', sa.String(), nullable=False),
    sa.Column('services', sa.JSON(), nullable=False),
    sa.Column('total_amount', sa.Float(), nullable=False),
    sa.Column('insurance_paid', sa.Float(), nullable=True),
    sa.Column('patient_responsibility', sa.Float(), nullable=False),
    sa.Column('due_date', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_saved_bills_id'), 'saved_bills', ['id'], unique=False)

    # Create saved_navigation_plans table
    op.create_table('saved_navigation_plans',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('plan_data', sa.JSON(), nullable=False),
    sa.Column('current_financial_situation', sa.JSON(), nullable=False),
    sa.Column('projected_savings', sa.Float(), nullable=False),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_saved_navigation_plans_id'), 'saved_navigation_plans', ['id'], unique=False)

    # Create saved_cost_estimates table
    op.create_table('saved_cost_estimates',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('service_type', sa.String(), nullable=False),
    sa.Column('procedure_code', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('location', sa.String(), nullable=True),
    sa.Column('estimated_cost', sa.Float(), nullable=False),
    sa.Column('insurance_coverage', sa.Float(), nullable=True),
    sa.Column('patient_responsibility', sa.Float(), nullable=False),
    sa.Column('breakdown', sa.JSON(), nullable=False),
    sa.Column('confidence_score', sa.Float(), nullable=False),
    sa.Column('alternatives', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_saved_cost_estimates_id'), 'saved_cost_estimates', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_saved_cost_estimates_id'), table_name='saved_cost_estimates')
    op.drop_table('saved_cost_estimates')
    op.drop_index(op.f('ix_saved_navigation_plans_id'), table_name='saved_navigation_plans')
    op.drop_table('saved_navigation_plans')
    op.drop_index(op.f('ix_saved_bills_id'), table_name='saved_bills')
    op.drop_table('saved_bills')
    op.drop_index(op.f('ix_user_insurance_user_id'), table_name='user_insurance')
    op.drop_index(op.f('ix_user_insurance_id'), table_name='user_insurance')
    op.drop_table('user_insurance')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
