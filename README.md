# K8s Toy API

A simple FastAPI application for learning Kubernetes deployment with docker-compose, plain Kubernetes manifests, and Pulumi.

## The API

A minimal REST API with:
- Basic CRUD operations for items (PostgreSQL database)
- Health check endpoint with database connectivity check
- Prometheus metrics (`/metrics`)
- FastAPI automatic documentation (`/docs`)
- Async operations with asyncpg connection pooling

### Endpoints

- `GET /api/v1/healthz` - Health check
- `GET /api/v1/items` - List all items
- `GET /api/v1/items/{item_id}` - Get a specific item
- `POST /api/v1/items` - Create a new item
- `PUT /api/v1/items/{item_id}` - Update an item
- `DELETE /api/v1/items/{item_id}` - Delete an item
- `GET /metrics` - Prometheus metrics

## Local Development

### With Docker Compose (Recommended)

```bash
# Start PostgreSQL and the API
docker compose up --build

# Test the API
curl http://localhost:8000/api/v1/items
curl http://localhost:8000/api/v1/healthz

# Visit the API docs
open http://localhost:8000/api/v1/docs

# Shut down
docker compose down
# Or to remove the database volume too:
docker compose down -v
```

### Without Docker (requires local PostgreSQL)

```bash
# Install dependencies
uv sync

# Start PostgreSQL (or use an existing instance)
# Default connection: postgresql://postgres:postgres@localhost:5432/toyapi

# Run the API
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/toyapi" \
  uv run uvicorn app:app --reload --port 8000

# Test
curl http://localhost:8000/api/v1/items
```

## Kubernetes (plain manifests)

```bash
# Build the image
docker build -t k8s-toy-api:local .

# Load into your local k8s cluster
kind load docker-image k8s-toy-api:local
# OR: minikube image load k8s-toy-api:local

# Deploy database first
kubectl apply -f postgres-secret.yaml
kubectl apply -f postgres-pvc.yaml
kubectl apply -f postgres-statefulset.yaml
kubectl apply -f postgres-service.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgres --timeout=120s

# Deploy the API
kubectl apply -f deployment.yaml -f service.yaml

# Wait for API pods to be ready
kubectl wait --for=condition=ready pod -l app=toy-api --timeout=60s

# Check status
kubectl get pods,svc,pvc

# Test (via port-forward)
kubectl port-forward svc/toy-api 8000:8000
curl http://localhost:8000/api/v1/items

# OR test via NodePort (minikube)
curl "$(minikube service toy-api --url)/api/v1/items"
```

### Understanding the manifests

**Database:**
- **`postgres-secret.yaml`** - Database credentials (use proper secrets management in production)
- **`postgres-pvc.yaml`** - PersistentVolumeClaim for database storage (survives pod restarts)
- **`postgres-statefulset.yaml`** - StatefulSet for PostgreSQL (stable identity, persistent storage)
- **`postgres-service.yaml`** - Headless Service for StatefulSet DNS

**API:**
- **`deployment.yaml`** - API deployment (2 replicas, health probes, resource limits)
- **`service.yaml`** - NodePort service for external access

See the inline comments in each file for more details.

## Pulumi (Infrastructure as Code)

An alternative to plain YAML manifests - same resources, but expressed in Python with type checking and IDE support.

```bash
# First-time setup
curl -fsSL https://get.pulumi.com | sh
export PATH="$HOME/.pulumi/bin:$PATH"
pulumi login --local

cd pulumi
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
export PULUMI_CONFIG_PASSPHRASE=""
pulumi stack init dev

# Day-to-day usage
pulumi preview   # dry run
pulumi up        # apply changes
pulumi destroy   # tear down

# Get the service URL
pulumi stack output base_url
```

The Pulumi program (`pulumi/__main__.py`) creates the exact same ConfigMap + Deployment + Service as the YAML manifests.

## Setting Up a Local Kubernetes Cluster

If you don't have a local Kubernetes cluster yet, here's how to set one up:

### Option 1: Minikube (Recommended for beginners)

```bash
# Install minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
rm minikube-linux-amd64

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
rm kubectl

# Start minikube
minikube start --driver=docker

# Verify
minikube status
kubectl get nodes
```

### Option 2: Kind (Kubernetes in Docker)

```bash
# Install kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Create a cluster
kind create cluster

# Verify
kubectl cluster-info --context kind-kind
kubectl get nodes
```

### Quick Test

Once your cluster is running, test the deployment:

```bash
# Build and load the image
docker build -t k8s-toy-api:local .
minikube image load k8s-toy-api:local  # or: kind load docker-image k8s-toy-api:local

# Deploy everything
kubectl apply -f postgres-secret.yaml -f postgres-pvc.yaml -f postgres-statefulset.yaml -f postgres-service.yaml
kubectl apply -f deployment.yaml -f service.yaml

# Wait for pods
kubectl wait --for=condition=ready pod -l app=postgres --timeout=120s
kubectl wait --for=condition=ready pod -l app=toy-api --timeout=60s

# Test the API
kubectl port-forward svc/toy-api 8000:8000 &
sleep 2
curl http://localhost:8000/api/v1/items
curl http://localhost:8000/api/v1/healthz
```

## Next Steps

Things to try once the basics are working:

- **Scaling**: `kubectl scale deployment/toy-api --replicas=3`
- **Self-healing**: Delete a pod and watch it get replaced
- **Rolling updates**: Change the image, apply, and watch the rollout
- **Monitoring**: Add Prometheus scraping and Grafana dashboards
- **Ingress**: Add an Ingress controller for HTTP routing
- **Secrets**: Convert some config to a Secret resource
- **Persistent storage**: Add a database with a PersistentVolumeClaim
