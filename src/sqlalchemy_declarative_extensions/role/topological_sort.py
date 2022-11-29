from typing import Dict, Iterable, Set

from sqlalchemy_declarative_extensions.role.generic import Role


def topological_sort(roles: Iterable[Role]):
    """Sort roles in an order that guarantees success based on role dependence.

    Uses Kahn's algorithm.
    """
    role_name_map = generate_role_map(roles)
    role_dep_map = generate_role_dependency_map(role_name_map)

    fullfilled_role_names = deduplicate_roles(
        role_dep_map.items(), exclude_no_deps=True
    )

    for role in fullfilled_role_names:
        role_dep_map.pop(role)

    result = []
    while fullfilled_role_names:
        fullfilled_role_name = fullfilled_role_names.pop(0)
        result.append(role_name_map[fullfilled_role_name])

        # Remove fullfilled role from deps of all other roles which might depend on it.
        for deps in role_dep_map.values():
            if fullfilled_role_name in deps:
                deps.remove(fullfilled_role_name)

        newly_fullfilled_roles = deduplicate_roles(
            role_dep_map.items(), exclude_no_deps=True
        )

        fullfilled_role_names = deduplicate_roles(
            fullfilled_role_names + newly_fullfilled_roles
        )
        for role in newly_fullfilled_roles:
            role_dep_map.pop(role)

    if any(role_dep_map):
        cyclical_roles = ", ".join(sorted(role_dep_map.keys()))
        raise ValueError(
            f"The following roles have cyclical dependencies: {cyclical_roles}"
        )

    return result


def deduplicate_roles(deps, exclude_no_deps=False):
    if exclude_no_deps:
        deps = (role for role, deps in deps if not deps)

    return list(dict.fromkeys(deps))


def generate_role_map(roles: Iterable[Role]) -> Dict[str, Role]:
    result: Dict[str, Role] = {}
    for role in roles:
        if role.name in result:
            raise ValueError(f"Duplicate role specified: {role}")
        result[role.name] = role
    return result


def generate_role_dependency_map(role_name_map: Dict[str, Role]) -> Dict[str, Set[str]]:
    result: Dict[str, Set[str]] = {}
    valid_role_names = set(role_name_map)
    for name, role in role_name_map.items():
        in_roles = set(role.in_roles or [])

        if not in_roles.issubset(valid_role_names):
            missing_roles = ", ".join(sorted(in_roles - valid_role_names))
            raise ValueError(
                "The following roles are specified as dependencies of other "
                "top-level roles, but are missing in the list of top-level "
                f"roles: {missing_roles}."
            )
        result[name] = in_roles
    return result
