#!/usr/bin/python
# -*- coding:utf8

import collections
import itertools
import sys


def chain_from_iterables(iterables):
    for it in iterables:
        for element in it:
            yield element

if  'chain_from_iterables' not in itertools.__dict__:
    itertools.chain_from_iterables = chain_from_iterables


LEG = -1


class Nickel(object):
    """Class to convert graph representations.

    Possible representations are serialized Nickel-string, list of edges,
    Nickel-list of nodes, node adjacency dictionary.
    Usage:
    >>> n = nickel.Nickel(edges=[[-1, 0], [0, 1], [1, -1]])
    >>> n.nickel
    [[-1, 1], [-1]]
    >>> n.string
    'e1-e-'
    """
    SEP = '|'
    _SEP_ID = -600
    NODE_TO_CHAR = {_SEP_ID: SEP, LEG: 'e', 10: 'A', 11: 'B', 12: 'C',
                    13: 'D', 14: 'E', 15: 'F'}
    def __init__(self, edges=None, nickel=None, string=None):
        num_args = len(filter(lambda x: x is not None, (edges, nickel, string)))
        if num_args != 1:
            raise InputError(
                'Exactly one argument is expected. Received %d' % num_args)
        self._edges = None
        self._nickel = None
        self._string = None
        self._adjacent = None
        if edges != None:
            self._nickel = self.NickelFromEdges(edges)
        elif nickel != None:
            self._nickel = [sorted(nn) for nn in nickel]
        elif string != None:
            self._string = string
            self._nickel = self.NickelFromString(string)

    @property
    def nickel(self):
        # nickel is the main representation and is expected to be set.
        return self._nickel

    @property
    def edges(self):
        if self._edges is None:
            self._edges = self.EdgesFromNickel(self._nickel)
        return self._edges

    @property
    def string(self):
        if self._string is None:
            self._string = self.StringFromNickel(self._nickel)
        return self._string

    @property
    def adjacent(self):
        if self._adjacent is None:
            self._adjacent = self.NickelToAdjacent(self._nickel)
        return self._adjacent

    @classmethod
    def NickelFromEdges(self, edges):
        node_limit = max(flatten(edges)) + 1
        nickel = [[] for _ in range(node_limit)]
        for e in edges:
            [s, d] = sorted(e, key=lambda n: n if n >= 0 else node_limit)
            nickel[s].append(d)
        for nn in nickel:
            nn.sort()
        return nickel

    @classmethod
    def EdgesFromNickel(self, nickel):
        edges = []
        for n in range(len(nickel)):
            for m in nickel[n]:
                edges.append(sorted([n, m]))
        return edges

    @classmethod
    def StringFromNickel(self, nickel):
        temp = [nn + [self._SEP_ID] for nn in nickel]
        temp = tuple(iflatten(temp))
        temp = [str(Nickel.NODE_TO_CHAR.get(n, n)) for n in temp]
        return ''.join(temp)

    @classmethod
    def NickelFromString(self, string):
        char_to_node = dict(zip(self.NODE_TO_CHAR.values(),
                                self.NODE_TO_CHAR.keys()))
        flat_nickel = [int(char_to_node.get(c, c)) for c in string]
        nickel = []
        accum = []
        for n in flat_nickel:
            if n != self._SEP_ID:
                accum.append(n)
            else:
                nickel.append(accum)
                accum = []
        return nickel

    @staticmethod
    def NickelToAdjacent(nickel_list):
        """Returns map of node id to adjacent nodes."""
        adjacent = {}
        backward_nodes = collections.defaultdict(list)
        for node_id, forward_nodes in enumerate(nickel_list):
            for forward_node in forward_nodes:
                backward_nodes[forward_node].append(node_id)
            adjacent[node_id] = backward_nodes[node_id]
            adjacent[node_id].extend(forward_nodes)
        for node in adjacent:
            adjacent[node].sort()
        return adjacent


class InputError(Exception):
    """Rased when Canonicalize is called with wrong input.
    """
    pass


