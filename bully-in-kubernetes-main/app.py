from aiohttp import web
import asyncio
from asyncio import to_thread
from fortune_service import get_random_fortune
from bully_algorithm import run_bully, receive_coordinator, background_tasks, pod_id

# Create an aiohttp web app
app = web.Application()

# Handlers for API routes
async def fortune_endpoint(request):
    """Return a random fortune."""
    return web.json_response({"fortune": get_random_fortune()})

async def leader_endpoint(request):
    """Return the current leader."""
    leader_id = receive_coordinator()
    if leader_id is None:
        return web.json_response({"error": "No leader elected"}, status=503)
    return web.json_response({"leader_id": leader_id})

async def election_endpoint(request):
    """Start a leader election."""
    run_bully()
    return web.json_response({"message": "Election started"})

# Serve the HTML file
async def index(request):
    return web.FileResponse('index.html')

# Add a route for the frontend
app.router.add_get('/', index)

# Add routes to the app
app.add_routes([
    web.get('/api/fortune', fortune_endpoint),
    web.get('/api/leader', leader_endpoint),
    web.post('/api/election', election_endpoint),
    web.get('/pod_id',pod_id)
])

if __name__ == '__main__':
    app.cleanup_ctx.append(background_tasks)
    web.run_app(app, host='0.0.0.0', port=8080)
    