def qualify_name(schema: str, name: str):
    if not schema or schema == "public":
        return name
    return f"{schema}.{name}"
