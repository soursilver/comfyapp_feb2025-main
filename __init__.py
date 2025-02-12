import os
from aiohttp import web
from server import PromptServer



current_dir = os.path.dirname(os.path.realpath(__file__))
web_dist = os.path.join(current_dir, "web", "dist")

@PromptServer.instance.routes.get("/myaddon")
@PromptServer.instance.routes.get("/myaddon/")
@PromptServer.instance.routes.get("/myaddon/{path:.*}")
async def serve_myaddon(request):
    path = request.match_info.get("path", "index.html")  # Default to index.html
    
    # Redirect "/myaddon" to "/myaddon/"
    if request.path == "/myaddon":
        return web.HTTPFound("/myaddon/")
    
    # Construct the full path
    full_path = os.path.join(web_dist, path)
    
    # Always serve index.html for directory requests
    if not os.path.isfile(full_path) or os.path.isdir(full_path):
        full_path = os.path.join(web_dist, "index.html")
    
    return web.FileResponse(full_path)