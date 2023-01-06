from typing import Dict, List, Optional, Set, Tuple

from ipyelk.diagram import layout_options as opt
from ipyelk.elements import (  # Compartment,; Compound,; Edge,; Mark,; Record,
    Label,
    Node,
    Port,
)

# from ipyelk.diagram.shape import shapes
from rdflib.plugins.sparql import parserutils
from rdflib.plugins.sparql.parserutils import CompValue, ParseResults
from rdflib.term import Literal, URIRef, Variable

from ..rdf_diagram.rdf_diagram import (
    RDFElement,
    RDFLiteralBinding,
    RDFPartition,
    RDFURIRef,
    rdf_label,
)

ExpressionOps = {
    # "RelationalExpression": "",
}

HEADING_OPTS = opt.OptionsWidget(
    options=[
        opt.NodeLabelPlacement(horizontal="center", vertical="top"),
    ]
).value


def get_expr_name(name):
    name = name.replace("Builtin_", "")
    return ExpressionOps.get(name, name)


def get_vars(expr):
    _vars = set()
    if "_vars" in expr:
        _vars |= expr._vars
    if "expr" in expr:
        if isinstance(expr.expr, Variable):
            _vars |= set([expr.expr])
    if isinstance(expr, dict):
        for k, v in expr.items():
            _vars |= get_vars(v)
    elif isinstance(expr, list):
        for v in expr:
            _vars |= get_vars(v)
    return _vars


def extract_prologue(parse_tree: ParseResults) -> Tuple[Optional[str], Dict]:
    base = None
    ns = {}
    for t in parse_tree[0]:
        if t.name == "Base":
            base = t.iri
        elif t.name == "PrefixDecl":
            ns[t.prefix] = t.iri
    return base, ns


class SparqlVariable(RDFElement):
    css_classes: Set[str] = {"rdf-variable"}


class SparqlNamespace(RDFElement):
    css_classes: Set[str] = {"rdf-namespace"}


class SparqlExpression(RDFElement):
    css_classes: Set[str] = {"rdf-expression"}


class SparqlPartition(RDFPartition):
    def add_expr(self, expr, parent: RDFElement = None) -> SparqlExpression:
        if parent is None:
            parent = self
        if isinstance(expr, list):
            return [self.add_expr(e, parent=parent) for e in expr]
        if "op" in expr:
            source = self._process_expr(expr.expr, parent=parent)
            target = self._process_expr(expr.other, parent=parent)
            edge = self[source : target : rdf_label(self.ns, expr.op)]
            edge.add_class("rdf-expression")
        elif expr.name == "OrderCondition":
            child = self._get_child(expr.expr, parent)
            if expr.order:
                title = child.labels[0].text
                child.labels[0].text = f"{expr.order}({title})"

    def _process_expr(self, side, parent: RDFElement):
        if not isinstance(side, parserutils.Expr):
            return self._get_child(side)
        source = self._process_expr(side.arg, parent=parent)
        target = parent.add_child(
            SparqlExpression(labels=[Label(text=get_expr_name(side.name))])
        )
        arg_port = target.add_port(
            port=Port().add_class("rdf-expression"), key=side.arg
        )
        edge = self[source:arg_port]
        edge.add_class("rdf-expression")
        return target

    def _get_child(self, term, key=None, parent=None):
        if parent is None:
            parent = self
        if key is None:
            key = term

        if key in parent._child_namespace:
            return parent._child_namespace[key]
        # test type of key: [uri, variable, literal]
        _cls = RDFElement
        text = rdf_label(self.ns, term)
        if isinstance(term, Variable):
            _cls = SparqlVariable
        elif isinstance(term, Literal):
            _cls = RDFLiteralBinding
        elif isinstance(term, URIRef):
            _cls = RDFURIRef

        node = _cls(labels=[Label(text=text)])
        return parent.add_child(node, key)


