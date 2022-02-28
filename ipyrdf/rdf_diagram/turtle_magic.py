import argparse

from IPython.core.magic import needs_local_scope, register_cell_magic
from rdflib import Graph


from ..util import get_variable, set_variable
from .describe_tool import DescribeTool
from .rdf_loader import from_rdf

parser = argparse.ArgumentParser(description="Turtle Magic.")
parser.add_argument(
    "varname", type=str, help="path to the variable from the local namespace"
)
parser.add_argument(
    "--id", 
    type=str, 
    help="identifier for the graph", 
    default=None,
)
parser.add_argument(
    "--append",
    help="append parsed graph to existing value",
    action="store_true",
)
parser.add_argument(
    "--base",
    help="append parsed graph to base graph",
    type=str,
)
parser.add_argument(
    "--store", 
    help="specify store for the graph",
    type=str,
    default=None,
)

parser.add_argument(
    "--uris",
    nargs="*",
    help="initially focused uris",
    type=str,
    default=None,
)


def get_prefix_string(graph: Graph):
    prefixes = []
    for name, uri in graph.namespaces():
        prefixes.append(f"@prefix {name}: <{uri}> .")
    return prefixes


@register_cell_magic
@needs_local_scope
def turtle(parameters: str, cell: str, local_ns: dict = None):
    """Parse turtle into an rdfgraph.
    If provided a variable name in the magic parameters, the graph will be saved
    to the local namespace along that given variable name.

    Otherwise the graph will be returned in an RDFGraphWidget.

    :param parameters: parameter string. Currently only supports variable name
    as a single parameter
    :param cell: cell body to parse
    :param local_ns: calling scopes local namespace, defaults to None
    """
    args = parser.parse_args(parameters.strip().split(" "))
    varname = args.varname
    store = get_variable(args.store, local_ns) if args.store else None
    graph = Graph(store=store, identifier=args.id)

    if args.append and "@prefix" not in cell:
        var = get_variable(varname, local_ns)
        if isinstance(var, DescribeTool):
            graph = var.graph
        elif isinstance(var, Graph):
            graph = var
        cell = "\n".join(get_prefix_string(graph)) + cell

    value = graph.parse(data=cell, format="turtle")
        
    if args.base:
        base = get_variable(args.base, local_ns)
        value = value + base

    if args.append:
        assert varname, "Varname must exist"
        base = get_variable(varname, local_ns)
        if isinstance(base, DescribeTool):
            base = base.graph
        value = value + base

    set_uri = False
    if isinstance(args.uris, list):
        set_uri = True
        uris = [get_variable(uri, local_ns) for uri in args.uris]
        if len(uris) == 0:
            uris = None  # would display all
    else:
        uris = None

    if varname:
        # update existing diagram
        var: DescribeTool = get_variable(varname, local_ns)
        if isinstance(var, DescribeTool):
            if set_uri:
                var.uris = uris
            var.graph = value
        else:
            set_variable(varname, value, local_ns)
    else:
        # make new diagram
        return from_rdf(
            graph=graph,
            uris=uris,
        )
