  #!/usr/bin/python
# -*- coding: utf8 -*-

import itertools
import nickel
import graph_state
import graph_state_property


if 'chain_from_iterables' not in itertools.__dict__:
    def chain_from_iterables(iterables):
        for it in iterables:
            for element in it:
                yield element

    itertools.chain_from_iterables = chain_from_iterables


class Properties(object):
    def __init__(self, from_edge, properties_config=None, **kwargs):
        assert properties_config is not None
        self._from_edge = from_edge
        self._properties_config = properties_config
        self._key = None
        for p_name in self._properties_config.property_order:
            if p_name in kwargs and properties_config.property_target[p_name] == self._from_edge:
                setattr(self, p_name, kwargs[p_name])

    @property
    def properties_config(self):
        return self._properties_config

    @staticmethod
    def from_kwargs(from_edge=True, **kwargs):
        properties_config = kwargs.get('properties_config', None)
        if properties_config is None:
            return None
        p = Properties(from_edge, properties_config)
        for p_name, to_edge in properties_config.property_target.items():
            if to_edge != from_edge:
                continue
            setattr(p, p_name, kwargs.get(p_name, None))
        return p

    def is_none(self):
        return len(self._properties_config) == 0

    def has_property(self, name, from_edge=True):
        return self._properties_config.has_property(name, from_edge=from_edge)

    def make_external(self, nodes, external_node):
        external_prop = Properties(from_edge=True, properties_config=self._properties_config)
        for p_name in self._properties_config.property_order:
            v = getattr(self, p_name, None)
            if Edge.MAKE_PROPERTY_EXTERNAL_METHOD_NAME in v.__class__.__dict__:
                v = v.make_external(nodes, external_node)
            setattr(external_prop, p_name, v)
        return external_prop

    def key(self):
        if self._key is None:
            raw_key = list()
            for p_name in self._properties_config.property_order:
                v = getattr(self, p_name, None)
                raw_key.append(v)
            self._key = tuple(raw_key)
        return self._key

    def update(self, from_edge=True, **kwargs):
        p = Properties(from_edge, self._properties_config)
        for p_name, to_edge in self._properties_config.property_target.items():
            if to_edge != from_edge:
                continue
            if p_name not in kwargs:
                value = getattr(self, p_name, None)
            else:
                value = kwargs[p_name]
            setattr(p, p_name, value)
        return p

    def __neg__(self):
        neg_prop = Properties(self._from_edge, properties_config=self._properties_config)
        for p_name in self._properties_config.property_order:
            self_v = getattr(self, p_name, None)
            if self_v is None:
                neg_v = None
            else:
                directed = self._properties_config.is_directed(p_name)
                neg_v = -self_v if directed else self_v
            setattr(neg_prop, p_name, neg_v)
        return neg_prop

    # noinspection PyProtectedMember
    def __cmp__(self, other):
        if isinstance(other, Properties):
            assert self._properties_config is other._properties_config, 'configs must be same to compare'
            property_order = self._properties_config.property_order
            for i in xrange(len(property_order)):
                p_name = property_order[i]
                self_v = getattr(self, p_name, None)
                other_v = getattr(other, p_name, None)
                if self_v is None:
                    if other_v is None:
                        continue
                    else:
                        return -1
                if other_v is None:
                    return 1
                cmp_res = cmp(self_v, other_v)
                if cmp_res:
                    return cmp_res
        raise AssertionError()

    @staticmethod
    def cmp_by_index(p1, p2, index):
        assert isinstance(p1, Properties), ('unexpected type %s' % type(p1))
        assert isinstance(p2, Properties), ('unexpected type %s' % type(p2))
        assert p1._properties_config is p2._properties_config, 'configs must be same to compare'
        property_order = p1._properties_config.property_order
        p_name = property_order[index]
        p1_v = getattr(p1, p_name, None)
        p2_v = getattr(p2, p_name, None)
        if p1_v is None:
            return 0 if p2_v is None else -1
        if p2_v is None:
            return 1
        return cmp(p1_v, p2_v)

    def __len__(self):
        return len(filter(lambda to_edge: to_edge == self._from_edge, self._properties_config.property_target.values()))

    def __repr__(self):
        property_order = self._properties_config.property_order
        builder = list()
        for i in xrange(len(property_order)):
            p_name = property_order[i]
            if self._from_edge == self._properties_config.property_target[p_name]:
                self_v = getattr(self, p_name, None)
                builder.append('%s=%s' % (p_name, self_v))
        return ', '.join(builder)

    __str__ = __repr__


