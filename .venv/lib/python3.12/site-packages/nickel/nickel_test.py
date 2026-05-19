#!/usr/bin/python
# 
# Test for generation of Nickel index from edges
#

import nickel

import unittest


class TestNickel(unittest.TestCase):
    def testRaisesOnManyArgs(self):
        self.assertRaises(nickel.InputError, nickel.Nickel, edges=[], nickel=[])

    def testNickelFromEdges(self):
        e = nickel.Nickel(edges=[[0, -1], [-1, 0]])
        self.assertEqual(e.nickel, [[-1, -1]])
        self.assertEqual(e.string, 'ee|')

        s = nickel.Nickel(string='ee|')
        self.assertEqual(s.nickel, [[-1, -1]])
        self.assertEqual(s.edges, e.edges)

        ee = nickel.Nickel(edges=[[0, -1], [-1, 0], [2, 1], [1, 0]])
        self.assertEqual(ee.nickel, [[-1, -1, 1], [2], []])
        self.assertEqual(ee.string, 'ee1|2||')

        ss = nickel.Nickel(string='ee1|2|')
        self.assertEqual(ss.nickel, [[-1, -1, 1], [2]])
        self.assertEqual(ss.edges, ee.edges)

        s1 = nickel.Nickel(string='eE|')
        self.assertEqual(s1.nickel, [[-1, 14]])
        self.assertEqual(s1.edges, [[-1, 0], [0, 14]])

    def testNickelFromEdgeTuples(self):
        e = nickel.Nickel(edges=[(0, -1), (-1, 0)])
        self.assertEqual(e.nickel, [[-1, -1]])
        self.assertEqual(e.string, 'ee|')

        e = nickel.Nickel(edges=[(-1, 0), (0, 1), (1, -1)])
        self.assertEqual(e.nickel, [[-1, 1], [-1]])

    def testNickelEdgesSort(self):
        n = nickel.Nickel(edges=[(-1, 0), (-1, 1), (0, 1)])
        self.assertEqual(n.edges, [[-1, 0], [0, 1], [-1, 1]])

    def testNickelToAdjacent(self):
        n = nickel.Nickel(nickel=[[1], []])
        self.assertEqual({0: [1], 1: [0]}, n.adjacent)
        n = nickel.Nickel(nickel=[[1]])
        self.assertNotEqual({0: [1], 1: [0]}, n.adjacent)
        n = nickel.Nickel(nickel=[[-1, 1], [-1]])
        self.assertEqual({0: [-1, 1], 1: [-1, 0]}, n.adjacent)

    def testAdjacentDobleEdge(self):
        n = nickel.Nickel(edges=[[0, 1], [0, 1]])
        self.assertEqual({0: [1, 1], 1: [0, 0]}, n.adjacent)

    def testVacuumBubble(self):
        n = nickel.Nickel(edges=[[0, 1], [0, 1]])
        self.assertEqual('11||', n.string)
        n = nickel.Nickel(edges=[[0, 0]])
        self.assertEqual('0|', n.string)


class TestCanonicalize(unittest.TestCase):
    def testInit(self):
        c = nickel.Canonicalize([[-1, 0]])
        init = c.InitStates([[-1, 10]])
        self.assertEqual(len(init), 1)
        self.assertEqual(len(c.InitStates([[-1, 10], [10, 11], [11, -1]])), 2)

    def testRaise(self):
        self.assertRaises(nickel.InputError, nickel.Canonicalize, [[0, 1], [2, 3]])

    def testCanon(self):
        c = nickel.Canonicalize([[-1, 0]])
        self.assertEqual(c.num_symmetries, 1)
        self.assertEqual(c.nickel, [[-1]])

    def testCanon1(self):
        c = nickel.Canonicalize([[-1, 0], [-1, 0]])
        self.assertEqual(c.num_symmetries, 1)
        self.assertEqual(c.nickel, [[-1, -1]])

    def testCanon2(self):
        c = nickel.Canonicalize([[-1, 10], [-1, 11], [10, 11]])
        self.assertEqual(c.nickel, [[-1, 1], [-1]])
        self.assertEqual(c.num_symmetries, 2)
        self.assertEqual(c.node_maps, [{10: 0, 11: 1}, {10: 1, 11: 0}])

    def testCanon3(self):
        c = nickel.Canonicalize([[-1, 11], [-1, 11], [-1, 10], [10, 11]])
        self.assertEqual(c.num_symmetries, 1)
        self.assertEqual(c.nickel, [[-1, -1, 1], [-1]])

    def testCanon4(self):
        c = nickel.Canonicalize([[-1, 0], [0, 1], [0, 2], [1, 2], [1, 3], [2, 3],
                                                        [3, -1]])
        self.assertEqual(c.num_symmetries, 4)
        self.assertEqual(c.nickel, [[-1, 1, 2], [2, 3], [3], [-1]])

    def testCanon5(self):
        c = nickel.Canonicalize([[-1, 3], [-1, 4], [-1, 5], [3, 4], [3, 5],
                                 [4, 6], [5, 7], [6, 8], [6, 8], [7, 9], [7, 9],
                                 [8, 10], [9, 11], [10, 11], [10, 11]])
        self.assertEqual(c.num_symmetries, 2)
        self.assertEqual(c.nickel, [[-1, 1, 2], [-1, 3], [-1, 4], [5, 5],
                                    [6, 6], [7], [8], [8, 8], []])

    def testCanon6(self):
        c = nickel.Canonicalize([[-1, 3], [-1, 4], [-1, 7], [3, 4], [3, 5],
                                 [4, 6], [5, 6], [5, 7], [6, 8], [7, 9], [8, 9],
                                 [8, 10], [9, 11], [10, 11], [10, 11]])
        self.assertEqual(c.num_symmetries, 1)
        self.assertEqual(c.nickel, [[-1, 1, 2], [-1, 3], [3, 4], [5], [-1, 6],
                                    [6, 7], [8], [8, 8], []])

    def testCanon7(self):
        c = nickel.Canonicalize([[-1, 2], [-1, 3], [2, 3], [2, 4], [3, 5],
                                 [4, 6], [4, 7], [5, 6], [5, 7], [6, 8], [7, 9],
                                 [8, 9], [8, 9]])
        self.assertEqual(c.num_symmetries, 4)
        self.assertEqual(c.nickel, [[-1, 1, 2], [-1, 3], [4, 5], [4, 5], [6],
                                    [7], [7, 7], []])


