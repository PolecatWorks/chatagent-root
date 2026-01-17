import aiohttp


config = aiohttp.web.AppKey("config")
metrics = aiohttp.web.AppKey("metrics")
hams = aiohttp.web.AppKey("hams")
events = aiohttp.web.AppKey("events")
coroutine = aiohttp.web.AppKey("coroutine")
webservice = aiohttp.web.AppKey("webservice")

storage = aiohttp.web.AppKey("storage")
cloud_adapter = aiohttp.web.AppKey("cloud_adapter")
agent_app = aiohttp.web.AppKey("agent_app")


# botsettings = aiohttp.web.AppKey("botsettings")
# botadapter = aiohttp.web.AppKey("botadapter")
# bot = aiohttp.web.AppKey("bot")

# The key for the Gemini service, used to store and retrieve Gemini-related data
# and configurations in the aiohttp application context.
langgraph_handler = aiohttp.web.AppKey("langgraph_handler")

mcpobjects = aiohttp.web.AppKey("mcptools")
