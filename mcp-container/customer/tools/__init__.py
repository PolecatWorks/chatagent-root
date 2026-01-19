# Contains tools to be used by the LLM
# These include MCP provisioned tools AND local tools

from customer.config import ServiceConfig

from .mcp import connect_to_mcp_server

mytools = []



def tools_app_create(app: web.Application, config: ServiceConfig) -> web.Application:

    app.on_startup.append(connect_to_mcp_server)

    return app
