import asyncio
from asyncio import to_thread
from aiohttp import web, ClientTimeout
import os
import socket
import random
import aiohttp
import requests
import random

POD_IP = str(os.environ['POD_IP'])
WEB_PORT = int(os.environ['WEB_PORT'])
POD_ID = random.randint(0, 100)
STATEFULSET_NAME = os.environ.get('STATEFULSET_NAME', 'bully-app')
NAMESPACE = os.environ.get('POD_NAMESPACE', 'default')
REPLICAS = int(os.environ.get('REPLICAS',3))

ACTIVE = True
ip_list = []
other_pods = dict()
leader = None
elec_in_prog = False

 
async def setup_pod_list():
    global ip_list
    replicas = await get_current_replicas_http(STATEFULSET_NAME)
    if replicas is None:
        replicas = REPLICAS
    ip_list = [
        f"{STATEFULSET_NAME}-{i}.bully-service.{NAMESPACE}.svc.cluster.local"
        for i in range(replicas)
    ]
    ip_list = [ip for ip in ip_list if not ip.startswith(POD_IP)]
    
 
async def run_bully():
    #ip_list = []
    #other_pods = dict()
    while True:
        
        while not ACTIVE:
            await asyncio.sleep(1)
        
        print("Running bully")
        await asyncio.sleep(5) # wait for everything to be up
        
        # Get all pods doing bully
        global ip_list
        print("Fetching all pods")
        await setup_pod_list()
        
        
        print("Got %d other pod ip's" % (len(ip_list)))
        
        # Get ID's of other pods by sending a GET request to them
        await asyncio.sleep(random.randint(1, 5))
        
        global other_pods
        
        async with aiohttp.ClientSession(timeout=ClientTimeout(total=5)) as session:
            for pod_ip in ip_list:
                endpoint = '/pod_id'
                url = 'http://' + str(pod_ip) + ':' + str(WEB_PORT) + endpoint
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            other_pods[pod_ip] = await response.json()
                        else:
                            print(f"Failed to get response from {url}, status: {response.status}")
                            ip_list.remove(pod_ip)
                except aiohttp.ClientError as e:
                    print(f"Error connecting to {url}: {e}")
                
                
        # Other pods in network
        print(other_pods)
        await asyncio.sleep(2)
        higher_priority_pods = {ip: pod['pod_id'] for ip, pod in other_pods.items() if pod['pod_id'] > POD_ID}
        if(not higher_priority_pods and not elec_in_prog and not leader == POD_ID):
            await start_election()
        
        await asyncio.sleep(1)
        
        print(f"Sending health checks.")
        if len(ip_list) < 5:
            samples = len(ip_list)
        elif len(ip_list) < 50:
            samples = 10
        else:
            samples = 15
        async with aiohttp.ClientSession(timeout=ClientTimeout(total=5)) as session:
            for pod_ip in random.sample(ip_list,samples):
                endpoint = '/health'
                url = "http://" + str(pod_ip) +":" +str(WEB_PORT) + str(endpoint)
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            print(f"Pod {other_pods[pod_ip]} is healthy.")
                        else:
                            print(f"Pod {other_pods[pod_ip]} is not healthy, status: {response.status}")
                            if (other_pods[pod_ip]["pod_id"] == leader):
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
    higher_priority_pods = {ip: pod['pod_id'] for ip, pod in other_pods.items() if pod['pod_id'] > POD_ID}
    
    if not higher_priority_pods:
        print("No higher-priority pods found. Declaring self as leader.")
        await announce_leader()
        return
    
    async with aiohttp.ClientSession(timeout=ClientTimeout(total=5)) as session:
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
        await asyncio.sleep(1)
        
        if len(responses) == 0:
            print("No responses from higher-priority pods. Declaring self as leader.")
            await announce_leader()
        else:
            print("Higher-priority pods responded. Waiting for coordinator message.")
                    

async def leader_get(request):
    if (leader == POD_ID):
        response_data = {"pod_id": POD_ID, "pod_ip": POD_IP}
    elif(not leader == None):
        pod_ip = {ip: pod["pod_ip"] for ip, pod in other_pods.items() if pod['id'] == POD_ID}
        response_data = {"pod_id": leader, "pod_ip": pod_ip}
    else:
        response_data = "No leader elected yet"
    return web.json_response(response_data)
    
#GET /pod_id
async def pod_id(request):
    return web.json_response({"pod_id": POD_ID})

# Health check endpoint

async def health_check(request):
    if not ACTIVE:
        return web.json_response({"status": "unhealthy"}, status=503)
    return web.json_response({"status": "healthy"})
    
    
#POST /receive_answer
async def receive_answer(request):
    pass

#POST /receive_election
async def receive_election(request):
    data = await request.json()
    incoming_pod_id = data.get("pod_id")
    print(f"Received election message from pod {incoming_pod_id}")
    
    if POD_ID > incoming_pod_id and ACTIVE:
        print(f"Current pod ({POD_ID}) has higher priority. Starting election")
        await start_election()
        return web.Response(text="OK")
    else:
        return web.Response(text="", status=503)
    
async def sleep(i):
    await asyncio.sleep(i)
    return

#POST /receive_coordinator
async def receive_coordinator(request):
    data = await request.json()
    leader_id = data.get("leader_id")
    print(f"Received coordinator message. Leader is: {leader_id}")
    global leader
    leader = leader_id
    global elec_in_prog
    elec_in_prog = False
    await asyncio.sleep(1)
    return web.Response(text="OK") 

async def announce_leader():
    print(f"Announcing leader: {POD_ID}")
    global elec_in_prog
    global leader
    leader = POD_ID
    elec_in_prog = False
    async with aiohttp.ClientSession(timeout=ClientTimeout(total=5)) as session:
        for pod_ip in other_pods.keys():
            try:
                url = 'http://' + str(pod_ip) + ":" + str(WEB_PORT) + '/receive_coordinator'
                print(f"Sending coordinator message to {url}")
                await session.post(url, json={"leader_id": POD_ID})
            except aiohttp.ClientError as e:
                print(f"Error connecting to {url}: {e}")
                
# POST /disable_leader
async def disable_leader(request):
    """Disable the leader pod to simulate failure."""
    global ACTIVE, leader
    if leader == POD_ID:
        ACTIVE = False
        print(f"Leader pod {POD_ID} disabled.")
        return web.json_response({"message": f"Leader pod {POD_ID} has been disabled."})
    else:
        return web.json_response({"error": "This pod is not the leader."}, status=403)
    
# POST /reset
async def reset(request):
    """Reset the pod to an active state."""
    global ACTIVE
    ACTIVE = True
    print(f"Pod {POD_ID} reset to active state.")
    return web.json_response({"message": f"Pod {POD_ID} is now active."})
    
    
async def get_current_replicas_http(statefulset_name, namespace="default"):
    """Fetch the current replicas using direct HTTP request."""
    try:
        # Read service account token
        with open("/var/run/secrets/kubernetes.io/serviceaccount/token", "r") as f:
            token = f.read()

        # Kubernetes API URL
        api_server = os.getenv("KUBERNETES_SERVICE_HOST", "kubernetes.default.svc")
        url = f"https://{api_server}/apis/apps/v1/namespaces/{namespace}/statefulsets/{statefulset_name}"

        # Send GET request
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers, verify="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt")

        if response.status_code == 200:
            statefulset = response.json()
            return statefulset["status"]["replicas"]
        else:
            print(f"Failed to fetch replicas: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"Error fetching replicas: {e}")
        return None


async def background_tasks(app):
    task = asyncio.create_task((run_bully()))
    yield
    task.cancel()
    await task
