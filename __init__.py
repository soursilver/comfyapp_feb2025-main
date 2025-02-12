import os
from aiohttp import web
from server import PromptServer



current_dir = os.path.dirname(os.path.realpath(__file__))
web_dist = os.path.join(current_dir, "web", "dist")

@PromptServer.instance.routes.get("/myaddon")
@PromptServer.instance.routes.get("/myaddon/")
@PromptServer.instance.routes.get("/myaddon/{path:.*}")
async def serve_myaddon(request):
    path = request.match_info.get("path", "index.html")
    
    # Handle trailing slash redirect
    if request.path == "/myaddon":
        return web.HTTPFound("/myaddon/")
    
    full_path = os.path.join(web_dist, path)
    
    # Serve index.html for all non-file requests
    if not os.path.isfile(full_path):
        full_path = os.path.join(web_dist, "index.html")
    
    return web.FileResponse(full_path)

# Serve static assets
PromptServer.instance.app.add_routes([
    web.static(
        "/myaddon",
        web_dist,
        show_index=False,
        follow_symlinks=True,
        append_version=True
    )
])