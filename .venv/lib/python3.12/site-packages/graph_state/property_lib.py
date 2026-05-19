#!/usr/bin/python
# -*- coding: utf8
"""
library provides some useful primitive classes which can be used as edges/nodes properties
"""
__author__ = 'dima'

import graph_state_property
import graph_state


class Fields(object):
    """
    represents directed 2-letters word: "aA" <-> "Aa"
    """
    EXTERNAL = '0'
    STR_LEN = 2

    class Externalizer(graph_state_property.PropertyExternalizer):
        def deserialize(self, string):
            return Fields.from_str(string)

    def __init__(self, pair):
        assert len(str(pair[0])) == 1
        assert len(str(pair[1])) == 1
        self._pair = str(pair[0]), str(pair[1])

    def make_external(self, nodes, external_node):
        if external_node == nodes[0]:
            return Fields((Fields.EXTERNAL, self.pair[1]))
        else:
            return Fields((self.pair[0], Fields.EXTERNAL))

    def is_one_way(self):
        return Fields.EXTERNAL in self._pair

    @property
    def pair(self):
        return self._pair

    def __neg__(self):
        return Fields((self.pair[1], self.pair[0]))

    def __cmp__(self, other):
        return cmp(self.pair, other.pair)

    def __hash__(self):
        return hash(self.pair)

    def copy(self, swap=False):
        if swap:
            return Fields(tuple(reversed(self.pair)))
        return Fields(self.pair)

    def __str__(self):
        return self.pair[0] + self.pair[1]

    def __repr__(self):
        return str(self)

    def __getitem__(self, item):
        return self._pair[item]

    @staticmethod
    def externalizer():
        return Fields.Externalizer()

    @staticmethod
    def from_str(string):
        return Fields(string)

    @staticmethod
    def fieldsToStr(seq):
        return ''.join([str(fields) for fields in seq])

    @staticmethod
    def fieldsFromStr(string):
        return [Fields.from_str(string[i: i + Fields.STR_LEN])
                for i in range(0, len(string), Fields.STR_LEN)]


class Rainbow(object):
    """
    Class of sequences assigned to the edge.
    Stores all input attributes as tuple ex:
        colors: [1,2] self._colors: (1,2)
        colors: 1     self._colors: (1,)
    """

    class Externalizer(graph_state_property.PropertyExternalizer):
        def deserialize(self, string):
            return Rainbow.fromObject(string)

    def __init__(self, colors):
        if isinstance(colors, Rainbow):
            self._colors = colors.colors
        else:
            self._colors = tuple(colors) if isinstance(colors, (list, set, tuple)) else (colors, )

    @property
    def colors(self):
        """
        main method to access data from colors
        """
        return self._colors

    # noinspection PyUnusedLocal
    def make_external(self, nodes, external_node):
        return self

    def __getitem__(self, item):
        return self._colors[item]

    def __cmp__(self, other):
        if isinstance(other, tuple):
            return cmp(self.colors, other)
        return cmp(self.colors, other.colors)

    def __len__(self):
        return len(self.colors)

    def __hash__(self):
        return hash(self.colors)

    def __str__(self):
        return str(self.colors)

    def __repr__(self):
        return str(self)

    def __add__(self, other):
        if isinstance(other, Rainbow):
            return Rainbow(self.colors + other.colors)
        raise AssertionError()

    @staticmethod
    def externalizer():
        return Rainbow.Externalizer()

    @staticmethod
    def fromObject(obj):
        if obj is None:
            return None
        elif isinstance(obj, str):
            return Rainbow(eval(obj))
        else:
            return Rainbow(obj)


class Arrow(object):
    """
    direction class, can be on of three types "<", ">", "0"
    """
    LEFT_ARROW = "<"
    RIGHT_ARROW = ">"
    NULL = "0"

    _VALUES = set((LEFT_ARROW, RIGHT_ARROW, NULL))

    class Externalizer(graph_state_property.PropertyExternalizer):
        def deserialize(self, string):
            return Arrow(string)

    def __init__(self, value):
        assert value in Arrow._VALUES, value
        self._value = value

    @property
    def value(self):
        return self._value

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def make_external(self, nodes, external_node):
        return Arrow(Arrow.NULL)

    def is_null(self):
        return self.value == Arrow.NULL

    def is_left(self):
        return self.value == Arrow.LEFT_ARROW

    def as_numeric(self):
        if self.is_null():
            return 0
        return 1 if self.is_left() else -1

    def __cmp__(self, other):
        return cmp(self.value, other.value)

    def __neg__(self):
        if self.is_null():
            return self
        return Arrow(Arrow.RIGHT_ARROW) if self.is_left() else Arrow(Arrow.LEFT_ARROW)

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        return self.value == other.value

    def __str__(self):
        return str(self.value)

    __repr__ = __str__


class StringExternalizer(graph_state_property.PropertyExternalizer):
    def deserialize(self, string):
        return None if string == str(None) else string


EMPTY_CONFIG = graph_state.PropertiesConfig.create()


COLORS_AND_FIELDS_CONFIG = \
    graph_state.PropertiesConfig.create(graph_state_property.PropertyKey(name="colors",
                                                                         is_directed=False,
                                                                         externalizer=Rainbow.Externalizer()),
                                        graph_state_property.PropertyKey(name="fields",
                                                                         is_directed=True,
                                                                         externalizer=Fields.Externalizer()))
