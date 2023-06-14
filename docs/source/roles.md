# Roles

Due to the inconsistent set of available options there are dialect-specific role
implementations. [Role](sqlalchemy_declarative_extensions.role.generic.Role)
exists as a lowest common denominator, to create a role without any
dialect-specific options. For more complex roles, there exist alternative
implementations like
[Role](sqlalchemy_declarative_extensions.dialects.postgresql.role.Role).

```python
from sqlalchemy_declarative_extensions import Roles, Role

roles = Roles(ignore_roles=["user"]).are(
    "read",
    Role("admin", in_roles=["read"]),
)
```

```{eval-rst}
.. autoapimodule:: sqlalchemy_declarative_extensions.role.base
   :members: Roles, Role
   :noindex:
```

## Pytest-Alembic Compatibility

Compatibility with the [pytest-alembic](https://pytest-alembic.readthedocs.io/)
plugin is absolutely a goal of this library. Laterally,
[pytest-mock-resources](https://pytest-mock-resources.readthedocs.io/) is also a
consideration, in that one of the proposed solutions utilizes this library.

In point of fact, we use both libraries, internally, to test this whole library,
so they absolutely **do** work! Roles, however, present a unique problem,
relative to the set of other database objects supported by this library. Every
other object type is local to a single database on a given database instance,
whereas roles are global to the instance.

Basically, tests involving roles **may** need more test isolation than is
necessary by default. When running pytest-alembic, you might encounter issues
relating to your roles already existing, caused by their global nature.

You have at least a couple of options.

1. Use literally different database instances among these tests.

   If you're using `pytest-mock-resources`, like this library is, you could do
   something like:

   ```python
   # test_migrations.py
   from pytest_mock_resources import PostgresConfig, create_postgres_config
   from pytest_mock_resources.container.base import get_container

   @pytest.fixture(scope="function")
   def postgres_config():
       return PostgresConfig(port=None)

   @pytest.fixture(scope="function")
   def pmr_postgres_container(pytestconfig, pmr_postgres_config: PostgresConfig):
       yield from get_container(pytestconfig, pmr_postgres_config)

   alembic_engine = create_postgres_config()

   from pytest_alembic.tests import test_model_definitions_match_ddl, test_up_down_consistency, test_upgrade, test_downgrade
   ```

   - `scope="function"` will cause tests within this file to spin up a new
     database instance for each individual test (primarily important to
     `pmr_postgres_container`).

     Essentially it's telling pytest-mock-resources that the fixture is not
     "session" scoped, which will cause the evaluation of the fixture to occur
     on each test.

   - `port=None` will cause the new database instances to choose a unique,
     unused port.

     This is useful particularly if you're running your tests in
     parallel/concurrently. Basically it's a way to guarantee the tests dont try
     to attach to a preexisting database a former test had already used.

     This isn't **strictly** necessary, you could instead run your migrations
     tests with a separate fixed port, or on a separate `pytest` invocation.
     Whatever makes sense for your project.

2. Make role creation/dropping statements immune to failure.

   `sqlalchemy-declarative-extensions` is going to emit vanilla `CREATE ROLE`
   statements by default. However, in certain databases you can write the SQL in
   such a way that it wont fail if the role being created already exists.

   For example, in Postgres, you could do something like:

   ```postgresql
   DO $$
     BEGIN
       CREATE ROLE rolename;
       EXCEPTION WHEN OTHERS THEN
       RAISE NOTICE 'not creating role';
     END
   $$;
   ```

   Note though, this still **can** fail, depending on the operations your
   migrations are performing. Some series of `CREATE ROLE` and `DROP ROLE`
   statements with different alterations role roles/permissions, over the course
   of migrations history certainly **could** affect the end-permissions attached
   to a given role. **Particularly** if you're running tests in parallel.

3. Some other mechanism?

   Option 1 assumes you're using pytest-mock-resources, option 2 somewhat
   assumes you're using Postgres.

   Depending on your exact test setup, there may be more or less you can do.
   Feel free to reach out in an issue if there's something you think **this**
   library could be doing to enable your usecase.
