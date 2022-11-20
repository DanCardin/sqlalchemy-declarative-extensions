# Rows

Use of this feature ensures the existence of rows matching the defined values.
All columns included in the primary key (as defined by the `MetaData`) are
required to be included on a given `Row`.

Using uniqueness given by the primary key commands will be emitted to bring
the state of the world to match the defined values. This includes:

- Inserting rows if none exist
- (Optionally) Deleting them if they're not defined but exist in the database
- Updating them if the state of the database does not match the defined values.

  Note with updates, only the set of included fields will be updated. A given
  `Row` that excludes (non-nullable, say) columns will not be considered
  when performing the comparison against existing data.

```python
from sqlalchemy_declarative_extensions import Row, Rows

# Assumes some model/table defined for `foo`.
rows = Rows().are(
    Row("foo", id=2, name="asdf"),
    Row("foo", id=3, name="qwer", active=False),
)
```

Note one cannot usually use the models themselves to define row data, because
usually models are defined **off** the declarative base class. This would cause
issues of circular reliance on the definition of the declarative base being complete.

If defined using alternative SQLAlchemy APIs for model definition, one can
technically get around the circularity issues; so it's likely that a future
release will add support for subbing in models themselves in place of a `Row`.

```{eval-rst}
.. autoapimodule:: sqlalchemy_declarative_extensions.row.base
   :members:
```
