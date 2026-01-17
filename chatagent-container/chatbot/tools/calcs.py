import logging

from langchain_core.tools import InjectedToolArg, tool

logger = logging.getLogger(__name__)


# sum_numbers_tool_definition = \
#         types.FunctionDeclaration(
#             name="sum_numbers",
#             description="Sums an array of numbers.",
#             parameters=types.Schema(
#                 type="object",
#                 properties={
#                     "numbers": types.Schema(
#                         type="array",
#                         items=types.Schema(type="number"),
#                         description="A list of numbers to sum."
#                     )
#                 },
#                 required=["numbers"]
#             )
#         )


@tool(parse_docstring=True)
def sum_numbers(numbers: list[float]) -> float:
    """Sums an array of numbers.

    Args:
        numbers: A list of numbers to sum.

    Returns:
        The sum of the numbers.
    """
    logger.debug(f"Summing numbers: {numbers}")
    return sum(numbers)


@tool(parse_docstring=True)
def multiply_numbers(numbers: list[float]) -> float:
    """Multiplies an array of numbers.

    Args:
        numbers: A list of numbers to multiply.

    Returns:
        The product of the numbers.
    """
    logger.debug(f"Multiplying numbers: {numbers}")
    result = 1.0
    for num in numbers:
        result *= num
    return result


# def call_external_api(endpoint: str, method: str = "GET", payload: dict = None) -> dict:
#     """Calls an external API.

#     Args:
#         endpoint: The URL endpoint of the API.
#         method: The HTTP method (e.g., "GET", "POST"). Defaults to "GET".
#         payload: A dictionary of data to send with POST/PUT requests.

#     Returns:
#         A dictionary containing the JSON response from the API.
#     """
#     import requests
#     try:
#         if method.upper() == "GET":
#             response = requests.get(endpoint)
#         elif method.upper() == "POST":
#             response = requests.post(endpoint, json=payload)
#         else:
#             raise ValueError(f"Unsupported HTTP method: {method}")
#         response.raise_for_status()  # Raise an exception for HTTP errors
#         return response.json()
#     except requests.exceptions.RequestException as e:
#         print(f"Error calling API: {e}")
#         return {"error": str(e)}
