import pytest
from chatbot.tools.calcs import sum_numbers, multiply_numbers


def test_sum_numbers():
    # Test with positive numbers
    assert sum_numbers.invoke({"numbers": [1, 2, 3]}) == 6

    # Test with negative numbers
    assert sum_numbers.invoke({"numbers": [-1, -2, -3]}) == -6

    # Test with mixed numbers
    assert sum_numbers.invoke({"numbers": [1.5, -2.5, 3]}) == 2

    # Test with empty list
    assert sum_numbers.invoke({"numbers": []}) == 0


def test_multiply_numbers():
    # Test with positive numbers
    assert multiply_numbers.invoke({"numbers": [2, 3, 4]}) == 24

    # Test with negative numbers
    assert multiply_numbers.invoke({"numbers": [-2, 3]}) == -6

    # Test with decimals
    assert multiply_numbers.invoke({"numbers": [1.5, 2]}) == 3.0

    # Test with single number
    assert multiply_numbers.invoke({"numbers": [5]}) == 5.0

    # Test with empty list
    assert multiply_numbers.invoke({"numbers": []}) == 1.0
