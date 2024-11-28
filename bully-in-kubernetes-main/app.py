import asyncio
from aiohttp import web
from fortune_service import get_random_fortune
from bully_algorithm import run_bully, receive_coordinator

# Create an aiohttp web app
app = web.Application()

# Handlers for API routes
async def fortune_endpoint(request):
    """Return a random fortune."""
    return web.json_response({"fortune": get_random_fortune()})

async def leader_endpoint(request):
    """Return the current leader."""
    leader_id = await receive_coordinator(request)  # Correctly pass the request
    if leader_id is None:
        return web.json_response({"error": "No leader elected"}, status=503)
    return web.json_response({"leader_id": leader_id})

async def election_endpoint(request):
    """Start a leader election."""
    await run_bully()  # Await the run_bully function to start the election
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

# Background task to run the Bully Algorithm
async def background_tasks(app):
    task = asyncio.create_task(run_bully())  # Run the bully algorithm in the background
    yield  # Allow cleanup when app shuts down
    task.cancel()  # Ensure the task is cancelled
    await task  # Await task to ensure it finishes cleanly

if __name__ == '__main__':
    app.cleanup_ctx.append(background_tasks)  # Add background task to cleanup context
    web.run_app(app, host='0.0.0.0', port=8080)

