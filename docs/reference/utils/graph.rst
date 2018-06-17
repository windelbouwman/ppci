
Graphs
======

The :mod:`ppci.graph` module can be used to work with graphs.

For example:

.. doctest::

    >>> from ppci.graph import Graph, Node
    >>> g = Graph()
    >>> n1 = Node(g)
    >>> n2 = Node(g)
    >>> n3 = Node(g)
    >>> len(g)
    3
    >>> g.has_edge(n1, n2)
    False
    >>> n1.add_edge(n2)
    >>> n1.add_edge(n3)
    >>> g.has_edge(n1, n2)
    True
    >>> n1.degree
    2
    >>> n2.degree
    1


Reference
---------

.. automodule:: ppci.graph.graph
    :members:

.. automodule:: ppci.graph.lt
    :members:
