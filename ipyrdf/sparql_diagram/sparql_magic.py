from IPython.core.magic import needs_local_scope, register_cell_magic
from rdflib.plugins.sparql import parser

from ..widgets.widget_sparql import SparqlWidget
from .util import set_variable


@register_cell_magic
@needs_local_scope
def sparql(parameters: str, cell: str, local_ns: dict = None):
    """Parse turtle into an rdfgraph saved to the local namespace using the
    given variable name.

    :param parameters: parameter string. Currently only supports variable name
    as a single parameter
    :param cell: cell body to parse
    :param local_ns: calling scopes local namespace, defaults to None
    """
    params = parameters.strip().split(" ")
    var_name = None
    if len(params) == 1 and len(params[0]) >= 1:
        var_name = params[0]

    value = parser.parseQuery(cell)
    if var_name is not None:
        set_variable(var_name, value, local_ns)
    else:
        return SparqlWidget(parse_tree=value)
