# Kubernetes Fundamentals

## Table of Contents
- [Core Concepts](#core-concepts)
- [Workload Resources](#workload-resources)
- [Service & Networking](#service--networking)
- [Configuration](#configuration)
- [Storage](#storage)
- [Security](#security)

## Core Concepts

### Architecture
```
┌─────────────────────────────────────────────────────┐
│                   Control Plane                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│  │   API Server │ │   Scheduler  │ │  Controller  │ │
│  └──────────────┘ └──────────────┘ │   Manager    │ │
│                                    └──────────────┘ │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│                     Node 1                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │   Pod    │ │   Pod    │ │   Pod    │            │
│  └──────────┘ └──────────┘ └──────────┘            │
│  kubelet    kube-proxy    container-runtime        │
└─────────────────────────────────────────────────────┘
```

### Resource Hierarchy
```
Cluster
  └── Namespace
        └── Deployment
              └── ReplicaSet
                    └── Pod
                          └── Container
```

### Labels and Selectors
```yaml
# Define labels
metadata:
  labels:
    app: myapp
    tier: frontend
    environment: production

# Select by label
selector:
  matchLabels:
    app: myapp
    tier: frontend
```

## Workload Resources

### Pod (Smallest Deployable Unit)
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myapp
spec:
  containers:
    - name: app
      image: myapp:v1
      ports:
        - containerPort: 8000
```

### Deployment (Declarative Updates)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
        - name: app
          image: myapp:v1
```

### ReplicaSet (Managed by Deployment)
Ensures specified number of pod replicas are running. Usually managed by Deployment.

### StatefulSet (Stateful Applications)
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  template:
    # ... pod template
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 10Gi
```

### DaemonSet (One Pod per Node)
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: log-collector
spec:
  selector:
    matchLabels:
      app: log-collector
  template:
    # ... pod template (runs on every node)
```

## Service & Networking

### Service Types
| Type | Description | Use Case |
|------|-------------|----------|
| ClusterIP | Internal only | Service-to-service |
| NodePort | Expose on node port | Development |
| LoadBalancer | Cloud load balancer | Production traffic |
| ExternalName | DNS CNAME | External services |

### ClusterIP Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  type: ClusterIP
  selector:
    app: myapp
  ports:
    - port: 80
      targetPort: 8000
```

### Ingress (HTTP Routing)
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
    - host: myapp.example.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: backend
                port:
                  number: 8000
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend
                port:
                  number: 3000
```

### NetworkPolicy
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-policy
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: frontend
      ports:
        - port: 8000
```

## Configuration

### ConfigMap (Non-Sensitive Config)
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  LOG_LEVEL: "info"
  API_TIMEOUT: "30"
  config.json: |
    {
      "feature_flags": {
        "new_ui": true
      }
    }
```

### Secret (Sensitive Data)
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
stringData:              # Plain text (auto-encoded)
  DATABASE_URL: "postgres://user:pass@host/db"
data:                    # Base64 encoded
  API_KEY: YXBpLWtleS12YWx1ZQ==
```

### Using Config in Pods
```yaml
spec:
  containers:
    - name: app
      # All keys as env vars
      envFrom:
        - configMapRef:
            name: app-config
        - secretRef:
            name: app-secrets
      # Specific keys
      env:
        - name: DB_HOST
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: DB_HOST
      # As files
      volumeMounts:
        - name: config-volume
          mountPath: /etc/config
  volumes:
    - name: config-volume
      configMap:
        name: app-config
```

## Storage

### PersistentVolume (Cluster Resource)
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-storage
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: standard
  hostPath:
    path: /data
```

### PersistentVolumeClaim (Namespace Request)
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  storageClassName: standard
```

### Using PVC in Pod
```yaml
spec:
  containers:
    - name: app
      volumeMounts:
        - name: data
          mountPath: /app/data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: app-data
```

## Security

### SecurityContext (Pod Level)
```yaml
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000
```

### SecurityContext (Container Level)
```yaml
spec:
  containers:
    - name: app
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop:
            - ALL
```

### ServiceAccount
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-service-account
---
spec:
  serviceAccountName: app-service-account
```

### Resource Quotas
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "10"
```

## Health Checks

### Liveness Probe (Restart if Failed)
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 15
  periodSeconds: 20
  timeoutSeconds: 5
  failureThreshold: 3
```

### Readiness Probe (Remove from Service if Failed)
```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 3
```

### Startup Probe (For Slow-Starting Containers)
```yaml
startupProbe:
  httpGet:
    path: /health
    port: 8000
  failureThreshold: 30
  periodSeconds: 10
```

## Scaling

### Horizontal Pod Autoscaler
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: myapp-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

### Manual Scaling
```bash
kubectl scale deployment myapp --replicas=5
```
