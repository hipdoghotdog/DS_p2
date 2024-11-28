import os
import asyncio
import socket
import random
import aiohttp
from aiohttp import web

POD_IP = str(os.environ['POD_IP'])
WEB_PORT = int(os.environ['WEB_PORT'])
POD_ID = random.randint(0, 100)

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
async def start_election():
    global leader
    print("Starting Bully algorithm...")

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

# Function to return the current leader
async def get_leader():
    return web.json_response({"leader": leader})  # Ensure "web" is defined


# Function to serve the pod ID when queried
async def pod_id(request):
    return web.json_response({"pod_id": POD_ID})
