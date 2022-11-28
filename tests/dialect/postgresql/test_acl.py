import pytest

from sqlalchemy_declarative_extensions.dialects.postgresql.acl import (
    parse_acl,
    parse_default_acl,
)
from sqlalchemy_declarative_extensions.dialects.postgresql.grant_type import (
    DefaultGrantTypes,
    GrantTypes,
    TableGrants,
)


@pytest.mark.parametrize("acl", ("=/", "user=/", '"user"=/', '"us""er"=/'))
def test_empty(acl):
    result = parse_default_acl(acl, "r", "public")
    assert result == []


@pytest.mark.parametrize("acl", ('"=/', '"user=/', '"user"'))
def test_invalid(acl):
    with pytest.raises(ValueError):
        parse_default_acl(acl, "r", "public")


@pytest.mark.parametrize(
    "acl, grant_option", (("user=r/user", False), ("user=r*/user", True))
)
def test_default_grant_table(acl, grant_option):
    result = parse_default_acl(acl, "r", "public")
    assert len(result) == 1
    assert result[0].grant.target_role == "user"
    assert result[0].grant.grants == (TableGrants.select,)
    assert result[0].grant.grant_option == grant_option
    assert result[0].grant.revoke_ is False

    assert result[0].default_grant.grant_type == DefaultGrantTypes.table
    assert result[0].default_grant.in_schemas == ("public",)
    assert result[0].default_grant.target_role == "user"


def test_with_and_without_grant():
    result = parse_default_acl("user=rw*/", "r", "public")
    assert len(result) == 2
    assert result[0].grant.grant_option is False
    assert result[1].grant.grant_option is True


@pytest.mark.parametrize(
    "acl, grant_option", (("user=r/user", False), ("user=r*/user", True))
)
def test_grant_table(acl, grant_option):
    result = parse_acl(acl, "r", "foo")
    assert len(result) == 1
    assert result[0].grant.target_role == "user"
    assert result[0].grant.grants == (TableGrants.select,)
    assert result[0].grant.grant_option == grant_option
    assert result[0].grant.revoke_ is False

    assert result[0].grant_type == GrantTypes.table
    assert result[0].targets == ("foo",)
