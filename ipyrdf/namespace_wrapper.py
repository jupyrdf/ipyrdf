from typing import Dict

from rdflib import Graph, Namespace

ipython_checks = [
    "_ipython_canary_method_should_not_exist_",
    "_ipython_display",
    "_repr_html",
    "_repr_javascript_",
    "_repr_jpeg_",
    "_repr_json_",
    "_repr_latex_",
    "_repr_markdown_",
    "_repr_mimebundle_",
    "_repr_pdf_",
    "_repr_png_",
    "_repr_svg_",
]


class CuratedNamespace(Namespace):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._terms = set()

    def __getitem__(self, key, default=None):
        self._add(key)
        return self.term(key)

    def __getattr__(self, name):
        if name in ipython_checks:
            raise AttributeError
        elif name.startswith("__"):  # ignore any special Python names!
            raise AttributeError
        else:
            self._add(name)
            return self.term(name)

    def _add(self, term):
        self._terms.add(term)

    def __dir__(self):
        return list(self._terms)

    def _ipython_key_completions_(self):
        return list(self._terms)


class NSWrapper:
    """
    A convenience wrapper for namespaces
    """

    def __init__(self, graph=None, names: Dict = None):
        """
        create a ns wrapper
        """
        if graph is None:
            graph = Graph()
        self.__dict__["_graph"] = graph
        self.__dict__["_cnsp"] = cnsp = dict()

        if names is not None:
            for name, space in names.items():
                setattr(self, name, space)

        for key, value in graph.namespaces():
            cnsp[key] = CuratedNamespace(value)

    def __getattr__(self, name):
        """
        wrap a namespace uri in Namespace

        q.ns.rdfs.label
        """
        data = self.__dict__
        nsp = dict(data["_graph"].namespaces())
        cnsp = data["_cnsp"]
        if name in nsp:
            if name not in cnsp:
                cnsp[name] = CuratedNamespace(nsp[name])
            return cnsp[name]
        elif name == "_ipython_canary_method_should_not_exist_":
            # implemented so ipython can find rich repr method
            raise AttributeError("Ipython canary should not exist")
        raise NameError("That prefix isn't defined.")

    def __setattr__(self, prefix, uri_frag):
        """
        wrap a namespace uri in Namespace
        """
        self._graph.namespace_manager.bind(prefix, Namespace(uri_frag))
        self._cnsp[prefix] = CuratedNamespace(uri_frag)

    def __dir__(self):
        """
        return the namespaces we know about for autocomplete
        """
        return dict(self._graph.namespaces()).keys()

    def __getitem__(self, key):
        """Get the qualified name for the given key"""
        return self._graph.qname(key)

    def _add(self, uri):
        """Splits the given uri and adds the term to the prefixed curated namespace
        :param uri: URI
        """
        try:
            qname = self[uri]
        except ValueError:
            # some uris cannot be converted to qnames
            return
        # adding term to curated namespace
        prefix, *suffix = qname.split(":")
        cnsp = getattr(self, prefix)
        if isinstance(cnsp, CuratedNamespace):
            cnsp[":".join(suffix)]

    def _repr_html_(self):
        namespaces = dict(self._graph.namespaces())
        try:
            import pandas as pd

            df = pd.DataFrame([{"Prefix": k, "URL": v} for k, v in namespaces.items()])
            return df.style.set_properties(
                subset=["URL"], **{"width": "600px", "text-align": "left"}
            ).render()
        except ImportError:
            return " ".join(list(namespaces.keys()))
