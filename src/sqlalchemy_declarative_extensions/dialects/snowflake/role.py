from __future__ import annotations

import enum
from dataclasses import dataclass, field, fields

from sqlalchemy_declarative_extensions.role import generic


@enum.unique
class SecondaryRoles(enum.Enum):
    all = "ALL"


@dataclass
class Role(generic.Role):
    """Define a role object.

    role: https://docs.snowflake.com/en/sql-reference/sql/create-role
    user: https://docs.snowflake.com/en/sql-reference/sql/create-user

    Note, `is_user` defaults to `None`, which causes `CREATE ROLE` or `CREATE USER`
    to be automatically chosen based on the usage of user-specific options. If
    the mode is incorrectly determined, you can supply `is_user=True` to force
    creation of a user.

    Note, the password field can be supplied, but it will be ignored when
    performing comparisons against existing roles. That is, changing the
    password field will not produce any (alembic) changes!
    """

    is_user: bool | None = None

    # common role/user options
    comment: str | None = None

    # user-only options
    login_name: str | None = None
    display_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    must_change_password: bool | None = None
    disabled: bool | None = None
    days_to_expiry: int | None = None
    mins_to_unlock: int | None = None
    default_warehouse: str | None = None
    default_namespace: str | None = None
    default_role: str | None = None
    default_secondary_roles: list[SecondaryRoles] | None = None
    mins_to_bypass_mfa: int | None = None

    password: str | None = field(default=None, compare=False)
    rsa_public_key: str | None = field(default=None, compare=False)
    rsa_public_key_fp: str | None = field(default=None, compare=False)
    rsa_public_key_2: str | None = field(default=None, compare=False)
    rsa_public_key_2_fp: str | None = field(default=None, compare=False)

    @classmethod
    def from_snowflake_user(cls, r, in_roles: list[str] | None = None) -> Role:
        return cls(
            r.name,
            comment=r.comment,
            login_name=r.login_name,
            display_name=r.display_name,
            first_name=r.first_name,
            last_name=r.last_name,
            email=r.email,
            must_change_password=r.must_change_password,
            disabled=r.disabled,
            days_to_expiry=r.days_to_expiry,
            mins_to_unlock=r.mins_to_unlock,
            default_warehouse=r.default_warehouse,
            default_namespace=r.default_namespace,
            default_role=r.default_role,
            default_secondary_roles=r.default_secondary_roles,
            mins_to_bypass_mfa=r.mins_to_bypass_mfa,
            in_roles=sorted(in_roles) if in_roles else None,
        )

    @classmethod
    def from_snowflake_role(cls, r, in_roles: list[str] | None = None) -> Role:
        return cls(
            r.name,
            comment=r.comment,
            in_roles=sorted(in_roles) if in_roles else None,
        )

    @classmethod
    def from_unknown_role(cls, r: generic.Role | Role) -> Role:
        if not isinstance(r, Role):
            return Role(
                r.name,
                in_roles=sorted(r.in_roles, key=generic.by_name)
                if r.in_roles
                else None,
            )

        return r

    @property
    def options(self):
        for f in fields(self):
            if f.name == "name":
                continue

            value = getattr(self, f.name)
            if value is None:
                continue

            yield f.name, value

    def __repr__(self):
        cls_name = self.__class__.__name__
        options = ", ".join([f"{key}={value!r}" for key, value in self.options])
        return f'{cls_name}("{self.name}", {options})'

    @property
    def kind(self) -> str:
        is_user = self.is_user
        if self.is_user is None:
            is_user = any(
                opt
                for opt, val in self.options
                if val and opt not in {"name", "in_roles", "comment"}
            )
        return "USER" if is_user else "ROLE"

    def to_sql_create(self, raw: bool = True) -> list[str]:
        segments = [f"CREATE {self.kind}", self.name]

        options = render_role_options(self)
        if options:
            segments.append("WITH")
        segments.extend(options)

        command = " ".join(segments) + ";"

        result = [command]

        if self.in_roles:
            for role in generic.role_names(self.in_roles):
                result.append(f"GRANT ROLE {role} TO {self.kind} {self.name};")

        return result

    def to_sql_update(self, to_role: Role, raw: bool = True) -> list[str]:
        role_name = to_role.name
        diff = RoleDiff.diff(self, to_role)

        result = []

        diff_options = render_role_options(diff)
        if diff_options:
            segments = [f"ALTER {self.kind}", role_name, "WITH", *diff_options]
            alter_role = " ".join(segments) + ";"
            result.append(alter_role)

        for add_name in diff.add_roles:
            result.append(f"GRANT ROLE {add_name} TO {self.kind} {role_name};")

        for remove_name in diff.remove_roles:
            result.append(f"REVOKE {remove_name} FROM {self.kind} {role_name};")

        return result

    def to_sql_use(self, undo: bool) -> list[str]:
        result = []
        if undo:
            result.append("USE ROLE IDENTIFIER($ROLE);")
            result.append("UNSET ROLE;")
        else:
            result.append("SET ROLE=current_role();")
            result.append(f"USE ROLE {self.name}")

        return result


