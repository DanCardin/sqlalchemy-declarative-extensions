from pytest_mock_resources import create_mysql_fixture
from sqlalchemy import Column, Integer, text

from sqlalchemy_declarative_extensions import (
    Functions,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.dialects.mysql import (
    Function,
    FunctionDataAccess,
    FunctionSecurity,
)
from sqlalchemy_declarative_extensions.function.compare import compare_functions
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    functions = Functions().are(
        # Basic function
        Function(
            "gimme_count",
            """
            BEGIN
                DECLARE current_count INT;
                INSERT INTO foo (id) VALUES (DEFAULT);
                SELECT count(*) INTO current_count FROM foo;
                RETURN current_count;
            END
            """,
            returns="INTEGER",
            deterministic=False,  # Explicitly non-deterministic due to insert
            data_access=FunctionDataAccess.modifies_sql,
        ),
        # Function with parameters and deterministic
        Function(
            "add_deterministic",
            "RETURN i + 1;",
            parameters=["i integer"],
            returns="INTEGER",
            deterministic=True,
            data_access=FunctionDataAccess.no_sql,  # No SQL access
        ),
        # Complex function with multiple parameters and specific characteristics
        Function(
            "complex_processor",
            "RETURN CONCAT(label, ': ', CAST(val AS CHAR));",
            parameters=["val INT", "label VARCHAR(50)"],
            returns="VARCHAR(100)",
            deterministic=True,
            data_access=FunctionDataAccess.no_sql,
            security=FunctionSecurity.invoker,  # Explicitly set security
        ),
    )


class Foo(Base):
    __tablename__ = "foo"
    id = Column(Integer, primary_key=True, autoincrement=True)


register_sqlalchemy_events(Base.metadata, functions=True)

mysql = create_mysql_fixture(engine_kwargs={"echo": True}, session=True)


def test_create_mysql(mysql):
    # Required for MySQL function creation without SUPER privilege
    mysql.execute(text("SET GLOBAL log_bin_trust_function_creators = ON;"))

    Base.metadata.create_all(bind=mysql.connection())
    mysql.commit()

    # Test gimme_count
    result = mysql.execute(text("SELECT gimme_count()")).scalar()
    assert result == 1

    result = mysql.execute(text("SELECT gimme_count()")).scalar()
    assert result == 2

    # Test add_deterministic
    result_add = mysql.execute(text("SELECT add_deterministic(10)")).scalar()
    assert result_add == 11

    result_add_2 = mysql.execute(text("SELECT add_deterministic(1)")).scalar()
    assert result_add_2 == 2

    # Test complex_processor
    result_complex = mysql.execute(
        text("SELECT complex_processor(123, 'Test')")
    ).scalar()
    assert result_complex == "Test: 123"

    result_complex_2 = mysql.execute(
        text("SELECT complex_processor(45, 'Another')")
    ).scalar()
    assert result_complex_2 == "Another: 45"

    # Verify comparison
    connection = mysql.connection()
    diff = compare_functions(connection, Base.metadata.info["functions"])
    assert diff == [], f"Diff was: {diff}"  # Added detail to assertion
