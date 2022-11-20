import pytest

from sqlalchemy_declarative_extensions.grant.postgresql.grant_type import (
    DefaultGrantTypes,
    TableGrants,
)
from sqlalchemy_declarative_extensions.grant.postgresql.parse import parse_acl


@pytest.mark.parametrize("acl", ("=/", "user=/", '"user"=/', '"us""er"=/'))
def test_empty(acl):
    result = parse_acl(acl, "r", "public")
    assert result == []


@pytest.mark.parametrize("acl", ('"=/', '"user=/', '"user"'))
def test_invalid(acl):
    with pytest.raises(ValueError):
        parse_acl(acl, "r", "public")


@pytest.mark.parametrize(
    "acl, grant_option", (("user=r/user", False), ("user=r*/user", True))
)
def test_table(acl, grant_option):
    result = parse_acl(acl, "r", "public")
    assert len(result) == 1
    assert result[0].privileges.target_role == "user"
    assert result[0].privileges.grants == (TableGrants.select,)
    assert result[0].privileges.grant_option == grant_option
    assert result[0].privileges.revoke_ is False

    assert result[0].grant_type == DefaultGrantTypes.table
    assert result[0].in_schemas == ("public",)
    assert result[0].for_role == "user"


def test_with_and_without_grant():
    result = parse_acl("user=rw*/", "r", "public")
    assert len(result) == 2
    assert result[0].privileges.grant_option is False
    assert result[1].privileges.grant_option is True
