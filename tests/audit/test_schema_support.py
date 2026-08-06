"""Tests for schema-aware audit function and trigger creation."""

from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    Schemas,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.audit import audit
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    schemas = Schemas().are("myschema", "otherschema")


# Test table with schema from __table_args__
@audit()
class Product(Base):
    __tablename__ = "product"
    __table_args__ = {"schema": "myschema"}

    id = Column(types.Integer(), primary_key=True)
    name = Column(types.Unicode())
    price = Column(types.Numeric())


# Test table with explicit schema parameter in @audit decorator
@audit(schema="otherschema")
class Order(Base):
    __tablename__ = "order"
    __table_args__ = {"schema": "myschema"}

    id = Column(types.Integer(), primary_key=True)
    product_id = Column(types.Integer())
    quantity = Column(types.Integer())


# Test table without schema (should use default)
@audit()
class Customer(Base):
    __tablename__ = "customer"

    id = Column(types.Integer(), primary_key=True)
    name = Column(types.Unicode())


register_sqlalchemy_events(Base.metadata, schemas=True, functions=True, triggers=True)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_audit_functions_in_table_schema(pg):
    """Test that audit functions are created in the same schema as the audited table."""
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    # Check that audit functions exist in myschema (for Product table)
    result = pg.execute(
        text(
            """
            SELECT routine_schema, routine_name
            FROM information_schema.routines
            WHERE routine_schema = 'myschema'
              AND routine_name LIKE '%product_audit%'
            ORDER BY routine_name
            """
        )
    ).fetchall()

    # Should have 3 functions: insert, update, delete
    assert len(result) == 3
    schemas = {r[0] for r in result}
    assert schemas == {"myschema"}

    function_names = {r[1] for r in result}
    assert function_names == {
        "myschema_product_audit_insert",
        "myschema_product_audit_update",
        "myschema_product_audit_delete",
    }


def test_audit_functions_with_explicit_schema(pg):
    """Test that audit functions respect explicit schema parameter in @audit decorator."""
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    # Check that audit functions exist in otherschema (explicit schema for Order)
    result = pg.execute(
        text(
            """
            SELECT routine_schema, routine_name
            FROM information_schema.routines
            WHERE routine_schema = 'otherschema'
              AND routine_name LIKE '%order_audit%'
            ORDER BY routine_name
            """
        )
    ).fetchall()

    # Should have 3 functions: insert, update, delete
    assert len(result) == 3
    schemas = {r[0] for r in result}
    assert schemas == {"otherschema"}


def test_audit_table_in_correct_schema(pg):
    """Test that audit tables are created in the correct schema."""
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    # Check Product audit table is in myschema
    result = pg.execute(
        text(
            """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema = 'myschema'
              AND table_name = 'product_audit'
            """
        )
    ).fetchall()

    assert len(result) == 1
    assert result[0] == ("myschema", "product_audit")

    # Check Order audit table is in otherschema (explicit schema)
    result = pg.execute(
        text(
            """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema = 'otherschema'
              AND table_name = 'order_audit'
            """
        )
    ).fetchall()

    assert len(result) == 1
    assert result[0] == ("otherschema", "order_audit")


def test_audit_triggers_reference_correct_functions(pg):
    """Test that triggers correctly reference schema-qualified function names."""
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    # Check Product triggers reference myschema functions
    result = pg.execute(
        text(
            """
            SELECT trigger_name, action_statement
            FROM information_schema.triggers
            WHERE event_object_schema = 'myschema'
              AND event_object_table = 'product'
            ORDER BY trigger_name
            """
        )
    ).fetchall()

    assert len(result) == 3

    # Each trigger should execute a function from myschema
    for trigger_name, action_statement in result:
        assert "myschema." in action_statement.lower(), (
            f"Trigger {trigger_name} should reference myschema-qualified function, "
            f"got: {action_statement}"
        )


def test_audit_functionality_with_schema(pg):
    """Integration test: verify audit trail works correctly with schema-qualified functions."""
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    # Insert a product
    product = Product(id=1, name="Widget", price=19.99)
    pg.add(product)
    pg.commit()

    # Check audit trail
    result = pg.execute(
        text(
            "SELECT audit_operation, name, price FROM myschema.product_audit ORDER BY audit_pk"
        )
    ).fetchall()

    assert len(result) == 1
    assert result[0][0] == "I"  # Insert operation
    assert result[0][1] == "Widget"
    assert float(result[0][2]) == 19.99

    # Update the product
    product.price = 24.99
    pg.commit()

    result = pg.execute(
        text(
            "SELECT audit_operation, name, price FROM myschema.product_audit ORDER BY audit_pk"
        )
    ).fetchall()

    assert len(result) == 2
    assert result[1][0] == "U"  # Update operation
    assert float(result[1][2]) == 24.99

    # Delete the product
    pg.delete(product)
    pg.commit()

    result = pg.execute(
        text("SELECT audit_operation FROM myschema.product_audit ORDER BY audit_pk")
    ).fetchall()

    assert len(result) == 3
    assert result[2][0] == "D"  # Delete operation


def test_audit_functions_default_schema(pg):
    """Test that audit functions work in default schema when no schema is specified."""
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    # Check that Customer audit functions exist in public schema
    result = pg.execute(
        text(
            """
            SELECT routine_schema, routine_name
            FROM information_schema.routines
            WHERE routine_schema = 'public'
              AND routine_name LIKE '%customer_audit%'
            ORDER BY routine_name
            """
        )
    ).fetchall()

    # Should have 3 functions: insert, update, delete
    assert len(result) == 3

    # Verify Customer audit works
    customer = Customer(id=1, name="John Doe")
    pg.add(customer)
    pg.commit()

    result = pg.execute(
        text(
            "SELECT audit_operation, name FROM public.customer_audit ORDER BY audit_pk"
        )
    ).fetchall()

    assert len(result) == 1
    assert result[0] == ("I", "John Doe")
