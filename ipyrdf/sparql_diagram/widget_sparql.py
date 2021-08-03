import traitlets as T
from ipyelk import Elk, nx
from ipyelk.diagram import elk_model
from ipyelk.diagram import layout_options as opt
from ipyelk.elements import Compartment, Mark, MarkFactory
from ipyelk.tools import tools
from ipyrdf import NSWrapper
from pyparsing import ParseResults
from rdflib.plugins.sparql import algebra
from rdflib.plugins.sparql.parserutils import prettify_parsetree

from .sparql_diagram import SparqlPartition, extract_prologue, loop


class ToggleRecordBtn(tools.ToggleCollapsedBtn):
    def get_related(self, node):
        tree = self.app.transformer.source[1]
        if isinstance(node, Mark) and isinstance(node.node, Compartment):
            parent = list(tree.predecessors(node))[0]
            return [child for i, child in enumerate(tree.neighbors(parent)) if i > 0]
        return super().get_related(node)


class SparqlWidget(Elk):
    parse_tree = T.Instance(ParseResults)
    query = T.Instance(algebra.Query)
    ns = T.Instance(NSWrapper, kw={})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._make_toolbar()

    @T.default("style")
    def _default_style(self):
        return {
            " .rdf-keyword.elklabel": {"fill": "var(--jp-mirror-editor-keyword-color)"},
            " .rdf-variable > .elknode": {
                "stroke": "var(--jp-mirror-editor-variable-2-color)",
                "rx": "10px",
                "ry": "10px",
            },
            " .rdf-uriref > .elknode": {
                "stroke": "var(--jp-mirror-editor-atom-color)",
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
                # "rx": "10px",
                # "ry": "10px",
            },
            #      " .rdf-predicate.elkedge": {
            #         "stroke": "var(--jp-mirror-editor-atom-color)",
            #     },
            #      " .rdf-predicate.elkedge text": {
            #         "fill": "var(--jp-mirror-editor-atom-color)",
            #     },
        }

    @T.default("transformer")
    def _default_transformer(self):
        diagram_opts = opt.OptionsWidget(
            options=[opt.Direction(value="RIGHT"), opt.HierarchyHandling()]
        ).value

        return nx.XELK(
            layouts={
                elk_model.ElkRoot: {
                    "parents": diagram_opts,
                }
            }
        )

    @T.default("layout")
    def _default_layout(self):
        return {"height": "100%"}

    def _make_toolbar(self):
        toggle = ToggleRecordBtn(app=self)
        fit = tools.FitBtn(app=self)
        self.toolbar.commands = [fit, toggle]

    @T.observe("parse_tree")
    def _handle_parse_tree(self, change=None):
        base, initNs = extract_prologue(self.parse_tree)
        for key, value in initNs.items():
            setattr(self.ns, key, value)
        if base:
            setattr(self.ns, "", base)
        self.query = algebra.translateQuery(self.parse_tree, base, initNs)

    @T.observe("query")
    def _handle_query(self, change):
        ans = loop(self.query.algebra, context=SparqlPartition(ns=self.ns))
        cp = MarkFactory()
        self.transformer.source = cp(ans)

    def pretty(self):
        print(prettify_parsetree(self.query.algebra))
