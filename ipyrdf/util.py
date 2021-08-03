from typing import Dict


def set_variable(var_name: str, value, local_ns: Dict = None):
    """Handle logic of taking the variable name and setting the value.

    Resolve:
      - x.y
      - x["y"]

    TODO resolve nesting or more complex var_names

    :param var_name: string representing variable name
    :param value: value to set
    :param local_ns: local namespace, defaults to None
    """
    if "." and "[" in var_name:
        raise NotImplementedError(
            (
                "Complex variable name resolution. Contain either attribute "
                "or item lookup but not both"
            )
        )
    if "." in var_name:
        # attribute lookups
        names = var_name.split(".")
        var = local_ns[names[0]]
        for name in names[1:-1]:
            var = getattr(var, name)
        setattr(var, names[-1], value)
    elif "[" in var_name:
        # item lookups
        names = var_name.replace("[", " ").replace("]", "").split(" ").strip()
        var = local_ns[names[0]]
        for name in names[1:-1]:
            if name:
                var = var[name]
        var[names[-1]] = value
    else:
        # simple lookup
        local_ns[var_name] = value


def get_variable(var_name: str, local_ns: Dict = None):
    """Handle logic of taking the variable name and setting the value.

    Resolve:
      - x.y
      - x["y"]

    TODO resolve nesting or more complex var_names

    :param var_name: string representing variable name
    :param value: value to set
    :param local_ns: local namespace, defaults to None
    """
    if "." and "[" in var_name:
        raise NotImplementedError(
            (
                "Complex variable name resolution. Contain either attribute "
                "or item lookup but not both"
            )
        )
    if "." in var_name:
        # attribute lookups
        names = var_name.split(".")
        var = local_ns[names[0]]
        for name in names[1:]:
            var = getattr(var, name)
    elif "[" in var_name:
        # item lookups
        names = var_name.replace("[", " ").replace("]", "").split(" ").strip()
        var = local_ns[names[0]]
        for name in names[1:]:
            if name:
                var = var[name]
    else:
        # simple lookup
        var = local_ns[var_name]
    return var
