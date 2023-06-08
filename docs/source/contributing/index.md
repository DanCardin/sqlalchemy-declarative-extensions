# Contributing

Contributions of any kind are very welcome!

See [Dialect Support](./dialect-support.md) or [Testing](./testing.md) for more specific details on how
the library is organized.

## Local Development

A prerequisite for executing the code is a python version of at least 3.7.

Additionally Docker must be installed and accessible locally in order for at
least the tests to execute.

## Makefile/CI
See the `Makefile` for the an idea of the commands we run (locally and in CI)
for linting/executing tests.

Note, you can freely avoid using the `Makefile`, and just run any commands directly,
but all contributions must first pass CI, and the `Makefile` commands for `lint`
and `test` are directly executed in CI. Thus those commands passing locally
is a good indicator of whether you'll encounter issues in CI itself.

```{toctree}
:hidden:

Dialect Support <dialect-support>
Testing <testing>
```
