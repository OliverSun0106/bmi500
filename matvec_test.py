# generate tests for matrix-vector-product function in matvec_multiply.py

# generate tests for dot-product function in matvec_multiply.py
import unittest

from matvec_multiply import dot_product, matvec_multiply


class DotProductTests(unittest.TestCase):
    def test_known_values(self):
        self.assertEqual(dot_product([1, -2, 3], [4, 5, 6]), 12)
        self.assertAlmostEqual(dot_product((0.1, 0.2), (0.3, 0.4)), 0.11)

    def test_empty_and_zero(self):
        self.assertEqual(dot_product([], []), 0)
        self.assertEqual(dot_product([0, 0], [7, -8]), 0)

    def test_mismatched_lengths(self):
        for a, b in [([1], []), ([], [1]), ([1, 2], [3])]:
            with self.subTest(a=a, b=b), self.assertRaises(ValueError):
                dot_product(a, b)

    def test_invalid_inputs_on_either_side(self):
        for invalid in [None, '1', 1, [True], ['1'], [1j], [[1]]]:
            for a, b in [(invalid, [1]), ([1], invalid)]:
                with self.subTest(a=a, b=b), self.assertRaises(TypeError):
                    dot_product(a, b)

    def test_nonfinite_values(self):
        for value in [float('nan'), float('inf'), -float('inf')]:
            for a, b in [([value], [1]), ([1], [value])]:
                with self.subTest(a=a, b=b), self.assertRaises(ValueError):
                    dot_product(a, b)

    def test_overflow(self):
        for a, b in [([1e308], [2.0]), ([1e308, 1e308], [1.0, 1.0])]:
            with self.subTest(a=a, b=b), self.assertRaises(OverflowError):
                dot_product(a, b)

    def test_large_integers_remain_exact(self):
        self.assertEqual(dot_product([10**400], [2]), 2 * 10**400)


class MatrixVectorTests(unittest.TestCase):
    def test_rectangular_matrix(self):
        self.assertEqual(matvec_multiply([[1, 2, 3], [-1, 0, 4]], [2, -1, 3]), [9, 10])

    def test_identity_and_tuple_inputs(self):
        self.assertEqual(matvec_multiply(((1, 0), (0, 1)), (3, -4)), [3, -4])

    def test_empty_dimensions(self):
        self.assertEqual(matvec_multiply([], []), [])
        self.assertEqual(matvec_multiply([], [1]), [])
        self.assertEqual(matvec_multiply([[], []], []), [0, 0])

    def test_bad_dimensions(self):
        for matrix in [[[1, 2]], [[1], [2, 3]], [[]]]:
            with self.subTest(matrix=matrix), self.assertRaises(ValueError):
                matvec_multiply(matrix, [1])

    def test_invalid_matrix_or_rows(self):
        for matrix in [None, '1', [1], [[True]], [['1']]]:
            with self.subTest(matrix=matrix), self.assertRaises(TypeError):
                matvec_multiply(matrix, [1])

    def test_invalid_vector_even_with_empty_matrix(self):
        with self.assertRaises(TypeError):
            matvec_multiply([], None)
        with self.assertRaises(ValueError):
            matvec_multiply([], [float('nan')])

    def test_nonfinite_row_and_overflow(self):
        with self.assertRaises(ValueError):
            matvec_multiply([[float('inf')]], [1])
        with self.assertRaises(OverflowError):
            matvec_multiply([[1e308]], [2.0])

    def test_inputs_unchanged(self):
        matrix, vector = [[1, 2], [3, 4]], [5, 6]
        matvec_multiply(matrix, vector)
        self.assertEqual(matrix, [[1, 2], [3, 4]])
        self.assertEqual(vector, [5, 6])


if __name__ == '__main__':
    unittest.main()

