from typing import Type, Union

from ipyelk import exceptions
from ipyelk.contrib.molds import connectors
from ipyelk.elements import (  # Compartment,; Mark,; Record,; layout_options as opt,
    Edge,
    EdgeProperties,
    ElementMetadata,
    Label,
    Node,
    NodeProperties,
    Partition,
    SymbolSpec,
    merge_excluded,
)
from pydantic import Field

# from ipyelk.elements.shape import Shape, shapes, Symbol
from rdflib.term import BNode, Literal, URIRef, Variable

from ..namespace_wrapper import NSWrapper

RDF_DIAGRAM_STYLE = {
    " .rdf-uriref > .elknode": {
        "stroke": "var(--jp-mirror-editor-variable-2-color)",
        "rx": "10px",
        "ry": "10px",
    },
    " .active-set > .elknode": {
        "fill": "var(--jp-border-color3)",
    },
    " .rdf-literal  > .elknode": {
        "stroke": "var(--jp-mirror-editor-string-color)",
    },
    " .rdf-namespace  > .elknode": {
        "stroke": "var(--jp-mirror-editor-atom-color)",
    },
    " .rdf-predicate > .elknode": {
        "stroke": "var(--jp-mirror-editor-atom-color)",
    },
    " .rdf-expression  > .elknode": {
        "stroke": "var(--jp-mirror-editor-builtin-color)",
        "rx": "10px",
        "ry": "10px",
    },
    " .rdf-expression  > .elkport": {
        "stroke": "var(--jp-mirror-editor-builtin-color)",
    },
}

arrow_head = connectors.StraightArrow("arrow", r=4)

RDF_DIAGRAM_SYMBOLS: SymbolSpec = SymbolSpec().add(arrow_head)


class RDFMetadata(ElementMetadata):
    uri: Union[BNode, URIRef] = None


class SimplePredicate(Edge):
    properties: EdgeProperties = EdgeProperties(shape={"end": arrow_head.identifier})


class RDFElement(Node):
    metadata: RDFMetadata = Field(default_factory=RDFMetadata)


class RDFURIRef(RDFElement):
    properties: NodeProperties = Field(
        default_factory=lambda *_: NodeProperties(cssClasses="rdf-uriref")
    )


class RDFLiteralBinding(RDFElement):
    properties: NodeProperties = Field(
        default_factory=lambda *_: NodeProperties(cssClasses="rdf-literal")
    )


class RDFPredicate(RDFElement):
    properties: NodeProperties = Field(
        default_factory=lambda *_: NodeProperties(cssClasses="rdf-predicate")
    )


class RDFPartition(Partition):
    ns: NSWrapper = Field(default_factory=NSWrapper)
    default_edge: Type[Edge] = Field(default=SimplePredicate)

    class Config:
        copy_on_model_validation = False
        excluded = merge_excluded(Partition, "ns", "default_edge")

        # class Config:
        arbitrary_types_allowed = True

    def add_triple(self, s, p, o):
        # check predicate mode ["edges", "nested", "namespaced", "nodes"]

        source = self._get_child(s)
        target = self._get_child(o)

        edge = self[source : target : rdf_label(self.ns, p)]
        edge.add_class("rdf-predicate")
        edge.metadata = RDFMetadata(uri=p)

    def _get_child(self, term, key=None, parent=None):
        if parent is None:
            parent = self
        if key is None:
            key = term

        try:
            return parent.get_child(key)
        except exceptions.NotFoundError:
            pass
        if key in parent.children:
            return parent.children[key]
        # test type of key: [uri, variable, literal]
        _cls = RDFElement
        text = rdf_label(self.ns, term)
        if isinstance(term, Literal):
            _cls = RDFLiteralBinding
        if isinstance(term, URIRef):
            _cls = RDFURIRef

        node = _cls(labels=[*Label(text=text).wrap()], metadata=RDFMetadata(uri=key))
        return parent.add_child(node, key)

    def clear(self):
        # self._child_namespace = dict()
        # self.children = []
        # self.ports = {}
        self.edges = list()


def rdf_label(ns: NSWrapper, term) -> str:
    if isinstance(term, URIRef):
        text = ns[term]  # get the qname from the namespace manager
    elif isinstance(term, Variable):
        text = "?" + str(term)
    elif isinstance(term, Literal):
        text = term.n3(ns._graph.namespace_manager)
    else:
        text = str(term)
    return text
