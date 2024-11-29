import asyncio
from asyncio import to_thread
from aiohttp import web
import os
import socket
import random
import aiohttp
import requests
import random

POD_IP = str(os.environ['POD_IP'])
WEB_PORT = int(os.environ['WEB_PORT'])
POD_ID = random.randint(0, 100)

ip_list = []
other_pods = dict()
leader = None
elec_in_prog = False

async def setup_k8s():
    # If you need to do setup of Kubernetes, i.e. if using Kubernetes Python client
	print("K8S setup completed")
 
async def run_bully():
    #ip_list = []
    #other_pods = dict()
    while True:
        print("Running bully")
        await asyncio.sleep(5) # wait for everything to be up
        
        # Get all pods doing bully
        global ip_list
        
        print("Making a DNS lookup to service")
        response = socket.getaddrinfo("bully-service",0,0,0,0)
        print("Get response from DNS")
        for result in response:
            ip_list.append(result[-1][0])
        ip_list = list(set(ip_list))
        
        # Remove own POD ip from the list of pods
        ip_list.remove(POD_IP)
        print("Got %d other pod ip's" % (len(ip_list)))
        
        # Get ID's of other pods by sending a GET request to them
        await asyncio.sleep(random.randint(1, 5))
        
        global other_pods
        
        async with aiohttp.ClientSession() as session:
            for pod_ip in ip_list:
                endpoint = '/pod_id'
                url = 'http://' + str(pod_ip) + ':' + str(WEB_PORT) + endpoint
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            other_pods[pod_ip] = await response.json()
                        else:
                            print(f"Failed to get response from {url}, status: {response.status}")
                except aiohttp.ClientError as e:
                    print(f"Error connecting to {url}: {e}")
                
                
        # Other pods in network
        print(other_pods)
        await asyncio.sleep(2)
        higher_priority_pods = {ip: pod['id'] for ip, pod in other_pods.items() if pod['id'] > POD_ID}
        if(not higher_priority_pods and not elec_in_prog and not leader == POD_IP):
            await start_election()
        
        
        await asyncio.sleep(5)
        random_pod = random.choice(ip_list)
        print(f"Sending health check to pod {random_pod}.")
        async with aiohttp.ClientSession() as session:
            endpoint = '/health'
            url = "http://" + str(random_pod) +":" +str(WEB_PORT) + str(endpoint)
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        print(f"Pod {random_pod} is healthy.")
                    else:
                        print(f"Pod {random_pod} is not healthy, status: {response.status}")
                        if (random_pod == leader):
                            await start_election()
            except aiohttp.ClientError as e:
                print(f"Error connecting to {url}: {e}")
        
        # Sleep a bit, then repeat
        await asyncio.sleep(10)
        if(leader == None):
            await start_election()
        
async def start_election():
    print("Starting election")
    global elec_in_prog
    elec_in_prog = True
    higher_priority_pods = {ip: pod['id'] for ip, pod in other_pods.items() if pod['id'] > POD_ID}
    
    if not higher_priority_pods:
        print("No higher-priority pods found. Declaring self as leader.")
        await announce_leader(POD_IP)
        return
    
    async with aiohttp.ClientSession() as session:
        responses = []
        sorted_pods = dict(sorted(higher_priority_pods.items(), key=lambda item: item[1], reverse=True))
        total_pods = len(sorted_pods)
        if total_pods <= 10:
            bound = total_pods
        elif total_pods <= 50:
            bound = 10
        elif total_pods <= 100:
            bound = 20
        else:
            bound = total_pods // 10
        selected_pods = list(sorted_pods.items())[:bound]
        for pod_ip, pod_id in selected_pods:
            endpoint = '/receive_election'
            url = 'http://' + str(pod_ip) + ':' + str(WEB_PORT) + endpoint
            try:
                async with session.post(url, json={"pod_id": POD_ID}) as response:
                    if response.status == 200:
                        responses.append(pod_ip)
                    else:
                        print(f"Failed to get response from {url}, status: {response.status}")
            except aiohttp.ClientError as e:
                print(f"Error connecting to {url}: {e}")
        
        if not response:
            print("No responses from higher-priority pods. Declaring self as leader.")
            await announce_leader(POD_IP)
        else:
            print("Higher-priority pods responded. Waiting for coordinator message.")
                    

async def leader_get(request):
    if(not leader == None):
        response_data = {"ip": leader, "id": other_pods.get(leader)}
    else:
        response_data = "No leader elected yet"
    return web.json_response(response_data)
    
#GET /pod_id
async def pod_id(request):
    return web.json_response({"id": POD_ID})

# Health check endpoint

async def health_check(request):
    return web.json_response({"status": "healthy"})
    
    
#POST /receive_answer
async def receive_answer(request):
    pass

#POST /receive_election
async def receive_election(request):
    data = await request.json()
    incoming_pod_id = data.get("pod_id")
    print(f"Received election message from pod {incoming_pod_id}")
    
    if POD_ID > incoming_pod_id:
        print(f"Current pod ({POD_ID}) has higher priority. Starting election")
        await start_election()
    return web.Response(text="OK")
    

#POST /receive_coordinator
async def receive_coordinator(request):
    data = await request.json()
    leader_ip = data.get("leader_ip")
    print(f"Received coordinator message. Leader is: {leader_ip}")
    global leader
    leader = leader_ip
    global elec_in_prog
    elec_in_prog = False
    return web.Response(text="OK")

async def announce_leader(leader_ip):
    print(f"Announcing leader: {leader_ip}")
    global elec_in_prog
    global leader
    leader = POD_IP
    elec_in_prog = False
    async with aiohttp.ClientSession() as session:
        for pod_ip in other_pods.keys():
            try:
                url = 'http://' + str(pod_ip) + ":" + str(WEB_PORT) + '/receive_coordinator'
                print(f"Sending coordinator message to {url}")
                await session.post(url, json={"leader_ip": leader_ip})
            except aiohttp.ClientError as e:
                print(f"Error connecting to {url}: {e}")

async def background_tasks(app):
    task = asyncio.create_task((run_bully()))
    yield
    task.cancel()
    await task
"""""
if __name__ == "__main__":
    app = web.Application()
    app.router.add_get('/pod_id', pod_id)
    app.router.add_post('/receive_answer', receive_answer)
    app.router.add_post('/receive_election', receive_election)
    app.router.add_post('/receive_coordinator', receive_coordinator)
    app.cleanup_ctx.append(background_tasks)
    web.run_app(app, host='0.0.0.0', port=WEB_PORT)
"""""