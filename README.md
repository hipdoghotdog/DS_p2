# bully-in-kubernetes
This project includes automated tests for the Kubernetes-based leader election implementation.

### Prerequisites

Ensure you have the following tools installed:
- [Node.js](https://nodejs.org/)
- [Kubernetes](https://kubernetes.io/docs/setup/)
- [Docker](https://www.docker.com/get-started)
- [kubectl](https://kubernetes.io/docs/reference/kubectl/overview/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop)

## Setup and Running the Application

Follow these steps to build and run the Bully algorithm in Kubernetes.

### 1. Navigate to the Project Directory
First, navigate to the correct folder where the project is located:
```
cd bully-in-kubernetes-main
```
### 2. Build the Docker Image
Once you're inside the `bully-in-kubernetes-main` folder, build the Docker image for the application:
```
docker build -t bully-app .
```
### 3. Configure `kubectl` for Docker Desktop
After the Docker image has been built successfully, configure `kubectl` to use the `docker-desktop` context:
```
kubectl config use-context docker-desktop
```
### 4. Apply Kubernetes Configurations
Next, apply the Kubernetes configuration files to set up the service and statefulset:
```
kubectl apply -f ./k8s/headless-service.yaml
```
```
kubectl apply -f ./k8s/statefulset.yaml
```

### 5. Set Up the Ingress Controller (Only if Not Already Installed)
If you don't already have the Ingress controller set up, follow these steps:

- Apply the Ingress resource:

```
kubectl apply -f ./k8s/ingress.yaml

```

- Deploy the NGINX ingress controller:
```
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml
```

- Verify the Ingress controller is running:
```
kubectl get deployment -n ingress-nginx
```

### 5. Check the Pods
To verify if everything is running as expected, check the status of the pods:
```
kubectl get pods
There should by default be 3 pods {bully-app-0, bully-app-1, bully-app-3}
```
### 6. Troubleshooting
If there are any issues, you can check the logs of the individual pods to see what might be wrong. Use the following command to retrieve the logs for a specific pod:
```
kubectl logs <pod_name>
```
If the pod is not running, you can describe the pod to get more detailed status information:
```
kubectl describe pod <pod_name>
```

### 8. Accessing the Application
Once everything is running correctly, you can access the application directly in your browser at [http://localhost](http://localhost), thanks to the Ingress configuration.

### 9. Scaling the Deployment
To scale the number of replicas in the deployment, use the following command:

```
kubectl scale statefulsets bully-app --replicas=<desired_number_of_replicas>
```
### 10. Stopping and Deleting the Application
To stop the application and delete the deployment, use the following command:
```
kubectl delete -f ./k8s/statefulset.yaml
```
To clean up everything created by Kubernetes (including the service, ingress, and deployment), use:

```
kubectl delete -f ./k8s/
```

---

### Additional Notes
- Ensure that Kubernetes is running properly on Docker Desktop and that `kubectl` is correctly configured.
- The Ingress setup replaces the need for `kubectl port-forward`, making it easier to access the application via `localhost`.
- If you encounter any issues with the Kubernetes setup or Docker build, check the logs for more specific error messages.

---

## Testing Instructions

### Load Test

1. Check the status of your pods:
```
kubectl get pods
```
2. Navigate to the `tests` directory:
```
cd tests
```
3. Run the load test:
```
node loadTest.js
```
4. After the test finishes, check the status of your pods again:
```
kubectl get pods
```
5. To return to the root directory:
```
cd ..
```
### Simulate Pod Failure 1
1. Set up a deseired amount of pods and check the pods are running:
```
kubectl get pods
They should have names like 'bully-app-0' with the number going up to N-1 for N replicas
```
2. In Docker desktop or through the logs command observe the bully algorithm process in the pods
```
kubectl logs <pod-name>
```
3. Locate the leader pod and delete it
```
kubectl delete pod <pod_name>
```
4. A new pod will be created. Watch the change in leadership in Docker Desktop.

### Simulate Pod failure 2 
1. Setup the pods like explained earlier
2. Instead of deleting pods we will be disabling the leader
- Find which pod is the leader as described earlier
- Either in the terminal or in docker desktop enter the pod's command line
- Run this command
    - curl -X POST http://<bully-app-x>:8080/disable_leader
        - replace the 'x' with the relevant number of the pod
3. Now the leader is disabled, observe the other pods
- The pods run health checks on eachother regularly, this way they can discover the leader is disabled
4. If you want to restore the pod
- Run this command
    - curl -X POST http://<bully-app-x>:8080/reset
    - The pod should start an election and become leader again


- Ensure that Kubernetes is running properly on Docker Desktop and that `kubectl` is correctly configured.
- The Ingress setup replaces the need for `kubectl port-forward`, making it easier to access the application via `localhost`.
- If you encounter any issues with the Kubernetes setup or Docker build, check the logs for more specific error messages.