class PropertiesConfig(object):
    """
    Base factory class to produce :class:`GraphState`, :class:`Edge` or :class:`Node` objects. Creation of all new instances must
    be done using this class. Don't use constructors of these classes directly.
    """
    def __init__(self, property_order, property_directionality, property_externalizer, property_target):
        self._property_order = property_order
        self._property_directionality = property_directionality
        self._property_externalizer = property_externalizer
        self._property_target = property_target

    @staticmethod
    def create(*property_keys):
        """
        :param property_keys: property keys define properties behaviour. See :class:`graph_state_property.PropertyKey`.
        :return: properties config created for given keys
        """
        property_order = [None] * len(property_keys)
        property_directionality = dict()
        property_externalizer = dict()
        property_target = dict()
        for i, k in enumerate(property_keys):
            property_order[i] = k.name
            property_directionality[k.name] = k.is_directed
            property_externalizer[k.name] = k.externalizer
            property_target[k.name] = k.is_edge_property
        return PropertiesConfig(property_order, property_directionality, property_externalizer, property_target)

    def new_node(self, node_index, **kwargs):
        """
        creates new node with this config with specified node_index and specified node properties in **kwargs.
        """
        kwargs['properties_config'] = self
        return graph_state_property.Node(node_index, Properties.from_kwargs(from_edge=False, **kwargs))

    def new_edge(self, nodes, external_node=-1, edge_id=None, **kwargs):
        """
        :param nodes: pair of nodes defines edge
        :type nodes: tuple
        :param external_node: external node index
        :type external_node: int or :class:`Node`
        :param edge_id: unique edge id, if not given then assigned automatically
        :type edge_id: int
        :param **kwargs: properties of edge and properties config
        :return: new edge represented as :class:`Edge` object
        """
        kwargs['properties_config'] = self
        return graph_state.Edge(nodes, external_node, edge_id, **kwargs)

    @classmethod
    def new_graph_state(cls, edges):
        """
        :return: :class:`GraphState` object from given edges and properties config held by these edges.
        """
        return GraphState(edges)

    def graph_state_from_str(self, string):
        """
        :return: :class:`GraphState` object for given serialized string corresponding to properties config.
        """
        return graph_state.GraphState.from_str(string, properties_config=self)

    def new_properties(self, **kwargs):
        return Properties(self, **kwargs)

    @property
    def property_order(self):
        return self._property_order

    @property
    def property_target(self):
        return self._property_target

    def externalizer(self, p_name):
        return self._property_externalizer[p_name]

    def properties_count(self):
        return len(self._property_order)

    def is_directed(self, property_name):
        return self._property_directionality[property_name]

    def has_property(self, property_name, from_edge=True):
        return self._property_target.get(property_name, None) is from_edge

    def __len__(self):
        return len(self._property_order)

    def __str__(self):
        return "PropertiesConfig(%s)" % self.property_order

    __repr__ = __str__


DEFAULT_PROPERTIES_CONFIG = PropertiesConfig.create()


