import asyncio
from aiohttp import web
import os
import socket
import random
import aiohttp
import requests

POD_IP = str(os.environ['POD_IP'])
WEB_PORT = int(os.environ['WEB_PORT'])
POD_ID = random.randint(0, 100)

# A dictionary to keep track of pod IDs and their states (whether they are the leader or not)
pod_info = {}

# Global variable to store the current leader pod
leader = None

# Function to query the other pods for their pod ID
async def get_other_pods():
    ip_list = []
    print("Making a DNS lookup to service")
    response = socket.getaddrinfo("bully-service", 0, 0, 0, 0)
    for result in response:
        ip_list.append(result[-1][0])
    ip_list = list(set(ip_list))

    ip_list.remove(POD_IP)  # Remove self from the list of pods
    return ip_list

# The Bully algorithm to determine the leader
async def run_bully():
    global pod_info, leader
    print("Running Bully algorithm...")

    # Get all other pod IPs using the DNS lookup
    ip_list = await get_other_pods()
    other_pods = {}

    async with aiohttp.ClientSession() as session:
        for pod_ip in ip_list:
            url = f'http://{pod_ip}:{WEB_PORT}/pod_id'
            try:
                async with session.get(url) as response:
                    pod_data = await response.json()
                    other_pods[str(pod_ip)] = pod_data
            except Exception as e:
                print(f"Failed to get data from {pod_ip}: {str(e)}")

    print("Other pods in network:", other_pods)

    # Determine leader election by comparing pod IDs (Bully algorithm)
    if other_pods:
        leader = max(other_pods, key=other_pods.get)  # Leader is the pod with the highest ID
        print(f"New leader elected: {leader}")
    else:
        print("No other pods found to elect a leader.")

    pod_info = other_pods  # Update pod info with the elected leader


# Function to serve the pod ID when queried
async def pod_id(request):
    return web.json_response({"pod_id": POD_ID})

# Endpoint to trigger election
async def election_endpoint(request):
    print("Election started!")
    await run_bully()
    return web.json_response({"message": "Election started"})

# Endpoint to get the current leader
async def leader_endpoint(request):
    if leader:
        return web.json_response({"leader": leader})
    else:
        return web.json_response({"leader": "No leader elected"}, status=503)

# Function to serve fortune cookies
async def fortune_endpoint(request):
    return web.json_response({"fortune": "You will have a great day!"})

# Set up the app
async def background_tasks(app):
    task = asyncio.create_task(run_bully())
    yield
    task.cancel()
    await task

# Create and run the app
app = web.Application()
app.router.add_get('/pod_id', pod_id)
app.router.add_post('/api/election', election_endpoint)
app.router.add_get('/api/fortune', fortune_endpoint)
app.router.add_get('/api/leader', leader_endpoint)  # Added route for current leader

app.cleanup_ctx.append(background_tasks)
web.run_app(app, host='0.0.0.0', port=WEB_PORT)
