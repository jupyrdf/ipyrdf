import traitlets as T
from ipyelk import Diagram, MarkElementWidget, tools
from rdflib import BNode, Graph, URIRef, term

from ..queries import describe
from .rdf_diagram import RDFElement
from .rdf_loader import RDFLoader


class DescribeTool(tools.SetTool):
    diagram = T.Instance(Diagram, allow_none=True)
    graph = T.Instance(Graph)
    uris = T.List(T.Instance(term.Identifier), allow_none=True)
    subgraph = T.Instance(Graph, kw={})
    loader = T.Instance(RDFLoader, kw={})
    source = T.Instance(MarkElementWidget, kw={})

    @T.observe("active")
    def handler(self, change):
        super().handler(change)
        uris = []
        for el in change.new:
            if isinstance(el, RDFElement):
                uri = el.metadata.uri
                if isinstance(uri, (URIRef, BNode)):
                    uris.append(uri)
        if len(uris) == 0:
            self.uris = None
        else:
            self.uris = uris

    @T.observe("uris", "graph")
    def _update_uris(self, change):
        if self.uris is None:
            self.subgraph = self.graph
        else:
            self.subgraph = describe(self.graph, self.uris)

    @T.observe("subgraph")
    def _update_source(self, change):
        self.source = self.loader.load(change.new, change.old)

    @T.observe("source", "diagram")
    def _update_output(self, change):
        if self.diagram:
            self.diagram.source = self.source