class Canonicalize(object):
    """Class to find canonical node maping and to give Nickel node list for it.

    Negative nodes assumed to be external. Non-negative ones - internal.
    Usage:
        c = nickel.Canonicalize([[-1, 10], [-1, 11], [10, 11]])
        assertEqual(c.nickel, [[-1, 1], [-1]])
        assertEqual(c.num_symmetries, 2)
        assertEqual(c.node_maps, [{10: 0, 11: 1}, {10: 1, 11: 0}])
    """
    def __init__(self, edges):
        if not IsConnected(edges):
            raise InputError('Input edge list is an unconnected graph.')

        self.orig = edges

        num_internal_nodes = 0
        for n in set(iflatten(edges)):
            if n >= 0:
                num_internal_nodes += 1

        # Shift original nodes to free space for canonical numbers.
        offset = max(100, num_internal_nodes)
        def shift(n):
            return n + offset if n >= 0 else LEG
        self.edges = [[shift(n), shift(m)] for [n, m] in edges]

        # Do the work.
        self.curr_states = self.InitStates(self.edges)
        for _ in range(num_internal_nodes):
            self.curr_states = self.DoExpand(self.curr_states)

        # Collect results.
        nickels = [s.nickel_list for s in self.curr_states]
        self.num_symmetries = len(nickels)
        self.nickel = min(nickels)
        assert min(nickels) == max(nickels), 'All nickels must be equal.'
        assert len(flatten(self.nickel)) == len(self.edges), ('Graph is not connected: %s' % (edges, ))

        # Shift back to original nodes.
        self.node_maps = []
        for state in self.curr_states:
            node_map = {}
            for key, value in state.node_map.items():
                node_map[key - offset] = value
            self.node_maps.append(node_map)

    def __str__(self):
        return Nickel(nickel=self.nickel).string

    def InitStates(self, edges):
        """Creates all possible initial states for node 0."""
        all_nodes = set(iflatten(edges))
        if LEG in all_nodes:
            boundary_nodes = set(AdjacentNodes(LEG, edges))
        else:
            boundary_nodes = all_nodes

        states = []
        for node in boundary_nodes:
            states.append(Expander(MapNodes2({node: 0}, self.edges),
                                                         [], {node: 0}, 0, 1))
        return states

    def DoExpand(self, curr_states):
        states = [list(s.Expand()) for s in curr_states]
        states = flatten(states)
        minimum = min(states)
        return [s for s in states if s == minimum]

    def GetGroupedEdges(self):
        permuts = PermutatedFromCanonical(self.node_maps)
        equal_graphs = [MapNodes2(permut, self.orig) for permut in permuts]
        equal_edges = zip(*equal_graphs)
        equal_edges = map(list, equal_edges)
        equal_edges = map(lambda x: sorted(x), equal_edges)
        Dedup(equal_edges)
        groups = [[] for _ in range(len(equal_edges))]
        for e in self.orig:
            for i in range(len(equal_edges)):
                if sorted(e) in equal_edges[i]:
                    groups[i].append(e)
        return groups


def PermutatedFromCanonical(list_of_dicts):
    dic = list_of_dicts[0]
    back_dic = dict(zip(dic.values(), dic.keys()))
    permutations = []
    for d in list_of_dicts:
        permutation = dict(zip(d.keys(), [back_dic[v] for v in d.values()]))
        permutations.append(permutation)
    return permutations


def Dedup(mylist):
    mylist.sort()
    last = mylist[-1]
    for i in range(len(mylist) - 2, -1, -1):
        if last == mylist[i]:
            del mylist[i]
        else:
            last = mylist[i]


class Expander(object):
    """A helper class for Canonicalize.

    Eats edges adjacent to already canonicalized nodes and canonicalizes them.
    """
    def __init__(self, edges, nickel_list, node_map, curr_node, free_node):
        self.edges = edges
        self.nickel_list = nickel_list    # Nested lists must be sorted.
        self.node_map = node_map
        self.curr_node = curr_node
        self.free_node = free_node

    def __cmp__(self, other):
        # Shorten the long list to not let unexpanded one win.
        min_len = min(len(self.nickel_list), len(other.nickel_list))
        return cmp(self.nickel_list[:min_len], other.nickel_list[:min_len])

    def Expand(self):
        nodes = AdjacentNodes(self.curr_node, self.edges)
        edge_rest = [e for e in self.edges if self.curr_node not in e]
        new_nodes = [n for n in nodes if n > self.free_node]
        new_nodes = list(set(new_nodes))
        free_nodes = range(self.free_node, self.free_node + len(new_nodes))
        for perm in itertools.permutations(free_nodes):
            node_map = dict(zip(new_nodes, perm))
            expanded_nodes = MapNodes1(node_map, nodes)
            edges = MapNodes2(node_map, edge_rest)
            node_map.update(self.node_map)
            yield Expander(edges, self.nickel_list + [expanded_nodes],
                           node_map, self.curr_node + 1,
                           self.free_node + len(new_nodes))


def AdjacentNodes(node, edges):
    nodes = []
    for e in edges:
        if e[0] == node:
            nodes.append(e[1])
        elif e[1] == node:
            nodes.append(e[0])
    return nodes


def IsConnected(edges):
    if not edges:
        return False

    old_len = 0
    visited_nodes = set(edges[0])
    while old_len < len(visited_nodes):
        old_len = len(visited_nodes)
        for edge in edges:
            if edge[0] in visited_nodes or edge[1] in visited_nodes:
                visited_nodes.update(edge)
    return visited_nodes == set(iflatten(edges))


def flatten(edges):
   '''flattens shallow iterable of iterables.'''
   return list(itertools.chain_from_iterables(edges))


def iflatten(edges):
   '''flattens shallow iterable of iterables.'''
   return itertools.chain_from_iterables(edges)


def MapNodes1(dic, list_of_nodes):
    return sorted([dic.get(n, n) for n in list_of_nodes])


def MapNodes2(dic, list_of_lists):
    return [MapNodes1(dic, x) for x in list_of_lists]


if __name__ == "__main__":
    pass
