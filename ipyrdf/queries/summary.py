"""Collect generic queries to help summary activities"""
from typing import Dict, Iterator, List, Tuple, Type

import ujson
from jinja2 import Template
from rdflib import Graph, URIRef


def get_distinct_ends(graph, match: Tuple[Type] = None) -> Iterator[URIRef]:
    template = Template(
        """
        SElECT DISTINCT ?s
        WHERE {
            {
                ?s ?p ?o
            } UNION {
                ?o ?p ?s
            }

        }
    """
    )
    for result in graph.query(template.render()):
        if match and not isinstance(result[0], match):
            continue
        yield result[0]


def count_distinct_subjects(graph, match: Tuple[Type] = None) -> int:
    template = Template(
        """
        SELECT (COUNT(DISTINCT ?s) AS ?subjects) WHERE { ?s ?p ?o }
    """
    )
    for result in graph.query(template.render()):
        if match and not isinstance(result[0], match):
            continue
        return int(result[0])


def count_distinct_predicates(graph, match: Tuple[Type] = None) -> int:
    template = Template(
        """
        SELECT (COUNT(DISTINCT ?p) AS ?subjects) WHERE { ?s ?p ?o }
    """
    )
    for result in graph.query(template.render()):
        if match and not isinstance(result[0], match):
            continue
        return int(result[0])


def count_distinct_objects(graph, match: Tuple[Type] = None) -> int:
    template = Template(
        """
        SELECT (COUNT(DISTINCT ?o) AS ?subjects) WHERE { ?s ?p ?o }
    """
    )
    for result in graph.query(template.render()):
        if match and not isinstance(result[0], match):
            continue
        return int(result[0])


def to_jsonld(graph: Graph, context: Dict = None) -> Dict:
    """Helper function to generate json-ld from the input rdf graph

    :param graph: input graph
    :param context: json-ld context, if not provided it will extract the namespaces
    from the input graph
    :return: json-ld
    """
    if context is None:
        context = {k: str(v) for k, v in graph.namespaces()}
    return ujson.loads(graph.serialize(format="json-ld", context=context))


def describe(graph: Graph, uris: List[URIRef]) -> Graph:
    if isinstance(uris, URIRef):
        uris = [uris]

    result = Graph(namespace_manager=graph.namespace_manager)
    for uri in uris:
        patterns = [
            [uri, None, None],
            [None, None, uri],
        ]
        for pattern in patterns:
            for spo in graph.triples(pattern):
                result.add(spo)
    return result