class TestGetGroupedEdges(unittest.TestCase):
    def testPermutatedFromCanonical(self):
        perm = nickel.PermutatedFromCanonical([{1: 'a', 2: 'b'},
                                               {1: 'b', 2: 'a'}])
        self.assertEqual(perm, [{1: 1, 2: 2}, {1: 2, 2: 1}])

    def test1(self):
        c = nickel.Canonicalize([[-1, 1], [1, 2], [2, -1]])
        self.assertEqual(c.GetGroupedEdges(),
                         [[[-1, 1], [2, -1]], [[1, 2]]])

    def test2(self):
      c = nickel.Canonicalize([[-1, 1], [1, 2], [1, 2], [2, -1]])
      self.assertEqual(c.GetGroupedEdges(),
                       [[[-1, 1], [2, -1]], [[1, 2], [1, 2]]])

    def test3(self):
      c = nickel.Canonicalize([[-1, 1], [1, 2], [1, 3], [2, 3],
                               [2, 4], [3, 4], [4, -1]])
      self.assertEqual(sorted(c.GetGroupedEdges()),
                       sorted([[[-1, 1], [4, -1]], [[2, 3]],
                               [[1, 2], [1, 3], [2, 4], [3, 4]]]))


class TestExpander(unittest.TestCase):
    def compareExpanders(self, l, r):
        self.assertEqual(l.curr_node, r.curr_node)
        self.assertEqual(l.free_node, r.free_node)
        self.assertEqual(l.edges, r.edges)
        self.assertEqual(l.nickel_list, r.nickel_list)
        self.assertEqual(l.node_map, r.node_map)

    def testExpand(self):
        input = nickel.Expander([[-1, 0]], [], {}, 0, 1)
        output = nickel.Expander([], [[-1]], {}, 1, 1)
        l = list(input.Expand())
        self.assertEqual(len(l), 1)
        self.compareExpanders(l[0], output)

    def testExpand2(self):
        input = nickel.Expander([[-1, 1], [1, 2], [1, 13], [1, 14]], [[1, 2]],
                                {10: 0, 11: 1, 12: 2}, 1, 3)
        output = nickel.Expander([], [[1, 2], [-1, 2, 3, 4]],
                                 {10: 0, 11: 1, 12: 2, 13: 3, 14: 4}, 2, 5)
        l = list(input.Expand())
        self.assertEqual(len(l), 2)
        self.compareExpanders(l[0], output)

    def testStopExpand(self):
        output = nickel.Expander([], [[-1, 1]], {10: 1}, 1, 2)
        l = list(output.Expand())
        self.assertEqual(l[0].nickel_list, [[-1, 1], []])

    def testCmp(self):
        input = nickel.Expander([[-1, 0], [0, 10]], [], {}, 0, 1)
        output = nickel.Expander([], [[-1, 1]], {10: 1}, 1, 2)
        self.assertEqual(input, output)



class TestUtil(unittest.TestCase):
    def testAdjacentNodes(self):
        self.assertEqual(nickel.AdjacentNodes(1, [[1, 0], [0, 2], [2,1]]),
                         [0, 2])
        self.assertEqual(nickel.AdjacentNodes(0, [[-1, 0]]), [-1])

    def testIsConnected(self):
        conn = nickel.IsConnected
        self.assertFalse(conn([]))
        self.assertTrue(conn([[0, 1]]))
        self.assertTrue(conn([(0, 1)]))
        self.assertTrue(conn(((0, 1),)))
        self.assertTrue(conn([[-1, 0], [0, 1]]))
        self.assertFalse(conn([[-1, 0], [2, 1]]))
        self.assertTrue(conn([[1, 0], [3, 4], [1, 2], [2, 3]]))

    def testFlatten(self):
        self.assertEqual(nickel.flatten([[1, 2], [3, 4]]), [1, 2, 3, 4])
        self.assertEqual(nickel.flatten([(1, 2), (3, 4)]), [1, 2, 3, 4])


class TestOrigNickel(unittest.TestCase):
    def _testStr(self, orig_str):
        c = nickel.Canonicalize(nickel.Nickel(string=orig_str).edges)
        self.assertEqual(orig_str, str(c))

    def testOrigNickelCompare(self):
        self._testStr('e12|e3|333||')
        self._testStr('e123|e24|34|e4|e|')
        self._testStr('e112|e2|33|44|56|e66|e|')
        # Vacuum loops.
        self._testStr('111||')
        self._testStr('123|23|3||')
        self._testStr('112|3|33||')

    def testFromStr(self):
        not_minimum = 'e1|3|e3||'
        n = nickel.Nickel(string=not_minimum)
        self.assertEqual(n.string, not_minimum)
        c = nickel.Canonicalize(nickel.Nickel(string=not_minimum).edges)
        self.assertEqual('e1|2|3|e|', str(c))


if __name__ == "__main__":
    unittest.main()

