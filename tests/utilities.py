from sqlalchemy import text
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.elements import TextClause


def clear_roles(engine):
    roles = engine.execute(
        text(
            "SELECT rolname from pg_roles "
            "WHERE rolname != 'user' "
            "AND rolname not like 'pg_%'"
            "ORDER BY rolname"
        )
    )

    connected_name = engine.pmr_credentials.username
    for role, *_ in roles:
        engine.execute(text(f'REASSIGN OWNED BY {role} TO "{connected_name}"'))
        engine.execute(text(f"DROP ROLE {role}"))


def render_sql(text: TextClause) -> str:
    statement = text.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": True},
    )
    return str(statement)


def successful_test_run(pytester, *, count=None, skipped_count=0):
    pytester.copy_example()
    result = pytester.runpytest_inprocess(
        "-vv",
        "--log-cli-level=WARNING",
        "--log-level=WARNING",
    )
    result.assert_outcomes(passed=count, skipped=skipped_count, failed=0)
