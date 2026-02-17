# Local Kubernetes Setup

## Table of Contents
- [Tool Comparison](#tool-comparison)
- [minikube](#minikube)
- [kind (Kubernetes in Docker)](#kind-kubernetes-in-docker)
- [Docker Desktop Kubernetes](#docker-desktop-kubernetes)
- [Common Setup Tasks](#common-setup-tasks)

## Tool Comparison

| Feature | minikube | kind | Docker Desktop |
|---------|----------|------|----------------|
| Setup Complexity | Medium | Easy | Easy |
| Resource Usage | Medium | Low | Medium |
| Multi-node | Yes | Yes | No |
| Load Balancer | Tunnel | No | Yes |
| Ingress | Addon | Manual | Built-in |
| Best For | Full features | CI/CD, Testing | Mac/Windows dev |

## minikube

### Installation

**macOS:**
```bash
brew install minikube
```

**Linux:**
```bash
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
```

**Windows:**
```bash
choco install minikube
```

### Starting a Cluster

```bash
# Start with default settings
minikube start

# Start with specific resources
minikube start --cpus=4 --memory=8192 --disk-size=20g

# Start with specific Kubernetes version
minikube start --kubernetes-version=v1.28.0

# Start with specific driver
minikube start --driver=docker    # or hyperv, virtualbox, etc.
```

### Useful Commands

```bash
# Check status
minikube status

# Dashboard
minikube dashboard

# Get IP
minikube ip

# SSH into node
minikube ssh

# Stop cluster
minikube stop

# Delete cluster
minikube delete

# Delete all clusters
minikube delete --all
```

### Addons

```bash
# List available addons
minikube addons list

# Enable ingress
minikube addons enable ingress

# Enable metrics-server
minikube addons enable metrics-server

# Enable registry
minikube addons enable registry
```

### Accessing Services

```bash
# Create tunnel for LoadBalancer services
minikube tunnel

# Open service in browser
minikube service myapp-service

# Get service URL
minikube service myapp-service --url
```

### Using Local Docker Images

```bash
# Point docker CLI to minikube's Docker daemon
eval $(minikube docker-env)

# Build image (available in minikube)
docker build -t myapp:local .

# Use in deployment with imagePullPolicy: Never
```

## kind (Kubernetes in Docker)

### Installation

**macOS:**
```bash
brew install kind
```

**Linux:**
```bash
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```

### Creating a Cluster

```bash
# Simple cluster
kind create cluster

# Named cluster
kind create cluster --name my-cluster

# With config file
kind create cluster --config kind-config.yaml
```

### Cluster Configuration

**kind-config.yaml:**
```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    kubeadmConfigPatches:
      - |
        kind: InitConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            node-labels: "ingress-ready=true"
    extraPortMappings:
      - containerPort: 80
        hostPort: 80
        protocol: TCP
      - containerPort: 443
        hostPort: 443
        protocol: TCP
  - role: worker
  - role: worker
```

### Loading Images

```bash
# Build locally, then load into kind
docker build -t myapp:local .
kind load docker-image myapp:local --name my-cluster

# Load from tar
kind load image-archive myapp.tar --name my-cluster
```

### Useful Commands

```bash
# List clusters
kind get clusters

# Get kubeconfig
kind get kubeconfig --name my-cluster

# Delete cluster
kind delete cluster --name my-cluster

# Get nodes
kind get nodes --name my-cluster
```

### Setting Up Ingress

```bash
# Install nginx ingress controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Wait for it to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
```

## Docker Desktop Kubernetes

### Enabling Kubernetes

1. Open Docker Desktop settings
2. Go to "Kubernetes" tab
3. Check "Enable Kubernetes"
4. Click "Apply & Restart"

### Switching Contexts

```bash
# List contexts
kubectl config get-contexts

# Switch to Docker Desktop
kubectl config use-context docker-desktop
```

### Reset Kubernetes

1. Docker Desktop → Settings → Kubernetes
2. Click "Reset Kubernetes Cluster"

## Common Setup Tasks

### Install kubectl

**macOS:**
```bash
brew install kubectl
```

**Linux:**
```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
```

### Verify Installation

```bash
# Check kubectl version
kubectl version --client

# Check cluster info
kubectl cluster-info

# Get nodes
kubectl get nodes
```

### Set Up Namespace

```bash
# Create namespace
kubectl create namespace dev

# Set default namespace
kubectl config set-context --current --namespace=dev
```

### Deploy Sample Application

```bash
# Create deployment
kubectl create deployment nginx --image=nginx

# Expose as service
kubectl expose deployment nginx --port=80 --type=NodePort

# Get service URL (minikube)
minikube service nginx --url

# Forward port locally
kubectl port-forward service/nginx 8080:80
```

### Quick Test Workflow

```bash
# 1. Start cluster
minikube start  # or kind create cluster

# 2. Deploy app
kubectl apply -f ./k8s/

# 3. Check status
kubectl get pods -w

# 4. Access app
kubectl port-forward service/myapp 8080:8000

# 5. View logs
kubectl logs -f deployment/myapp

# 6. Clean up
kubectl delete -f ./k8s/
```

### Debugging

```bash
# Describe pod
kubectl describe pod myapp-xyz

# Get events
kubectl get events --sort-by='.lastTimestamp'

# Shell into pod
kubectl exec -it myapp-xyz -- /bin/sh

# Check resource usage
kubectl top pods
kubectl top nodes
```
