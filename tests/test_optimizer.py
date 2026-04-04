"""测试 TSP 优化算法"""
import pytest
import sys
sys.path.insert(0, '..')

from core.optimizer import tsp_brute_force, calc_midpoint


class TestTSPSolver:
    """TSP 暴力枚举算法测试"""

    def test_no_waypoints(self):
        """无途经点时应直接返回起点→终点"""
        dist_matrix = [[0, 100], [100, 0]]
        order, cost = tsp_brute_force(dist_matrix, 0, 1, [])
        assert order == [0, 1]
        assert cost == 100

    def test_single_waypoint(self):
        """单途经点"""
        dist_matrix = [[0, 10, 20], [10, 0, 15], [20, 15, 0]]
        order, cost = tsp_brute_force(dist_matrix, 0, 2, [1])
        assert order == [0, 1, 2]
        assert cost == 10 + 15

    def test_two_waypoints_best_order(self):
        """两途经点，TSP 选出最优排列"""
        dist_matrix = [
            [0, 5, 10, 20],
            [5, 0, 8, 15],
            [10, 8, 0, 6],
            [20, 15, 6, 0],
        ]
        order, cost = tsp_brute_force(dist_matrix, 0, 3, [1, 2])
        assert cost == 19   # 0→1→2→3: 5+8+6=19（最优）
        assert order == [0, 1, 2, 3]

    def test_three_waypoints(self):
        """三途经点，枚举 3! = 6 种排列，取最优"""
        dist_matrix = [
            [0, 5, 10, 20, 30],
            [5, 0, 8, 15, 25],
            [10, 8, 0, 6, 18],
            [20, 15, 6, 0, 12],
            [30, 25, 18, 12, 0],
        ]
        order, cost = tsp_brute_force(dist_matrix, 0, 4, [1, 2, 3])
        assert cost == 31   # 0→1→2→3→4: 5+8+6+12=31（最优）
        assert order == [0, 1, 2, 3, 4]


class TestMidpoint:
    """几何中点计算测试"""

    def test_single_point(self):
        assert calc_midpoint([(116.3, 39.9)]) == (116.3, 39.9)

    def test_two_points(self):
        assert calc_midpoint([(0.0, 0.0), (10.0, 10.0)]) == (5.0, 5.0)

    def test_three_points(self):
        assert calc_midpoint([(0.0, 0.0), (6.0, 0.0), (0.0, 12.0)]) == (2.0, 4.0)

    def test_empty_list(self):
        assert calc_midpoint([]) == (0.0, 0.0)
