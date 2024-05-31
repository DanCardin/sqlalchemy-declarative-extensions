# Changelog

## 0.9

### 0.9.0

- feat: Allow postgres specific materialized view options.
- fix: Deprecates `constraints` and `materialized` arguments
  during direct construction of generic `View` instances. Moved
  to dialect-specific variants.
- feat: add "security" option to postgres `Function`.
- feat: Add `external` option to `Role`, which can be used to reference
  non-managed roles.
- feat: Allow `Role` to be referenced by object rather than just name.
