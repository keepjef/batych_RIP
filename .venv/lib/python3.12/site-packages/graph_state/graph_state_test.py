#!/usr/bin/python
# -*- coding: utf8 -*-
#
# test creation of GraphState object (from string, by constructor)
# and base methods (getting structure information, edge sortings) of GraphState and Edge objects.
#

import graph_state
import graph_state_property
import property_lib
import unittest

new_edge = property_lib.COLORS_AND_FIELDS_CONFIG.new_edge
new_properties = property_lib.COLORS_AND_FIELDS_CONFIG.new_properties


class TestFields(unittest.TestCase):
    def testCopy(self):
        fields = property_lib.Fields('ab')
        self.assertEqual(fields, fields.copy())
        swapped = fields.copy(swap=True)
        self.assertTrue(fields != swapped)
        self.assertEqual(fields, swapped.copy(swap=True))

    def testToFromString(self):
        fields = property_lib.Fields('ab')
        self.assertEqual(len(str(fields)), property_lib.Fields.STR_LEN)
        decoded = property_lib.Fields.from_str(str(fields))
        self.assertEqual(fields, decoded)

    def testFieldsToFromString(self):
        string = 'aBcD'
        fields = property_lib.Fields.fieldsFromStr(string)
        self.assertEqual(len(fields), 2)
        self.assertEqual(property_lib.Fields.fieldsToStr(fields),
                         string)

    def testHash(self):
        first = property_lib.Fields('ab')
        second = property_lib.Fields('ba').copy(swap=True)
        self.assertTrue(first == second)
        self.assertTrue(hash(first) == hash(second))


class TestRainbow(unittest.TestCase):
    def testToFromStr(self):
        r = property_lib.Rainbow((0, 1))
        self.assertEqual(str(r), '(0, 1)')
        self.assertEqual(r, property_lib.Rainbow.fromObject(str(r)))

    def testFromStr2(self):
        r = property_lib.Rainbow.fromObject("\"asd\"")
        self.assertEqual(r.colors, ("asd",))


class TestEdge(unittest.TestCase):
    def testCompare(self):
        self.assertEqual(new_edge((0, 1)), new_edge((1, 0)),
                         'Non-typed edges should not depend on nodes order.')
        self.assertTrue(new_edge((0, 1)) < new_edge((0, 2)))
        # (-1, 0) < (0, 1) < (1, -1) - Nickel ordering.
        self.assertTrue(new_edge((-1, 0)) < new_edge((0, 1)))
        self.assertTrue(new_edge((0, 1)) < new_edge((1, -1)))
        self.assertTrue(new_edge((-1, 0)) < new_edge((1, -1)))

    def testCompareWithFields(self):
        self.assertEqual(
            new_edge((0, 1), fields=property_lib.Fields('ab')),
            new_edge((1, 0), fields=property_lib.Fields('ba')))

        cmp_fields = cmp(property_lib.Fields('ab'), property_lib.Fields('ba'))
        cmp_edges = cmp(
            new_edge((0, 1), fields=property_lib.Fields('ab')),
            new_edge((0, 1), fields=property_lib.Fields('ba')))
        self.assertEqual(cmp_fields, cmp_edges)

    def testExternalNode(self):
        self.assertEqual(new_edge((0, 1), external_node=1),
                         new_edge((0, 2), external_node=2))

    def testAnnotateExternalField(self):
        edge = new_edge((0, 1),
                        external_node=1,
                        fields=property_lib.Fields('ab'))
        self.assertEqual(edge.fields.pair[0], 'a')
        self.assertEqual(edge.fields.pair[1], edge.fields.EXTERNAL)

    def testCopy(self):
        edge = new_edge((0, 1),
                        external_node=1,
                        fields=property_lib.Fields('ab'),
                        colors=property_lib.Rainbow((0,)),
                        edge_id=333)
        missed_attrs = [attr for attr in edge.__dict__ if not edge.__dict__[attr]]
        self.assertEqual(len(missed_attrs), 0,
                         'Attributes %s should be set.' % missed_attrs)

        self.assertEqual(edge, edge.copy())
        self.assertTrue(edge < edge.copy(node_map={0: 2}))

    def testHash(self):
        a = new_edge((0, 1), external_node=1,
                     fields=property_lib.Fields('ab'))
        b = new_edge((0, 1), external_node=1,
                     fields=property_lib.Fields('ab'))
        self.assertTrue(a == b)
        self.assertTrue(hash(a) == hash(b))