@dataclass
class RoleDiff:
    name: str

    comment: str | None = None
    login_name: str | None = None
    display_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    must_change_password: bool | None = None
    disabled: bool | None = None
    days_to_expiry: int | None = None
    mins_to_unlock: int | None = None
    default_warehouse: str | None = None
    default_namespace: str | None = None
    default_role: str | None = None
    default_secondary_roles: list[SecondaryRoles] | None = None
    mins_to_bypass_mfa: int | None = None

    add_roles: list[str] = field(default_factory=list)
    remove_roles: list[str] = field(default_factory=list)

    @classmethod
    def diff(cls, from_role: Role, to_role: Role) -> RoleDiff:
        add_roles = []
        remove_roles = []
        if to_role.in_roles != from_role.in_roles:
            from_in_roles = from_role.in_roles or []
            to_in_roles = to_role.in_roles or []

            add_roles = [r for r in to_in_roles if r not in from_in_roles]
            remove_roles = [r for r in from_in_roles if r not in to_in_roles]

        return cls(
            name=to_role.name,
            comment=None if from_role.comment == to_role.comment else to_role.comment,
            login_name=(
                None
                if from_role.login_name == to_role.login_name
                else to_role.login_name
            ),
            display_name=(
                None
                if from_role.display_name == to_role.display_name
                else to_role.display_name
            ),
            first_name=(
                None
                if from_role.first_name == to_role.first_name
                else to_role.first_name
            ),
            last_name=(
                None if from_role.last_name == to_role.last_name else to_role.last_name
            ),
            email=None if from_role.email == to_role.email else to_role.email,
            must_change_password=(
                None
                if from_role.must_change_password == to_role.must_change_password
                else to_role.must_change_password
            ),
            disabled=(
                None if from_role.disabled == to_role.disabled else to_role.disabled
            ),
            days_to_expiry=(
                None
                if from_role.days_to_expiry == to_role.days_to_expiry
                else to_role.days_to_expiry
            ),
            mins_to_unlock=(
                None
                if from_role.mins_to_unlock == to_role.mins_to_unlock
                else to_role.mins_to_unlock
            ),
            default_warehouse=(
                None
                if from_role.default_warehouse == to_role.default_warehouse
                else to_role.default_warehouse
            ),
            default_namespace=(
                None
                if from_role.default_namespace == to_role.default_namespace
                else to_role.default_namespace
            ),
            default_role=(
                None
                if from_role.default_role == to_role.default_role
                else to_role.default_role
            ),
            default_secondary_roles=(
                None
                if from_role.default_secondary_roles == to_role.default_secondary_roles
                else to_role.default_secondary_roles
            ),
            mins_to_bypass_mfa=(
                None
                if from_role.mins_to_bypass_mfa == to_role.mins_to_bypass_mfa
                else to_role.mins_to_bypass_mfa
            ),
            add_roles=generic.role_names(add_roles),
            remove_roles=generic.role_names(remove_roles),
        )


def render_role_options(role: Role | RoleDiff) -> list[str]:
    segments = []

    if role.comment is not None:
        segments.append(f"COMMENT = '{role.comment}'")

    if role.login_name is not None:
        segments.append(f"LOGIN_NAME = '{role.login_name}'")

    if role.display_name is not None:
        segments.append(f"DISPLAY_NAME = '{role.display_name}'")

    if role.first_name is not None:
        segments.append(f"FIRST_NAME = '{role.first_name}'")

    if role.last_name is not None:
        segments.append(f"LAST_NAME = '{role.last_name}'")

    if role.email is not None:
        segments.append(f"EMAIL = '{role.email}'")

    if role.must_change_password is not None:
        must_change_password = "TRUE" if role.must_change_password else "FALSE"
        segments.append(f"MUST_CHANGE_PASSWORD = {must_change_password}")

    if role.disabled is not None:
        disabled = "TRUE" if role.disabled else "FALSE"
        segments.append(f'DISABLED = "{disabled}"')

    if role.days_to_expiry is not None:
        segments.append(f"DAYS_TO_EXPIRY = {role.days_to_expiry}")

    if role.mins_to_unlock is not None:
        segments.append(f"MINS_TO_UNLOCK = {role.mins_to_unlock}")

    if role.default_warehouse is not None:
        segments.append(f"DEFAULT_WAREHOUSE = '{role.default_warehouse}'")

    if role.default_namespace is not None:
        segments.append(f"DEFAULT_NAMESPACE = '{role.default_namespace}'")

    if role.default_role is not None:
        segments.append(f"DEFAULT_ROLE = '{role.default_role}'")

    if role.default_secondary_roles is not None:
        secondary_roles = ", ".join(f"'{r}'" for r in role.default_secondary_roles)
        segments.append(f"default_secondary_roles = ({secondary_roles})")

    if role.mins_to_bypass_mfa is not None:
        segments.append(f"MINS_TO_BYPASS_MFA = {role.mins_to_bypass_mfa}")

    if isinstance(role, Role):
        if role.password is not None:
            segments.append(f"PASSWORD {role.password}")

        if role.rsa_public_key is not None:
            segments.append(f"RSA_PUBLIC_KEY {role.rsa_public_key}")

        if role.rsa_public_key_fp is not None:
            segments.append(f"RSA_PUBLIC_KEY_FP {role.rsa_public_key_fp}")

        if role.rsa_public_key_2 is not None:
            segments.append(f"RSA_PUBLIC_KEY_2 {role.rsa_public_key_2}")

        if role.rsa_public_key_2_fp is not None:
            segments.append(f"RSA_PUBLIC_KEY_2_FP {role.rsa_public_key_2_fp}")

    return segments
