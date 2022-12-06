def register_alembic_events(
    schemas: bool = True,
    views: bool = True,
    roles: bool = True,
    grants: bool = True,
    rows: bool = True,
):
    """Register handlers into alembic's event system for the supported object types.

    By default all object types are enabled, but each can be individually disabled.

    Note this is the opposite of the defaults when registering against SQLAlchemy's
    event system.
    """
    if schemas:
        import sqlalchemy_declarative_extensions.alembic.schema

    if views:
        import sqlalchemy_declarative_extensions.alembic.view

    if roles:
        import sqlalchemy_declarative_extensions.alembic.role

    if grants:
        import sqlalchemy_declarative_extensions.alembic.grant

    if rows:
        import sqlalchemy_declarative_extensions.alembic.row  # noqa


def ignore_view_tables(object, *_):
    """A function capable of being used as alembic's `include_object` argument of configure.

    >>> def run_online():
    ...     ...
    ...     context.configure(..., include_object=ignore_view_tables)

    Note that if you are already using your own `include_object`, you can either manually
    compose a call to this function from inside it, or use :func:`compose_include_object_callbacks`
    to compose the two calls.
    """
    return not object.info.get("is_view")


def compose_include_object_callbacks(*callbacks):
    """Composes one or more `include_object` calls in sequence, producing a new function.

    This is meant to make it easier to compose a self-defined `include_object` function
    with one provided by this library, such as `ignore_view_tables`.

    >>> def my_include_object(object, *_):
    ...     return True
    >>> include_object = compose_include_object_callbacks(my_include_object, ignore_view_tables)

    Note that the callbacks are called in the order given, and only terminate
    when a function returns `False` for a particular object. Whereas `True` values
    are passed through to the rest of the callbacks.
    """

    def callback(*args, **kwargs):
        for callback in callbacks:
            result = callback(*args, **kwargs)
            if result is False:
                return False

        return True

    return callback
