# Changelog

## 0.15

### 0.15.13
- fix: sqlalchemy<2 import-time regression.

### 0.15.12
- fix: Enable registering zero objects (enable without declaring anything).
- fix: Add explicit relkind casts to ensure compatibility with postgres 11.
- fix: Improve quoting of role names, particularly in postgres.

### 0.15.11
- fix: Exclude extension-created objects from comparisons.
- fix: Quote audit column names.

### 0.15.10

- feat: Support alembic check.
- fix: Quote trigger name/tablenames.

### 0.15.9

- fix: Quote trigger name/tablenames.

### 0.15.8

- fix: Snowflake - Stop asserting views start with SELECT (CTEs).

### 0.15.7

- fix: Snowflake - Strip whitespace from SQL def before asserting starts with SELECT

### 0.15.6

- fix: Metadata naming_convention registration in combination with register_sqlalchemy_events.

### 0.15.5

- fix: Dont set `None` audit "context values".

### 0.15.4

- fix: Undo accidental inclusion of alembic as required dependencies.

### 0.15.3

- fix: Handle row/view metadata sequence.

### 0.15.2

- fix: Handle trigger metadata sequence.
- fix: Handle procedure metadata sequence.
- fix: Handle function metadata sequence.
- fix: Handle grant metadata sequence.
- fix: Handle role metadata sequence.
- fix: Handle schema metadata sequence.

### 0.15.1

- fix: Accept more generic sequence to roles.

### 0.15.0

- fix: Add role name coercion to postgres default grant `to` argument.
- feat: Add ability to supply environment deferred password value to postgres role.

## 0.14

### 0.14.0

- feat: Add basic support for triggers with arguments to Postgres.

## 0.13

### 0.13.0

- feat: Add support for MetaData.drop_all.
- feat: Add basic support for functions and procedures to MySQL.

## 0.12

### 0.12.0

- feat: Add basic support for triggers to MySQL.

## 0.11

### 0.11.4

- fix: Incorrect when condition paren stripping.

### 0.11.3

- fix: Use different mechanism to get WHEN clause in trigger definitions to avoid
  postgres internal error.

### 0.11.2

- fix: Add trailing semicolon to avoid syntax issue with snowflake schema ....create

### 0.11.1

- fix: Snowflake create schema emitting invalid syntax due to double string wrapping.

### 0.11.0

- feat: Add "use role" with schema.
- feat: Add snowflake-specific schema support.
- feat: Add support for declarative database.
- feat: Add support for snowflake roles.
- feat: Add support for snowflake views.
- fix: Snowflake schema name comparison casing.

## 0.10

### 0.10.0

- feat: Add separate Procedure object for postgres.

## 0.9

### 0.9.3

- feat: Allow glob matching view creation in sqlalchemy event hook.

### 0.9.2

- fix: Ignore snowflake schema casing.

### 0.9.1

- feat: Allow **view** to be a callable.
- feat: Add concept of "external" role that is ignored during comparisons.

### 0.9.0

- feat: Allow postgres specific materialized view options.
- fix: Deprecates `constraints` and `materialized` arguments
  during direct construction of generic `View` instances. Moved
  to dialect-specific variants.
- feat: add "security" option to postgres `Function`.
- feat: Add `external` option to `Role`, which can be used to reference
  non-managed roles.
- feat: Allow `Role` to be referenced by object rather than just name.
