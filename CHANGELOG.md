# Changelog

## 0.11

### 0.11.0

- feat: Add support for declarative database.
- feat: Add support for snowflake roles.

## 0.10

### 0.10.0

- feat: Add separate Procedure object for postgres.

## 0.9

### 0.9.3

- feat: Allow glob matching view creation in sqlalchemy event hook.

### 0.9.2

- fix: Ignore snowflake schema casing.

### 0.9.1

- feat: Allow __view__ to be a callable.
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
