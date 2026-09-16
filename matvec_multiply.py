import random
import math
from numbers import Real


def _validate_vector(vector, name):
    """Accept lists/tuples of finite real numbers, excluding booleans."""
    if not isinstance(vector, (list, tuple)):
        raise TypeError(f"{name} must be a list or tuple")
    for value in vector:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError(f"{name} must contain real numbers (not booleans)")
        # Python integers have arbitrary precision; do not convert them to float.
        if not isinstance(value, int) and not math.isfinite(value):
            raise ValueError(f"{name} must contain only finite numbers")

# create a function to compute the dot product of two vectors using a for loop
# add comments for the selected function
def dot_product(vector_a, vector_b):
    """Return the dot product of equal-length vectors; empty vectors give 0.

    Inputs must be lists or tuples of finite real numbers. Invalid types raise
    TypeError; incompatible lengths or nonfinite inputs raise ValueError.
    Floating-point overflow raises OverflowError.
    """
    _validate_vector(vector_a, 'vector_a')
    _validate_vector(vector_b, 'vector_b')
    if len(vector_a) != len(vector_b):
        raise ValueError('vectors must have equal lengths')

    total = 0
    for a, b in zip(vector_a, vector_b):
        total += a * b
        if not isinstance(total, int) and not math.isfinite(total):
            raise OverflowError('dot product exceeded finite numeric range')
    return total



# create a function to compute the matrix-vector product using the dot_product function
# add comments for the selected function
def matvec_multiply(matrix, vector):
    """Multiply a rectangular list/tuple of rows by a list/tuple vector.

    Every row must match the vector length. An empty matrix returns []; rows
    with zero columns return 0 when multiplied by an empty vector.
    Inputs are not modified. Validation errors follow dot_product's contract.
    """
    if not isinstance(matrix, (list, tuple)):
        raise TypeError('matrix must be a list or tuple of rows')
    _validate_vector(vector, 'vector')
    result = []
    for row in matrix:
        # dot_product checks row types, values, and compatible dimensions.
        result.append(dot_product(row, vector))
    return result



# create a main function to test the matrix-vector product function using randomly generated data of size 1000x1000
# add comments for the selected function
def main():
    """Demonstrate multiplication with reproducible random 1000x1000 data."""
    rng = random.Random(500)
    matrix = [[rng.random() for _ in range(1000)] for _ in range(1000)]
    vector = [rng.random() for _ in range(1000)]
    result = matvec_multiply(matrix, vector)
    print(f'Result length: {len(result)}')
    print(f'First five entries: {result[:5]}')


if __name__ == '__main__':
    main()
