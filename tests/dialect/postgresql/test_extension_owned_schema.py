from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import text

from sqlalchemy_declarative_extensions import Triggers
from sqlalchemy_declarative_extensions.dialects import get_triggers
from sqlalchemy_declarative_extensions.trigger.compare import compare_triggers

pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})

setup = """
CREATE EXTENSION hstore;
CREATE SCHEMA ext_owned;

INSERT INTO pg_depend
    (classid, objid, objsubid, refclassid, refobjid, refobjsubid, deptype)
SELECT 'pg_namespace'::regclass, n.oid, 0, 'pg_extension'::regclass, e.oid, 0, 'e'
FROM pg_namespace n, pg_extension e
WHERE n.nspname = 'ext_owned' AND e.extname = 'hstore';

CREATE FUNCTION gimme() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
RETURN NULL;
END
$$;

CREATE TABLE foo (id integer primary key);
CREATE TRIGGER on_insert_foo AFTER INSERT ON foo
FOR EACH ROW EXECUTE PROCEDURE gimme();

CREATE TABLE ext_owned.bar (id integer primary key);
CREATE TRIGGER on_insert_bar AFTER INSERT ON ext_owned.bar
FOR EACH ROW EXECUTE PROCEDURE gimme();
"""


def test_extension_owned_schema_only_excludes_triggers_on_own_tables(pg):
    with pg.connect() as connection:
        connection.execute(text(setup))
        connection.commit()
        
        trigger_names = [trigger.name for trigger in get_triggers(connection)]
        assert trigger_names == ["on_insert_foo"]

        diff = compare_triggers(connection, Triggers())

    diff_trigger_names = [op.trigger.name for op in diff]
    assert diff_trigger_names == ["on_insert_foo"]
