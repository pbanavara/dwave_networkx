import unittest
import itertools

import dwave_networkx as dnx
from dwave_networkx.algorithms.tests.solver import Sampler, sampler_found
from dwave_networkx.algorithms.coloring_dw import _quadratic_chi_bound
from dwave_networkx.algorithms.coloring_dw import _vertex_different_colors_qubo
from dwave_networkx.algorithms.coloring_dw import _vertex_one_color_qubo
from dwave_networkx.algorithms.coloring_dw import _minimum_coloring_qubo


class TestColor(unittest.TestCase):
    def test__quadratic_chi_bound(self):
        """Make sure that the quadratic formula is run correctly.
        we want chi*(chi - 1) <= n_edges * 2
        so chi_ub * (chi_ub - 1) >= n_edges * 2
        """
        for n_edges in range(100):
            chi_ub = _quadratic_chi_bound(n_edges)
            self.assertGreaterEqual(chi_ub * (chi_ub - 1), n_edges * 2)

    def test__vertex_different_colors_qubo(self):
        # Chimera tile (can be 2-colored)
        G = dnx.chimera_graph(1, 1, 4)
        counter = itertools.count()
        x_vars = {v: {0: next(counter), 1: next(counter)} for v in G}

        # get the QUBO
        Q = _vertex_different_colors_qubo(G, x_vars)

        # this thing should have energy 0 when each node is a different color
        bicolor = {v: 0 for v in range(4)}
        bicolor.update({v: 1 for v in range(4, 8)})

        # make the sample from the bicolor
        sample = {}
        for v in G:
            if bicolor[v] == 0:
                sample[x_vars[v][0]] = 1
                sample[x_vars[v][1]] = 0
            else:
                sample[x_vars[v][0]] = 0
                sample[x_vars[v][1]] = 1

        self.assertEqual(qubo_energy(Q, sample), 0)

    def test__vertex_one_color_qubo(self):
        G = dnx.chimera_graph(2, 2, 4)
        counter = itertools.count()
        x_vars = {v: {0: next(counter), 1: next(counter)} for v in G}

        # get the QUBO
        Q = _vertex_one_color_qubo(x_vars)

        # assign each variable a single color
        sample = {}
        for v in G:
            sample[x_vars[v][0]] = 1
            sample[x_vars[v][1]] = 0

        self.assertEqual(qubo_energy(Q, sample), -1 * len(G))

    def test__minimum_coloring_qubo(self):
        # Chimera tile (can be 2-colored)
        G = dnx.chimera_graph(1, 1, 4)
        chi_ub = 5
        chi_lb = 2
        possible_colors = {v: set(range(chi_ub)) for v in G}

        counter = itertools.count()
        x_vars = {v: {c: next(counter) for c in possible_colors[v]} for v in G}

        # get the QUBO
        Q = _minimum_coloring_qubo(x_vars, chi_lb, chi_ub)

        # TODO: actually test something other than it running

    def test_vertex_color_basic(self):
        G = dnx.chimera_graph(1, 2, 2)
        coloring = dnx.min_vertex_coloring_dm(G, Sampler())
        self.assertTrue(dnx.is_vertex_coloring(G, coloring))

        G = dnx.path_graph(5)
        coloring = dnx.min_vertex_coloring_dm(G, Sampler())
        self.assertTrue(dnx.is_vertex_coloring(G, coloring))

        for __ in range(10):
            G = dnx.gnp_random_graph(5, .5)
            coloring = dnx.min_vertex_coloring_dm(G, Sampler())
            self.assertTrue(dnx.is_vertex_coloring(G, coloring))

    def test_vertex_color_complete_graph(self):
        G = dnx.complete_graph(101)
        coloring = dnx.min_vertex_coloring_dm(G, Sampler())
        self.assertTrue(dnx.is_vertex_coloring(G, coloring))

    def test_vertex_color_odd_cycle_graph(self):
        """Graph that is an odd circle"""
        G = dnx.cycle_graph(11)
        coloring = dnx.min_vertex_coloring_dm(G, Sampler())
        self.assertTrue(dnx.is_vertex_coloring(G, coloring))

    def test_vertex_color_no_edge_graph(self):
        """Graph with many nodes but no edges, should be caught before QUBO"""
        G = dnx.Graph()
        G.add_nodes_from(range(100))
        coloring = dnx.min_vertex_coloring_dm(G, Sampler())
        self.assertTrue(dnx.is_vertex_coloring(G, coloring))

    def test_vertex_color_random_graph(self):

        G = dnx.gnp_random_graph(4, .3)
        mapping = dict(zip(G.nodes(), "abcdefghijklmnopqrstuvwxyz"))
        G = dnx.relabel_nodes(G, mapping)
        coloring = dnx.min_vertex_coloring_dm(G, Sampler())
        self.assertTrue(dnx.is_vertex_coloring(G, coloring))

    def test_vertex_color_almost_complete(self):

        G = dnx.complete_graph(10)
        mapping = dict(zip(G.nodes(), "abcdefghijklmnopqrstuvwxyz"))
        G = dnx.relabel_nodes(G, mapping)
        n0, n1 = next(G.edges_iter())
        G.remove_edge(n0, n1)
        coloring = dnx.min_vertex_coloring_dm(G, Sampler())
        self.assertTrue(dnx.is_vertex_coloring(G, coloring))


def qubo_energy(Q, sample):
    """Calculate the quadratic polynomial value of the given sample
    to a quadratic unconstrained binary optimization (QUBO) problem.
    """
    energy = 0

    for v0, v1 in Q:
        energy += sample[v0] * sample[v1] * Q[(v0, v1)]

    return energy
