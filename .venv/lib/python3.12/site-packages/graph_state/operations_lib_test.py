#!/usr/bin/python
# -*- coding: utf8 -*-
#
# Test for operations_lib.py. Provides test cases for useful util functions like determination of connected components,
# irreducibility etc.
#

__author__ = 'dima'


import unittest
import operations_lib
import property_lib
import graph_state
import graph_state_property


config = property_lib.COLORS_AND_FIELDS_CONFIG


class OperationsLibTest(unittest.TestCase):
    def testEdgesForNode(self):
        gs = config.graph_state_from_str("e1|e|")
        self.assertEqual([(-1, 0), (0, 1)], [e.nodes for e in operations_lib.edges_for_node(gs, 0)])

    def testGetExternalNode(self):
        gs = config.graph_state_from_str("e1|e|")
        self.assertEqual(-1, operations_lib.get_external_node(gs))
        self.assertEqual(graph_state_property.Node(-1, object()), operations_lib.get_external_node(gs))

    def testGetBoundVertices(self):
        gs = config.graph_state_from_str("e1|e|")
        self.assertEqual(set([0, 1]), operations_lib.get_bound_vertices(gs))
        self.assertEqual(set([0, 1]), operations_lib.get_bound_vertices(gs.edges))

    def testGetConnectedComponents(self):
        edges = [config.new_edge(nodes) for nodes in [(-1, 0), (0, 1), (1, 2), (2, 3), (3, 4), (4, -1)]]
        components = operations_lib.get_connected_components(edges)
        self.assertEqual(len(components), 1)
        self.assertEqual(set(components[0]), set([0, 1, 2, 3, 4]))

        edges = [config.new_edge(nodes) for nodes in [(-1, 0), (0, 1), (1, 2), (3, 4), (4, -1)]]
        components = operations_lib.get_connected_components(edges)
        self.assertEqual(len(components), 2)
        self.assertEqual(set(components[0]), set([0, 1, 2]))
        self.assertEqual(set(components[1]), set([3, 4]))

        edges = [config.new_edge(nodes) for nodes in [(-1, 0), (0, 1), (1, 2), (2, 3), (3, 4), (4, -1)]]
        components = operations_lib.get_connected_components(edges, additional_vertices=[4, 5])
        self.assertEqual(len(components), 2)

        components = operations_lib.get_connected_components(edges, singular_vertices=set([2]))
        self.assertEqual(len(components), 2)

    def testIsEdgePropertyIsFullyNone(self):
        edges = [config.new_edge(nodes) for nodes in [(-1, 0), (0, 1), (1, 2), (2, 3), (3, 4), (4, -1)]]
        self.assertTrue(operations_lib.is_edge_property_fully_none(edges, "colors"))
        edges[3] = edges[3].copy(colors=(2, 3))
        self.assertFalse(operations_lib.is_edge_property_fully_none(edges, "colors"))

    def testIsGraphConnected(self):
        edges = [config.new_edge(nodes) for nodes in [(-1, 0), (0, 1), (2, -1)]]
        self.assertFalse(operations_lib.is_graph_connected(edges))
        edges.append(config.new_edge((1, 2)))
        self.assertTrue(operations_lib.is_graph_connected(edges))

    def testIsVertexIrreducible(self):
        gs = config.graph_state_from_str("e11|22|e|")
        self.assertFalse(operations_lib.is_vertex_irreducible(gs))

        gs = config.graph_state_from_str("e12|23|3|e|")
        self.assertTrue(operations_lib.is_vertex_irreducible(gs))

    def testIsOneIrreducible(self):
        gs = config.graph_state_from_str("e11|22|e|")
        self.assertTrue(operations_lib.is_1_irreducible(gs))

        gs = config.graph_state_from_str("e1|e|")
        self.assertFalse(operations_lib.is_1_irreducible(gs))

if __name__ == "__main__":
    unittest.main()