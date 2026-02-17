# Cloud Kubernetes Providers

## Table of Contents
- [Provider Comparison](#provider-comparison)
- [AWS EKS](#aws-eks)
- [Google GKE](#google-gke)
- [Azure AKS](#azure-aks)
- [Common Patterns](#common-patterns)

## Provider Comparison

| Feature | EKS (AWS) | GKE (Google) | AKS (Azure) |
|---------|-----------|--------------|-------------|
| Control Plane Cost | $0.10/hr | Free (Autopilot: $0.10/hr) | Free |
| Node Scaling | Cluster Autoscaler | GKE Autopilot | VMSS Autoscaler |
| Load Balancer | AWS ALB/NLB | GCP Load Balancer | Azure LB |
| Container Registry | ECR | Artifact Registry | ACR |
| IAM Integration | IAM Roles | Workload Identity | Azure AD |
| CLI | eksctl, aws | gcloud | az |

## AWS EKS

### Prerequisites
```bash
# Install AWS CLI
brew install awscli

# Install eksctl
brew install eksctl

# Configure AWS credentials
aws configure
```

### Create Cluster
```bash
# Create cluster with eksctl
eksctl create cluster \
  --name my-cluster \
  --region us-west-2 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 5 \
  --managed

# Or with config file
eksctl create cluster -f cluster.yaml
```

**cluster.yaml:**
```yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: my-cluster
  region: us-west-2

nodeGroups:
  - name: ng-1
    instanceType: t3.medium
    desiredCapacity: 3
    minSize: 1
    maxSize: 5
    volumeSize: 50
    ssh:
      allow: false
```

### Update kubeconfig
```bash
aws eks update-kubeconfig --region us-west-2 --name my-cluster
```

### ECR (Container Registry)
```bash
# Create repository
aws ecr create-repository --repository-name myapp

# Login to ECR
aws ecr get-login-password --region us-west-2 | \
  docker login --username AWS --password-stdin \
  123456789.dkr.ecr.us-west-2.amazonaws.com

# Tag and push
docker tag myapp:latest 123456789.dkr.ecr.us-west-2.amazonaws.com/myapp:latest
docker push 123456789.dkr.ecr.us-west-2.amazonaws.com/myapp:latest
```

### AWS Load Balancer Controller
```bash
# Install controller
eksctl utils associate-iam-oidc-provider --cluster my-cluster --approve

kubectl apply -f https://github.com/kubernetes-sigs/aws-load-balancer-controller/releases/download/v2.6.0/v2_6_0_full.yaml
```

**Ingress with ALB:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
spec:
  rules:
    - http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: myapp
                port:
                  number: 80
```

### Clean Up
```bash
eksctl delete cluster --name my-cluster --region us-west-2
```

## Google GKE

### Prerequisites
```bash
# Install gcloud CLI
brew install google-cloud-sdk

# Login and set project
gcloud auth login
gcloud config set project my-project
```

### Create Cluster
```bash
# Standard cluster
gcloud container clusters create my-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type e2-medium \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 5

# Autopilot cluster (fully managed)
gcloud container clusters create-auto my-cluster \
  --region us-central1
```

### Get Credentials
```bash
gcloud container clusters get-credentials my-cluster --zone us-central1-a
```

### Artifact Registry
```bash
# Create repository
gcloud artifacts repositories create myapp \
  --repository-format=docker \
  --location=us-central1

# Configure Docker auth
gcloud auth configure-docker us-central1-docker.pkg.dev

# Tag and push
docker tag myapp:latest us-central1-docker.pkg.dev/my-project/myapp/myapp:latest
docker push us-central1-docker.pkg.dev/my-project/myapp/myapp:latest
```

### GKE Ingress
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
  annotations:
    kubernetes.io/ingress.class: gce
spec:
  rules:
    - http:
        paths:
          - path: /*
            pathType: ImplementationSpecific
            backend:
              service:
                name: myapp
                port:
                  number: 80
```

### Workload Identity
```bash
# Enable workload identity
gcloud container clusters update my-cluster \
  --zone us-central1-a \
  --workload-pool=my-project.svc.id.goog

# Create service account binding
gcloud iam service-accounts add-iam-policy-binding \
  my-gcp-sa@my-project.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:my-project.svc.id.goog[NAMESPACE/KSA_NAME]"
```

### Clean Up
```bash
gcloud container clusters delete my-cluster --zone us-central1-a
```

## Azure AKS

### Prerequisites
```bash
# Install Azure CLI
brew install azure-cli

# Login
az login
az account set --subscription "My Subscription"
```

### Create Cluster
```bash
# Create resource group
az group create --name myResourceGroup --location eastus

# Create cluster
az aks create \
  --resource-group myResourceGroup \
  --name my-cluster \
  --node-count 3 \
  --node-vm-size Standard_DS2_v2 \
  --enable-cluster-autoscaler \
  --min-count 1 \
  --max-count 5 \
  --generate-ssh-keys
```

### Get Credentials
```bash
az aks get-credentials --resource-group myResourceGroup --name my-cluster
```

### ACR (Container Registry)
```bash
# Create registry
az acr create --resource-group myResourceGroup --name myacr --sku Basic

# Login
az acr login --name myacr

# Tag and push
docker tag myapp:latest myacr.azurecr.io/myapp:latest
docker push myacr.azurecr.io/myapp:latest

# Attach ACR to AKS
az aks update \
  --resource-group myResourceGroup \
  --name my-cluster \
  --attach-acr myacr
```

### NGINX Ingress Controller
```bash
# Install ingress controller
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --create-namespace \
  --namespace ingress
```

### Clean Up
```bash
az aks delete --resource-group myResourceGroup --name my-cluster --yes
az group delete --name myResourceGroup --yes
```

## Common Patterns

### CI/CD Pipeline Structure
```yaml
# GitHub Actions example
name: Deploy to K8s

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build and push image
        run: |
          docker build -t $REGISTRY/$IMAGE:$GITHUB_SHA .
          docker push $REGISTRY/$IMAGE:$GITHUB_SHA

      - name: Deploy to cluster
        run: |
          kubectl set image deployment/myapp \
            myapp=$REGISTRY/$IMAGE:$GITHUB_SHA
```

### Multi-Environment Setup
```
clusters/
├── dev/
│   └── kustomization.yaml
├── staging/
│   └── kustomization.yaml
└── production/
    └── kustomization.yaml
```

### Secrets Management
```bash
# AWS Secrets Manager + External Secrets
kubectl apply -f https://raw.githubusercontent.com/external-secrets/external-secrets/main/deploy/crds/bundle.yaml

# GCP Secret Manager
gcloud secrets create my-secret --data-file=./secret.txt

# Azure Key Vault
az keyvault secret set --vault-name myKeyVault --name mySecret --value "secret"
```

### Cost Optimization
- Use spot/preemptible instances for non-critical workloads
- Enable cluster autoscaler with appropriate min/max
- Use node auto-provisioning (GKE) or Karpenter (EKS)
- Set resource requests/limits appropriately
- Use namespace quotas
