#!/usr/bin/python
# -*- coding: utf8 -*-
#
# Test for GraphState objects which have nodes with some properties (see graph_state.PropertyKey).
#

__author__ = 'dima'

import graph_state_property
import operations_lib
import property_lib
import graph_state
import unittest


config = \
    graph_state.PropertiesConfig.create(graph_state_property.PropertyKey(name='e_num',
                                                                         is_directed=False,
                                                                         is_edge_property=True,
                                                                         externalizer=graph_state_property.PropertyExternalizer()),
                                        graph_state_property.PropertyKey(name='n_num',
                                                                         is_directed=False,
                                                                         is_edge_property=False,
                                                                         externalizer=graph_state_property.PropertyExternalizer()),
                                        graph_state_property.PropertyKey(name='e_arrow',
                                                                         is_directed=True,
                                                                         is_edge_property=True,
                                                                         externalizer=property_lib.Arrow.Externalizer()))

config2 = graph_state.PropertiesConfig.create(graph_state_property.PropertyKey(name='n_num',
                                                                               is_directed=False,
                                                                               is_edge_property=False,
                                                                               externalizer=graph_state_property.PropertyExternalizer()))


class GraphStatePropertiesTest(unittest.TestCase):
    def testAllNoneProperties(self):
        gs = config.graph_state_from_str('e1|e|')
        self.assertEqual(str(gs), 'e1|e|:::')
        for n in gs.nodes:
            self.assertEqual(n.n_num, None)

    def testEdgesPropertiesNotEmpty(self):
        gs = config.graph_state_from_str('e1|e|:2_1|0|:20|30:0_>|0|')
        self.assertEqual(str(gs), 'e1|e|:0_1|2|:30|20:0_<|0|')
        self.assertEqual(str(gs.nodes[0]), 'n[-1, n_num=None]')
        self.assertEqual(gs.nodes[0].index, -1)
        for n in gs.nodes[1:]:
            self.assertTrue(n.n_num in (20, 30))
            self.assertTrue(n.index in (0, 1))
            self.assertTrue(str(n) in ('n[0, n_num=30]', 'n[1, n_num=20]'))

    def testOrderingByNodes(self):
        gs1 = config2.graph_state_from_str('e1|e|:5|1')
        gs2 = config2.graph_state_from_str('e1|e|:1|5')
        self.assertEqual(str(gs1), str(gs2))
        self.assertEqual(gs1, gs2)
        gs3 = config2.graph_state_from_str(str(gs2))
        self.assertEqual(gs3, gs1)

    def testOrderingByNodes2(self):
        gs1 = config.graph_state_from_str('e1|e|:1_1|1|:20|30:0_>|0|')
        gs2 = config.graph_state_from_str('e1|e|:1_1|1|:30|20:0_<|0|')
        self.assertEqual(gs1, gs2)

    def testNodeCreation(self):
        n = config.new_node(2, n_num=2)
        self.assertEqual('n[2, n_num=2]', str(n))
        self.assertEqual(2, n.index)
        self.assertEqual(2, n.n_num)

    def testEdgeCreation(self):
        e = config.new_edge((2, 5))
        self.assertEqual(str(e.nodes[0]), 'n[2, n_num=None]')
        self.assertEqual(str(e.nodes[1]), 'n[5, n_num=None]')

        e = config.new_edge((config.new_node(2, n_num=5), config.new_node(5, n_num=2)))
        self.assertEqual(str(e.nodes[0]), 'n[2, n_num=5]')
        self.assertEqual(str(e.nodes[1]), 'n[5, n_num=2]')

        e = graph_state.DEFAULT_PROPERTIES_CONFIG.new_edge((2, 5))
        self.assertEqual(str(e.nodes[0]), '2')
        self.assertEqual(str(e.nodes[1]), '5')
        self.assertEqual(e.nodes[0], 2)
        self.assertEqual(e.nodes[1], 5)


if __name__ == '__main__':
    unittest.main()