def loop(t, context: SparqlPartition, parent: RDFElement = None):
    # flexibility for assigning hierarchy
    if parent is None:
        parent = context
    if isinstance(t, CompValue):
        if t.name == "BGP":
            for s, p, o in t["triples"]:
                context.add_triple(s, p, o)

        elif t.name == "Graph":
            graph = SparqlPartition(
                labels=[Label(text=rdf_label(context.ns, t.term))], ns=context.ns
            ).add_class("rdf-graph")
            context.add_child(graph)
            loop(t.p, context=graph)

        elif t.name == "OrderBy":
            orderby = SparqlPartition(
                labels=[Label(text="OrderBy").add_class("rdf-keyword")], ns=context.ns
            ).add_class("rdf-expression")
            context.add_child(orderby)
            loop(t.p, context=context)
            orderby.add_expr(t.expr)

        elif t.name == "Union":
            union = SparqlPartition(
                labels=[Label(text="Union").add_class("rdf-keyword")], ns=context.ns
            ).add_class("rdf-expression")
            c1 = SparqlPartition(ns=context.ns)
            c2 = SparqlPartition(ns=context.ns)
            loop(t.p1, context=c1)
            loop(t.p2, context=c2)

            context.add_child(union)
            union.add_child(c1)
            union.add_child(c2)
            # out.append(union)

        elif t.name == "Filter":
            f = SparqlPartition(
                labels=[
                    Label(text="FILTER", layoutOptions=HEADING_OPTS).add_class(
                        "rdf-keyword"
                    )
                ]
            ).add_class("rdf-expression")
            context.add_child(f)
            loop(t.expr, context=f)
            connect_ports(context, f, get_vars(t.expr))
            loop(t.p, context=context)

        elif t.name == "LeftJoin":
            loop(t.p1, context=context)
            optional = SparqlPartition(
                labels=[Label(text="Optional").add_class("rdf-keyword")], ns=context.ns
            )
            context.add_child(optional)
            loop(t.p2, context=optional)

            # process shared variables... turn into ports on the optional block
            for shared in set(t.p1._vars) & set(t.p2._vars):
                source = context._get_child(shared)
                target = optional._get_child(shared)
                port = optional.add_port(
                    port=Port().add_class("rdf-optional"), key=shared
                )
                context[source:port]
                optional[port:target]
        elif "expr" in t.keys():
            if t.name == "ConditionalAndExpression":
                ConditionalAndExpression(t, context=context, parent=parent)
            else:
                context.add_expr(t, parent=parent)

        else:
            for k, v in t.items():
                loop(v, context=context, parent=parent)

    elif isinstance(t, dict):
        for k, v in t.items():
            loop(v, context=context, parent=parent)
    elif isinstance(t, list):
        for e in t:
            loop(e, context=context, parent=parent)
    return context


def remove_child(partition: Node, child: Node, key: str = ""):
    if child in partition.children:
        partition.children.remove(child)
    if key:
        partition._child_namespace.pop(key, None)
    return child


def ConditionalAndExpression(
    t, context: SparqlPartition, parent: RDFElement = None
) -> List[SparqlPartition]:
    if parent is None:
        parent = context
    # need some extra effort to promote the variables in the expression
    v1 = get_vars(t.expr)
    v2 = get_vars(t.other)

    c1 = SparqlPartition(ns=context.ns).add_class("rdf-expression")
    c2 = SparqlPartition(ns=context.ns).add_class("rdf-expression")
    loop(t.expr, context=c1)
    loop(t.other, context=c2)
    parent.add_child(c1)
    parent.add_child(c2)

    connect_ports(context, c1, v1)
    connect_ports(context, c2, v2)

    return [c1, c2]


def connect_ports(c1, c2, terms):
    for v in terms:
        source = c1._get_child(v)
        target = c2._get_child(v)
        port = c2.add_port(Port().add_class("rdf-expression"), key=v)
        c1[source:port]
        c2[port:target]
