#!/usr/bin/python
# -*- coding: utf8 -*-
"""
Module provides some useful operations on graphs such obtaining nodes of graph or connected components.

All of functions in module marked with :func:`@_graph_state_to_edges_implicit_conversion`
can take list of edges or :class:`GraphState` object as parameter as well.
"""
__author__ = 'dima'

import graph_state
from functools import wraps


def _graph_state_to_edges_implicit_conversion(edges_first_parameter_function):
    """
    First edges parameter can be both list of edges and :class:`GraphState`.
    """
    @wraps(edges_first_parameter_function)
    def graph_state_first_parameter_function(some_obj, *other_params, **other_kwargs):
        return edges_first_parameter_function(some_obj.edges
                                              if isinstance(some_obj, graph_state.GraphState)
                                              else some_obj, *other_params, **other_kwargs)

    return graph_state_first_parameter_function

@_graph_state_to_edges_implicit_conversion
def edges_for_node(edges, node):
    """
    :return: only edges that contain node
    """
    return filter(lambda e: node in e.nodes, edges)

@_graph_state_to_edges_implicit_conversion
def split_edges_for_node(edges, node):
    """
    :return: only edges that contain node
    """
    with_node = list()
    without_node = list()
    for e in edges:
        (with_node if node in e.nodes else without_node).append(e)
    return with_node, without_node

@_graph_state_to_edges_implicit_conversion
def get_external_node(edges):
    """
    Method does not check that all edges have same external node and returns :func:`external_node`
    field of first occurred edge.

    :returns: external node for edges
    """
    return edges[0].external_node


@_graph_state_to_edges_implicit_conversion
def get_bound_vertices(edges):
    """
    :returns: non-external nodes of external edges
    """
    result = set()
    for e in edges:
        if e.is_external():
            result.add(e.internal_node)
    return result


@_graph_state_to_edges_implicit_conversion
def get_vertices(edges):
    """
    :returns: all nodes including external
    """
    return frozenset(reduce(lambda s, e: s + e.nodes, edges, tuple()))


def get_connected_components(edges, additional_vertices=set(), singular_vertices=set()):
    """
    :returns: get lists of connected undirected graph nodes
    
    :param additional_vertices: any additional nodes which will be included to result
    :type additional_vertices: set
    :param singular_vertices: nodes that not produce connection between nodes. All edges containing these nodes will be ignored
    :type singular_vertices: set
    """
    if not len(edges):
        return tuple()
    if len(additional_vertices):
        additional_vertices = set(additional_vertices)
    external_vertex = get_external_node(edges)

    if external_vertex in additional_vertices:
        additional_vertices.remove(external_vertex)
    disjoint_set = DisjointSet(additional_vertices)

    for e in edges:
        pair = e.nodes
        if external_vertex in pair:
            for v in set(pair) - set([external_vertex]):
                disjoint_set.add_key(v)
            continue

        v = pair[0]
        if v in singular_vertices:
            pair = (disjoint_set.next_singular_key(v)), pair[1]
        v = pair[1]
        if v in singular_vertices:
            pair = pair[0], (disjoint_set.next_singular_key(v))

        disjoint_set.union(pair)
    return disjoint_set.get_connected_components()


@_graph_state_to_edges_implicit_conversion
def is_edge_property_fully_none(edges, property_name):
    """
    Checks that property with given name is **None** for all edges
    """
    assert property_name is not None
    for e in edges:
        if getattr(e, property_name) is not None:
            return False
    return True


@_graph_state_to_edges_implicit_conversion
def has_no_tadpoles_in_counter_term(edges, super_graph_edges):
    # TODO dima forgot what this method do
    if not len(edges):
        return False
    external_node = get_external_node(super_graph_edges)
    edges_copy = list(super_graph_edges)
    singular_vertices = set()
    for e in edges:
        if e in edges_copy:
            edges_copy.remove(e)
        singular_vertices |= set(e.nodes)
    connected_components = get_connected_components(edges_copy, (external_node,), singular_vertices=singular_vertices)
    for component in connected_components:
        all_singular = True
        for v in component:
            if not DisjointSet.is_singular(v):
                all_singular = False
                break
        if all_singular:
            return False
        contains_external = False
        for v in component:
            for e in edges_for_node(super_graph_edges, v):
                if e.is_external():
                    contains_external = True
        if not contains_external:
            return False
    return True


@_graph_state_to_edges_implicit_conversion
def is_graph_connected(edges, additional_vertices=set()):
    """
    Checks that graph is connected. See :func:`get_connected_components`
    """
    return len(get_connected_components(edges, additional_vertices)) == 1 if len(edges) else True


@_graph_state_to_edges_implicit_conversion
def is_vertex_irreducible(edges):
    """
    Checks that graph is vertex irreducible
    """
    external_node = get_external_node(edges)
    vertices = get_vertices(edges)
    if len(vertices - set([external_node])) == 1:
        return True
    if len(vertices) == 2:
        return len(edges) - len(edges_for_node(edges, external_node)) > 0
    for v in vertices:
        for e in edges_for_node(edges, v):
            if e.nodes[0] == e.nodes[1]:
                return False
        if v is not external_node:
            _edges = list(edges)
            for e in edges_for_node(edges, v):
                _edges.remove(e)
            additional_vertices = set(vertices)
            additional_vertices.remove(v)
            if not is_graph_connected(_edges, additional_vertices=additional_vertices):
                return False
    return True


@_graph_state_to_edges_implicit_conversion
def is_1_irreducible(edges):
    """
    Checks that graph is 1-irreducible
    """
    if len(edges):
        external_node = get_external_node(edges)
        for e in edges:
            if e.is_external():
                continue
            copied_edges = list(edges)
            copied_edges.remove(e)
            if not is_graph_connected(copied_edges, additional_vertices=set([v for v in e.nodes]) - set([external_node])):
                return False
    return True


class DisjointSet(object):
    def __init__(self, keys=set()):
        self.underlying = dict()
        for k in keys:
            self.underlying[k] = k
        self.singular_key_prefix = 1

    def add_key(self, key):
        if key not in self.underlying:
            self.underlying[key] = key

    def root(self, a):
        a_root = a
        a_next = self.underlying[a_root]
        while a_next != a_root:
            a_root = a_next
            a_next = self.underlying[a_root]
        return a_root

    def union(self, pair):
        a, b = pair
        self.add_key(a)
        self.add_key(b)
        if a is b:
            return
        a_root = self.root(a)
        b_root = self.root(b)
        if a_root is not b_root:
            self.underlying[a_root] = b_root

    def get_connected_components(self):
        connected_components = dict()
        for k in self.underlying.keys():
            k_root = self.root(k)
            if k_root in connected_components:
                connected_components[k_root].append(k)
            else:
                connected_components[k_root] = [k]
        return connected_components.values()

    def next_singular_key(self, key):
        prefix = self.singular_key_prefix
        self.singular_key_prefix += 1
        return "__%s_%s" % (prefix, key)

    @staticmethod
    def is_singular(key):
        return str(key).startswith("__")