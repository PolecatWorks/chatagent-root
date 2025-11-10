from chatbot.tools import calcs
from chatbot.tools import customer
from langchain_mcp_adapters.client import MultiServerMCPClient

mytools = [
    calcs.sum_numbers,
    calcs.multiply_numbers,
    customer.search_records_by_name,
    customer.delete_record_by_id,
]
