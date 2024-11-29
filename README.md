# bully-in-kubernetes
A template to implement the Bully algorithm in Kubernetes.

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
Next, apply the Kubernetes configuration files to set up the service and deployment:
```
kubectl apply -f ./k8s/headless-service.yaml
```
```
kubectl apply -f ./k8s/deployment.yaml
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
kubectl scale deployment bully-app --replicas=<desired_number_of_replicas>
```
### 9. Stopping the Application
When you're done, you can stop the application by scaling the deployment to zero replicas:
```
kubectl scale deployment bully-app --replicas=0
```

---

### Additional Notes
- Ensure that Kubernetes is running properly on Docker Desktop and that `kubectl` is correctly configured.
- The Ingress setup replaces the need for `kubectl port-forward`, making it easier to access the application via `localhost`.
- If you encounter any issues with the Kubernetes setup or Docker build, check the logs for more specific error messages.