class TestGraphState(unittest.TestCase):
    def testGraphStateObjectsEqual(self):
        edges = tuple([new_edge(e, colors=property_lib.Rainbow((1, 2, 3))) for e in [(-1, 0), (0, 1), (1, -1)]])
        state1 = graph_state.GraphState(edges)
        state2 = graph_state.GraphState.from_str(str(state1), property_lib.COLORS_AND_FIELDS_CONFIG)
        self.assertEqual(state1, state2)

    def testEdgeId(self):
        edges = [new_edge(e, colors=(1, 2, 3)) for e in [(-1, 0), (0, 1), (1, -1)]]
        ids = map(lambda e: e.edge_id, edges)
        self.assertEqual(len(set(ids)), 3)

    def testInit(self):
        edges = tuple([new_edge(e, colors=(1, 2, 3))
                       for e in [(-1, 0), (0, 1), (1, -1)]])
        state = graph_state.GraphState(edges, node_maps=[{}])
        self.assertEqual(state.sortings, [edges])

        state = graph_state.GraphState(edges, node_maps=[{0: 1, 1: 0}])
        self.assertEqual(state.sortings, [edges])

        state = graph_state.GraphState(edges, node_maps=[{}, {}])
        self.assertEqual(state.sortings, [edges, edges])

        state = graph_state.GraphState(edges, node_maps=[{1: 2}])
        self.assertTrue(state.sortings != [edges])

    def testSymmetries(self):
        edges = [new_edge((-1, 0), fields=property_lib.Fields('aa')),
                 new_edge((0, 1), fields=property_lib.Fields('aa')),
                 new_edge((1, -1), fields=property_lib.Fields('aa'))]
        state = graph_state.GraphState(edges)
        self.assertEqual(len(state.sortings), 2, 'Symmetry 0 <--> 1.')

        edges[1] = new_edge((0, 1), fields=property_lib.Fields('ab'))
        state = graph_state.GraphState(edges)
        self.assertEqual(len(state.sortings), 1, 'No symmetry 0 <--> 1.')

    def testHash(self):
        a = graph_state.GraphState((new_edge((0, -1)),))
        b = graph_state.GraphState((new_edge((0, -1)),))
        self.assertTrue(a == b)
        self.assertTrue(hash(a) == hash(b))

    def testToFromStr(self):
        edges = (new_edge((-1, 0)),
                 new_edge((0, 1)),
                 new_edge((1, -1)))
        state = graph_state.GraphState(edges)
        self.assertEqual(str(state), 'e1|e|::')

        decoded = graph_state.GraphState.from_str(str(state), property_lib.COLORS_AND_FIELDS_CONFIG)
        self.assertEqual(decoded.sortings[0], edges)

    def testToFromStr1(self):
        actual_state = graph_state.GraphState.from_str("e1|e|", property_lib.COLORS_AND_FIELDS_CONFIG)
        self.assertEqual("e1|e|::", str(actual_state))
        edges = (new_edge((-1, 0)),
                 new_edge((0, 1)),
                 new_edge((1, -1)))
        expected_state = graph_state.GraphState(edges)
        self.assertEqual(actual_state, expected_state)

    def testToFromStrWithFields(self):
        edges = (new_edge((-1, 0), fields=property_lib.Fields('0a')),
                 new_edge((0, 1), fields=property_lib.Fields('ab')),
                 new_edge((1, -1), fields=property_lib.Fields('a0')))
        state = graph_state.GraphState(edges)
        self.assertEqual(str(state), 'e1|e|::0a_ab|0a|')

        decoded = graph_state.GraphState.from_str(str(state), property_lib.COLORS_AND_FIELDS_CONFIG)
        self.assertEqual(decoded.sortings[0], edges)

    def testToFromStrWithColors(self):
        edges = (new_edge((-1, 0), colors=property_lib.Rainbow((1, 7))),)
        state = graph_state.GraphState(edges)
        self.assertEqual(str(state), "e|:(1, 7)|:")

        decoded = graph_state.GraphState.from_str(str(state), property_lib.COLORS_AND_FIELDS_CONFIG)
        self.assertEqual(decoded.sortings[0], edges)


class TestProperties(unittest.TestCase):
    def testCustomUndirectedProperty(self):
        class MyProperty(object):
            def __init__(self, a, b):
                self.a = a + 1
                self.b = b - 1

            def __str__(self):
                return str((self.a - 1, self.b + 1))

            def __eq__(self, other):
                return self.a == other.a and self.b == other.b

            def __hash__(self):
                return self.a + self.b * 31

            __repr__ = __str__

        class MyPropertyExternalizer(graph_state_property.PropertyExternalizer):
            def serialize(self, obj):
                return str(obj)

            def deserialize(self, string):
                return MyProperty(*eval(string))

        property_key = graph_state_property.PropertyKey(name='some_name',
                                                        is_directed=False,
                                                        externalizer=MyPropertyExternalizer())
        config = graph_state.PropertiesConfig.create(property_key)

        state = graph_state.GraphState.from_str("e1|e|:(0,0)_(1,0)|(3,9)|", properties_config=config)
        es = set(map(lambda b: b.some_name, filter(lambda a: a.is_external(), state.edges)))
        self.assertEqual(es, set((MyProperty(3, 9), MyProperty(0, 0))))

    def testDirectedCustomProperty(self):
        class MyProperty(object):
            def __init__(self, a, b):
                self.a = a + 1
                self.b = b - 1

            def __str__(self):
                return str((self.a + 1, self.b - 1))

            __repr__ = __str__

            def __neg__(self):
                return MyProperty(self.b, self.a)

            def __eq__(self, other):
                return self.a == other.a and self.b == other.b

        class MyPropertyExternalizer(graph_state_property.PropertyExternalizer):
            def serialize(self, obj):
                return str(obj)

            def deserialize(self, string):
                return MyProperty(*eval(string))

        property_key = graph_state_property.PropertyKey(name='some_name',
                                                        is_directed=True,
                                                        externalizer=MyPropertyExternalizer())
        config = graph_state.PropertiesConfig.create(property_key)

        state = graph_state.GraphState.from_str("e12|2|e|:(1,0)_(1,0)_(1,0)|(1,0)|(1,0)|", properties_config=config)
        e = state.edges[3]
        self.assertEqual(e.nodes, (-1, 1))
        self.assertEqual(e.some_name, MyProperty(1, 0))

    def testEmptyProperties(self):
        self.assertEqual(str(property_lib.EMPTY_CONFIG.graph_state_from_str("e|")), "e|")


if __name__ == "__main__":
    unittest.main()