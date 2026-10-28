import enum

import pytest

from sqlalchemy_declarative_extensions.dialects import mysql, postgresql
from sqlalchemy_declarative_extensions.dialects.from_string import FromStrings


def test_from_string_accepts_the_sql_keyword_in_either_case():
    assert postgresql.FunctionVolatility.from_string("STABLE") is (
        postgresql.FunctionVolatility.stable
    )
    assert postgresql.FunctionVolatility.from_string("stable") is (
        postgresql.FunctionVolatility.stable
    )


def test_from_string_passes_members_through():
    assert postgresql.FunctionSecurity.from_string(
        postgresql.FunctionSecurity.definer
    ) is (postgresql.FunctionSecurity.definer)


def test_from_string_rejects_unknown_strings():
    with pytest.raises(ValueError):
        postgresql.FunctionVolatility.from_string("perhaps")


@pytest.mark.parametrize("module", [postgresql, mysql])
def test_every_dialect_enum_is_a_fromstrings(module):
    """Guard against a future enum being added without string coercion."""
    for name in module.__all__:
        obj = getattr(module, name)
        if isinstance(obj, type) and issubclass(obj, enum.Enum):
            assert issubclass(
                obj, FromStrings
            ), f"{module.__name__}.{name} should subclass FromStrings"


def test_postgresql_function_coerces_strings():
    function = postgresql.Function(
        "f",
        "SELECT 1;",
        returns="INTEGER",
        volatility="stable",
        parallel="safe",
        security="definer",
    )

    assert function.volatility is postgresql.FunctionVolatility.stable
    assert function.parallel is postgresql.FunctionParallel.safe
    assert function.security is postgresql.FunctionSecurity.definer

    assert function == postgresql.Function(
        "f",
        "SELECT 1;",
        returns="INTEGER",
        volatility=postgresql.FunctionVolatility.stable,
        parallel=postgresql.FunctionParallel.safe,
        security=postgresql.FunctionSecurity.definer,
    )

    (create,) = function.normalize().to_sql_create()
    assert "SECURITY DEFINER" in create
    assert "STABLE" in create
    assert "PARALLEL SAFE" in create


def test_postgresql_function_with_builders_accept_strings():
    function = postgresql.Function("f", "SELECT 1;", returns="INTEGER")

    assert function.with_volatility("immutable").volatility is (
        postgresql.FunctionVolatility.immutable
    )
    assert function.with_parallel("restricted").parallel is (
        postgresql.FunctionParallel.restricted
    )
    assert function.with_security("definer").security is (
        postgresql.FunctionSecurity.definer
    )


def test_postgresql_function_builders_accept_uppercase_aliases():
    function = postgresql.Function("f", "SELECT 1;", returns="INTEGER")

    assert function.with_volatility(
        postgresql.FunctionVolatility.IMMUTABLE
    ).volatility is (postgresql.FunctionVolatility.immutable)
    assert function.with_parallel(postgresql.FunctionParallel.RESTRICTED).parallel is (
        postgresql.FunctionParallel.restricted
    )


@pytest.mark.parametrize(
    "obj, builder, value, attr, expected",
    [
        (
            mysql.Function("f", "RETURN 1;", returns="INTEGER"),
            "with_security",
            "invoker",
            "security",
            mysql.FunctionSecurity.invoker,
        ),
        (
            mysql.Function("f", "RETURN 1;", returns="INTEGER"),
            "with_data_access",
            "reads sql data",
            "data_access",
            mysql.FunctionDataAccess.reads_sql,
        ),
        (
            mysql.Procedure("p", "SELECT 1;"),
            "with_security",
            "invoker",
            "security",
            mysql.ProcedureSecurity.invoker,
        ),
        (
            postgresql.Procedure("p", "SELECT 1;"),
            "with_security",
            "definer",
            "security",
            postgresql.ProcedureSecurity.definer,
        ),
    ],
)
def test_builders_accept_strings(
    obj: object, builder: str, value: str, attr: str, expected: enum.Enum
):
    assert getattr(getattr(obj, builder)(value), attr) is expected


def test_postgresql_procedure_coerces_strings():
    procedure = postgresql.Procedure("p", "SELECT 1;", security="definer")

    assert procedure.security is postgresql.ProcedureSecurity.definer
    assert "SECURITY DEFINER" in procedure.to_sql_create()[0]


def test_postgresql_trigger_coerces_strings_on_direct_construction():
    """Direct construction never coerced; only the before/after classmethods did."""
    trigger = postgresql.Trigger(
        name="t",
        time="before",
        events=["insert", "update"],
        for_each="row",
        on="foo",
        execute="bar",
    )

    assert trigger.time is postgresql.TriggerTimes.before
    assert trigger.events == [
        postgresql.TriggerEvents.insert,
        postgresql.TriggerEvents.update,
    ]
    assert trigger.for_each is postgresql.TriggerForEach.row

    create = trigger.to_sql_create()
    assert "BEFORE INSERT OR UPDATE" in create
    assert "FOR EACH ROW" in create


def test_mysql_function_coerces_strings():
    function = mysql.Function(
        "f",
        "RETURN 1;",
        returns="INTEGER",
        data_access="no sql",
        security="invoker",
    )

    assert function.data_access is mysql.FunctionDataAccess.no_sql
    assert function.security is mysql.FunctionSecurity.invoker

    (create,) = function.to_sql_create()
    assert "NO SQL" in create
    assert "SQL SECURITY INVOKER" in create


def test_mysql_procedure_coerces_strings():
    procedure = mysql.Procedure("p", "SELECT 1;", security="invoker")

    assert procedure.security is mysql.ProcedureSecurity.invoker
    assert "SQL SECURITY INVOKER" in procedure.to_sql_create()[0]


def test_mysql_trigger_coerces_strings():
    trigger = mysql.Trigger(
        name="t", time="after", event="delete", on="foo", execute="bar"
    )

    assert trigger.time is mysql.TriggerTimes.after
    assert trigger.event is mysql.TriggerEvents.delete

    ordered = trigger.follows("other")
    assert ordered.order is not None
    assert ordered.order.order is mysql.TriggerOrders.follows

    assert "AFTER DELETE" in ordered.to_sql_create()


def test_coercion_survives_dataclass_replace():
    """`normalize` and every `with_*` builder re-run `__post_init__`."""
    function = postgresql.Function(
        "f", "SELECT 1;", returns="INTEGER", volatility="stable"
    ).normalize()

    assert function.volatility is postgresql.FunctionVolatility.stable