class Edge(graph_state_property.PropertyGetAttrTrait):
    """
    Representation of an edge of a graph. Edge could have directed or undirected properties defined by :class:`PropertiesConfig`.
    """

    #if this attribute is True than any new Edge will be generated with unique edge_id
    CREATE_EDGES_INDEX = True
    NEXT_EDGES_INDEX = 1
    MAKE_PROPERTY_EXTERNAL_METHOD_NAME = 'make_external'

    def __init__(self, nodes, external_node=-1, edge_id=None, **kwargs):
        """
        warning:: Do not use directly. use PropertiesConfig#new_edge instead this

        :param nodes: pair of nodes defines edge
        :type nodes: tuple
        :param external_node: Current state to be in.
        :type external_node: int or :class:`Node`
        :param edge_id: unique edge id, if not given then assigned automated
        :type int
        :param **kwargs: properties of edge and properties config
        """
        properties = kwargs.get('properties', None)
        if properties is None:
            if 'properties_config' not in kwargs:
                kwargs['properties_config'] = DEFAULT_PROPERTIES_CONFIG
            properties = Properties.from_kwargs(from_edge=True, **kwargs)

        super(Edge, self).__init__()
        self._nodes = graph_state_property.Node.build_if_need(nodes, Properties.from_kwargs(from_edge=False,
                                                                                            properties_config=properties.properties_config))
        self.internal_nodes = tuple([node for node in self.nodes if node != external_node])
        self.external_node = external_node

        if properties is not None and self.is_external():
            properties = properties.make_external(nodes, external_node)
        swap = (nodes[0] > nodes[1])
        self._properties = properties if not swap or properties is None else -properties
        if edge_id is not None:
            self.edge_id = edge_id
        else:
            if Edge.CREATE_EDGES_INDEX:
                self.edge_id = Edge.NEXT_EDGES_INDEX
                Edge.NEXT_EDGES_INDEX += 1
            else:
                self.edge_id = None

    def is_external(self):
        """
        :return: if edge is external (has external node)
        """
        return len(self.internal_nodes) == 1

    @property
    def internal_node(self):
        assert self.is_external()
        return self.internal_nodes[0]

    @property
    def nodes(self):
        """
        :return: nodes of edge
        """
        return self._nodes

    def co_node(self, node):
        """
        :return: node that complements node given by parameter
        """
        for n in self.nodes:
            if n != node:
                return n

    def get_attr_regard_to(self, node, attr_name):
        attr_value = self.__getattr__(attr_name)
        if attr_value is None:
            return None
        if node == self.nodes[0]:
            return attr_value
        elif node == self.nodes[1]:
            return - attr_value
        raise ValueError("invalid node = %s" % node)

    def key(self):
        if '_key' not in self.__dict__:
            # noinspection PyAttributeOutsideInit
            self._key = (tuple(map(lambda n: n.index, self.internal_nodes)),)
            if self._properties:
                self._key += self._properties.key()
            self._key = reduce(lambda k, n: k + n.key(), self.nodes, self._key)
        return self._key

    def __repr__(self):
        return '(%s, %s)' % (self.internal_nodes, str(self._properties))

    __str__ = __repr__

    def __cmp__(self, other):
        return cmp(self.key(), other.key())

    def __hash__(self):
        if '_hash' not in self.__dict__:
            #noinspection PyAttributeOutsideInit
            self._hash = hash(self.key())
        return self._hash

    def cut_tadpole(self):
        nodes_set = set(self.nodes)
        assert len(nodes_set) == 1 and not self.is_external()
        node = nodes_set.pop()
        nodes1 = (node, self.external_node)
        nodes2 = (self.external_node, node)
        return tuple(map(lambda n: Edge(n,
                                        external_node=self.external_node,
                                        properties=self._properties.make_external(n,
                                                                                  self.external_node)), (nodes1,
                                                                                                         nodes2)))

    def copy(self, node_map=None, **kwargs):
        """
        Creates a copy of the object with possible change of nodes and possible change of properties.

        :param node_map: dictionary mapping old nodes to new ones. Identity map is assumed for the missed keys.
        :param **kwargs: properties that must be replaced for edge copy
        :return: new :class:`Edge` constructed by given rules.
        """
        node_map = node_map or {}

        mapped_nodes = map(lambda node: node.copy(new_node=node_map[node]) if node in node_map else node, self.nodes)

        mapped_external_node = node_map.get(self.external_node, self.external_node)

        properties_is_none = self._properties.is_none()
        updated_properties = None if properties_is_none else self._properties.update(from_edge=True, **kwargs)
        if updated_properties is None:
            if 'properties_config' not in kwargs:
                kwargs['properties_config'] = DEFAULT_PROPERTIES_CONFIG
            updated_properties = Properties.from_kwargs(from_edge=True, **kwargs)

        if mapped_external_node in mapped_nodes:
            updated_properties = updated_properties.make_external(mapped_nodes, mapped_external_node)
        return Edge(mapped_nodes,
                    external_node=mapped_external_node,
                    properties=updated_properties)

    @staticmethod
    def cmp_by_property_index(e1, e2, index):
        config = e1._properties.properties_config
        if config.property_target[config.property_order[index]]:
            return Properties.cmp_by_index(e1._properties, e2._properties, index)
        else:
            for n1, n2 in zip(e1.nodes, e2.nodes):
                c = Properties.cmp_by_index(n1._properties, n2._properties, index)
                if c != 0:
                    return c
        return 0


