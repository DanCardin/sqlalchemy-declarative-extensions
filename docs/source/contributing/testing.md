# Testing

Similar to the actual library source itself, the tests are subdivided primarily
by "feature" (i.e. schema/view/grant/etc).

There are a couple of key organizational factors that should become apparent,
looking at the tests' folder structure:

```
tests/
    examples/
        test_view_create_pg/
        test_view_create_mysql/
        ...
    view/
        test_alembic.py
        test_materialized.py
        ...
    ...
```

## Alembic tests

Generally, alembic tests are much slower and more difficult to debug than
regular tests. Therefore they should be limited as much as possible to the
things required to get proper code-coverage of a feature within alembic.

When testing variants of a feature where the only difference would be equally
well tested when running a `metadata.create_all()` call, you're better off
avoiding alembic-based tests and using the "SQLAlchemy tests" examples below.

Now, to the details:

First, `examples/`. Due to the way alembic works internally, in order to test
the alembic integration, we need to have a whole "fake" alembic migrations
history in a standalone folder, so that we can see whether a given feature works
end-to-end once running inside alembic.

Therefore, each folder inside the `examples/` folder is a standalone pseudo
"project" with models, migrations, and tests. The tests for each pseudo-project
invoke pytest using [pytest-alembic](https://pytest-alembic.readthedocs.io/), in
order to run the alembic migrations against a real database.

These examples are invoked using Pytest's `pytester` fixture, which automates
the calling of the examples' pytest inline or in a subprocess.

All of the alembic/examples-based tests for a given feature live in
`tests/<feature>/test_alembic.py`:

```python
import pytest

from tests.utilities import successful_test_run

@pytest.mark.alembic
def test_view_create_pg(pytester):
    successful_test_run(pytester, count=1)
```

You'll notice the name of the test must exactly match the name of the
`examples/` folder's name.

For organization's sake, examples' names should look like
`test_<feature>_<test-purpose>_<dialect>/`.

## SQLAlchemy tests

By contrast to the alembic tests, they dont need a special way to be invoked.
One can just create a new `tests/<feature>/test_<what-am-i-testing>.py` and be
done.

What still may be different relative to most projects though, is that most
features of this library operate on a SQLAlchemy model-base/MetaData. So testing
mulitple different scenarios within a singlar test file is frequently more
challenging than it's worth.

Therefore you'll find that most test files contain exactly 1, or a couple of
test. If a test file has more than one test, it's frequently to test the same
"thing" against the different dialect options.

For example:

```python
import sqlalchemy
from pytest_mock_resources import create_postgres_fixture, create_sqlite_fixture

from sqlalchemy_declarative_extensions import (
    Schemas,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base


_Base = declarative_base()

@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    schemas = Schemas().are("fooschema")


class Foo(Base):
    __tablename__ = "foo"
    __table_args__ = {"schema": "fooschema"}

    id = sqlalchemy.Column(sqlalchemy.types.Integer(), primary_key=True)


register_sqlalchemy_events(Base.metadata, schemas=True)

pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})
sqlite = create_sqlite_fixture()


def test_createall_schema_pg(pg):
    Base.metadata.create_all(bind=pg)
    with pg.connect() as conn:
        result = conn.execute(Foo.__table__.select()).fetchall()
    assert result == []


def test_createall_schema_sqlite(sqlite):
    Base.metadata.create_all(bind=sqlite, checkfirst=False)
    with sqlite.connect() as conn:
        result = conn.execute(Foo.__table__.select()).fetchall()
    assert result == []
```
