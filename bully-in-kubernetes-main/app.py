import asyncio
from aiohttp import web
from bully_algorithm import start_election, get_leader

# Create the aiohttp web app
app = web.Application()

# Handlers for API routes
async def fortune_endpoint(request):
    """Return a random fortune."""
    return web.json_response({"fortune": "You will have a great day!"})

async def leader_endpoint(request):
    """Return the current leader."""
    leader_id = await get_leader()  # Get the current leader
    if leader_id is None:
        return web.json_response({"error": "No leader elected"}, status=503)
    return web.json_response({"leader_id": leader_id})

async def election_endpoint(request):
    """Start a leader election."""
    await start_election()  # Start the election process
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
])

# Run the app
web.run_app(app, host='0.0.0.0', port=8080)