# noinspection PyProtectedMember
class GraphState(object):
    """
    Don't use constructor to create instances directly. Use :meth:`PropertiesConfig.graph_state_from_str` or
    :meth:`PropertiesConfig.new_graph_state`.

    To access of isomorphisms group of graph call ``graph_state.obj.sortings``. It returns all possible isomorphic graphs
    represented as list of edges.

    >>> GraphState.from_str("e11|e|", config).sortings
    [(((0,), ), ((0, 1), ), ((0, 1), ), ((1,), )), (((0,), ), ((0, 1), ), ((0, 1), ), ((1,), ))]

    Nodes and edges of graph can be obtained by corresponding properties access: :attr:`GraphState.edges` (or iterating
    over object) and :attr:`GraphState.nodes`:

    >>> gs = GraphState.from_str("e11|e|", config)
    >>> gs.edges
    (((0,), ), ((0, 1), ), ((0, 1), ), ((1,), ))
    >>> [e for e in gs]
    [((0,), ), ((0, 1), ), ((0, 1), ), ((1,), )]
    >>> gs.nodes
    [-1, 0, 1]

    graph state can be serialized to Nickel string using :func:`str()` function:

    >>> str(gs)
    "e11|e|"

    """
    SEP = ':'
    SEP2 = '_'
    NICKEL_SEP = nickel.Nickel.SEP

    def __init__(self, edges, node_maps=None):
        properties_count = len([edge._properties for edge in edges if edge._properties])
        assert properties_count == 0 or properties_count == len(edges), \
            ('properties_count =  %s, len(edges) = %s' % (properties_count, len(edges)))

        self._properties_config = None if edges[0]._properties is None else edges[0]._properties._properties_config
        node_maps = (node_maps or nickel.Canonicalize([map(lambda n: n.index, edge.nodes) for edge in edges]).node_maps)
        self.sortings = []
        for node_map in node_maps:
            mapped_edges = list()
            for edge in edges:
                props = edge._properties
                mapped_edges.append(edge.copy(node_map=node_map, properties=props))
            mapped_edges.sort()
            self.sortings.append(tuple(mapped_edges))

        for index in xrange(len(self._properties_config)):
            if len(self.sortings) == 1:
                break
            cmp_ = lambda e1, e2: Edge.cmp_by_property_index(e1, e2, index)
            self.sortings = GraphState._find_min_elements_(self.sortings, cmp_)

    @property
    def edges(self):
        """
        Returns ordered with Nickel order edges which represents corresponding GraphState.
        """
        return self.sortings[0]

    @property
    def nodes(self):
        """
        Returns all internal unique nodes in Nickel order.
        """
        return sorted(reduce(lambda s, e: s | set(e.nodes), self.edges, set()))

    def __cmp__(self, other):
        return cmp(self.sortings[0], other.sortings[0])

    def __hash__(self):
        return hash(self.sortings[0])

    def __len__(self):
        return len(self.edges)

    def __iter__(self):
        return iter(self.edges)

    def __str__(self):
        nickel_edges = [map(lambda n: n.index, edge.nodes) for edge in self.edges]
        edges_str = nickel.Nickel(edges=nickel_edges).string

        serialized = [edges_str]

        reduced_nodes = None
        if self._properties_config is not None:
            for p_name in self._properties_config.property_order:
                externalizer = self._properties_config.externalizer(p_name)
                if self._properties_config.property_target[p_name]:
                    is_all_attrs_none = reduce(lambda b, edge: b and getattr(edge, p_name) is None, self.sortings[0], True)
                    if is_all_attrs_none:
                        serialized.append('')
                        continue
                    prop_chars = [externalizer.serialize((getattr(edge, p_name))) for edge in self.sortings[0]]
                    prop_chars_iter = iter(prop_chars)
                    # edge string.
                    prop_chars_with_sep = []
                    for char in edges_str:
                        if char == self.NICKEL_SEP:
                            prop_chars_with_sep.append(self.NICKEL_SEP)
                        else:
                            if len(prop_chars_with_sep) and prop_chars_with_sep[-1] != self.NICKEL_SEP:
                                prop_chars_with_sep.append(self.SEP2)
                            prop_chars_with_sep.append(prop_chars_iter.next())
                    serialized.append(''.join(prop_chars_with_sep))
                else:
                    if not reduced_nodes:
                        reduced_nodes = filter(lambda n: n != self.edges[0].external_node, self.nodes)
                    is_all_none = True
                    values = list()
                    for n in reduced_nodes:
                        v = getattr(n, p_name)
                        values.append(str(v))
                        if v is not None:
                            is_all_none = False
                    serialized.append('' if is_all_none else GraphState.NICKEL_SEP.join(values))

        return self.SEP.join(serialized)

    __repr__ = __str__

    def topology_str(self):
        base_str = str(self)
        if ':' in base_str:
            base_str = base_str[:base_str.index(':')]
        return base_str

    @staticmethod
    def from_str(string, properties_config=None):
        """
        Creates :class:`graph_state.GraphState` object from Nickel serialized string. See :meth:`PropertiesConfig.graph_state_from_str`.
        """
        if properties_config is None:
            properties_config = DEFAULT_PROPERTIES_CONFIG
        parts_count = 1 + properties_config.properties_count()
        splitted_string = string.split(GraphState.SEP, parts_count)
        splitted_len = len(splitted_string)
        empty_properties = splitted_len == 1
        assert empty_properties or splitted_len == parts_count

        nickel_edges = nickel.Nickel(string=splitted_string[0]).edges

        if not empty_properties:
            raw_properties = splitted_string[1:]
            un_transposed_properties = dict()
            un_transposed_nodes_properties = dict()
            not_none_node_properties = None
            for (r_property_line, p_name) in itertools.izip(raw_properties, properties_config.property_order):
                if properties_config.property_target[p_name]:
                    if r_property_line != '':
                        r_properties = reduce(lambda _list, line: _list + line.split(GraphState.SEP2), r_property_line.split(nickel.Nickel.SEP),
                                              list())[:-1]
                        r_properties = filter(lambda p: len(p), r_properties)
                        externalizer = properties_config.externalizer(p_name)
                        un_transposed_properties[p_name] = map(lambda raw_prop: externalizer.deserialize(raw_prop), r_properties)
                    else:
                        un_transposed_properties[p_name] = [None] * len(nickel_edges)
                else:
                    if r_property_line != '':
                        r_properties = r_property_line.split(GraphState.NICKEL_SEP)
                        externalizer = properties_config.externalizer(p_name)
                        un_transposed_nodes_properties[p_name] = map(lambda raw_prop: externalizer.deserialize(raw_prop), r_properties)
                        if not not_none_node_properties:
                            not_none_node_properties = p_name
                    else:
                        un_transposed_nodes_properties[p_name] = None
            transposed_properties = list()
            for i in xrange(len(nickel_edges)):
                transposed_properties.append(dict({'properties_config': properties_config}))
            for (p_name, properties) in un_transposed_properties.iteritems():
                for p, m in itertools.izip(properties, transposed_properties):
                    m[p_name] = p

            if not_none_node_properties:
                nodes_transposed_properties = list()
                for i in xrange(len(un_transposed_nodes_properties[not_none_node_properties])):
                    nodes_transposed_properties.append(dict({'properties_config': properties_config}))
                for (p_name, properties) in un_transposed_nodes_properties.iteritems():
                    if properties is not None:
                        for p, m in itertools.izip(properties, nodes_transposed_properties):
                            m[p_name] = p
            else:
                nodes_transposed_properties = None
        else:
            transposed_properties = [None] * len(nickel_edges)
            nodes_transposed_properties = None

        edges = []
        nodes_mapper = GraphState._id_nodes_mapper if nodes_transposed_properties is None else GraphState._with_properties_node_mapper
        for nodes, props in itertools.izip(nickel_edges, transposed_properties):
            nodes = nodes_mapper(nodes, nodes_transposed_properties, properties_config)
            edges.append(Edge(nodes, properties_config=properties_config) if props is None else Edge(nodes, **props))
        assert len(edges) == len(nickel_edges)

        return GraphState(edges)

    # noinspection PyUnusedLocal
    @staticmethod
    def _id_nodes_mapper(nodes, nodes_properties, properties_config):
        return nodes

    @staticmethod
    def _with_properties_node_mapper(nodes, nodes_properties, properties_config):
        return tuple(map(lambda n: graph_state_property.Node(n, Properties.from_kwargs(False, **nodes_properties[n])
                                                                           if n != nickel.LEG
                                                                           else Properties.from_kwargs(False, properties_config=properties_config)), nodes))

    @staticmethod
    def _find_min_elements_(lists_of_edges, cmp_):
        _min = list()
        for edges in lists_of_edges:
            if not len(_min):
                _min.append(edges)
            else:
                current_min_edges = _min[0]
                new_edges_is_new_min = False
                is_equal = True
                for e_c, e_m in itertools.izip(edges, current_min_edges):
                    r = cmp_(e_c, e_m)
                    if r < 0:
                        new_edges_is_new_min = True
                        break
                    elif r > 0:
                        is_equal = False
                        break
                if new_edges_is_new_min:
                    _min = [edges]
                elif is_equal:
                    _min.append(edges)
        return _min