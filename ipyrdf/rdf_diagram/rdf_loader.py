from typing import List, Optional, Set, Tuple

import traitlets as T
from ipyelk import Diagram, ElementLoader, MarkElementWidget
from ipyelk.elements import layout_options as opt
from ipyrdf import NSWrapper
from rdflib import Graph

from ..queries.summary import get_distinct_ends
from .rdf_diagram import RDF_DIAGRAM_STYLE, RDF_DIAGRAM_SYMBOLS, RDFPartition


class RDFLoader(ElementLoader):
    partition: RDFPartition = T.Instance(RDFPartition, kw={})

    @T.default("default_label_opts")
    def _default_node_opts(self):
        return opt.OptionsWidget(
            options=[
                opt.NodeLabelPlacement(horizontal="center", vertical="center"),
            ]
        ).value

    @T.default("default_root_opts")
    def _default_root_opts(self):
        return {
            opt.HierarchyHandling.identifier: opt.HierarchyHandling().value,
            opt.Direction.identifier: opt.Direction(value="DOWN").value,
        }

    def load(self, new_graph: Graph, old_graph: Graph = None) -> MarkElementWidget:
        partition = self.partition
        partition.ns = NSWrapper(graph=new_graph)
        partition.clear()
        exiting_uri, exiting_triples, entering_triples = graph_lifecycle(
            old_graph, new_graph
        )
        for uri in exiting_uri:
            partition.remove_child(partition._get_child(uri))

        # TODO handle the exiting and entering triples
        for s, p, o in new_graph:
            partition.add_triple(s, p, o)

        return super().load(root=self.partition)


def graph_lifecycle(old: Graph, new: Graph):
    if not isinstance(old, Graph):
        old = Graph()
    if not isinstance(new, Graph):
        new = Graph()
    old_uri = set(get_distinct_ends(old))
    new_uri = set(get_distinct_ends(new))
    exiting_uri = old_uri.difference(new_uri)

    exiting_triples, entering_triples = lifecycle(
        old=set(t for t in old),
        new=set(t for t in new),
    )

    return exiting_uri, exiting_triples, entering_triples


def lifecycle(old: Set, new: Set) -> Tuple[Set, Set]:
    exiting = old.difference(new)
    entering = new.difference(old)
    return exiting, entering


def from_rdf(graph: Graph = None, uris: Optional[List[str]] = None, **kwargs):
    from .describe_tool import DescribeTool

    if graph is None:
        graph = Graph()

    return Diagram(style=RDF_DIAGRAM_STYLE, symbols=RDF_DIAGRAM_SYMBOLS,).register_tool(
        DescribeTool(
            graph=graph,
            uris=uris,
        )
    )
