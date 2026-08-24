# K8s Toy API

A simple FastAPI application for learning Kubernetes deployment with plain Kubernetes manifests and Pulumi.

---

## Learning Track: Kubernetes Fundamentals

**Goal:** Understand how Kubernetes works by deploying a real application with a database.

**Time:** 2-3 hours total | **Prerequisites:** Docker installed

### Quick Start (Recommended First Step)

**Do:** Run `./start.sh` and watch what happens
**Insight:** Kubernetes isn't magic—it's containers + orchestration. The script shows you deployment, health checks, and service discovery in 2 minutes.
**Verify:** Visit `http://localhost:8000/docs` and see the API running
**Time:** 5 minutes

---

### Track A: Core Concepts (Linear Path)

#### 1. Docker Compose Baseline
**Do:** `docker compose up` and explore the API
**Insight:** Before Kubernetes, understand the application itself. Two containers (API + PostgreSQL) talking to each other.
**Verify:** CRUD operations work at `/docs`, database persists data
**Time:** 15 minutes
**Why this matters:** You need to know what you're deploying before learning *how* to deploy it.

#### 2. Deploy to Kubernetes (Manual)
**Do:** Follow "Kubernetes (plain manifests)" section—deploy PostgreSQL first, then API
**Insight:** Kubernetes separation of concerns: ConfigMaps (config), Secrets (credentials), StatefulSets (databases), Deployments (stateless apps)
**Verify:** `kubectl get pods` shows running pods, `kubectl port-forward` lets you access the API
**Time:** 30 minutes
**Going deeper:** Read inline comments in each YAML manifest

#### 3. Self-Healing
**Do:** `kubectl delete pod <api-pod-name>` and watch Kubernetes recreate it
**Insight:** Declarative systems maintain desired state. You said "2 replicas," Kubernetes ensures 2 replicas always exist.
**Verify:** `kubectl get pods -w` shows new pod spinning up immediately
**Time:** 5 minutes
**Try also:** Delete the PostgreSQL pod—StatefulSet recreates it with the same identity and storage

#### 4. Scaling
**Do:** `kubectl scale deployment/toy-api --replicas=5`
**Insight:** Horizontal scaling is trivial for stateless apps. Database scaling is hard (hence StatefulSet vs Deployment).
**Verify:** `kubectl get pods` shows 5 API pods, all sharing the same database
**Time:** 5 minutes
**Going deeper:** Send requests, watch them load-balance across pods (`kubectl logs -f <pod-name>`)

#### 5. Configuration Management
**Do:** Edit `postgres-configmap.yaml` to change database name, `kubectl apply -f`, restart pods
**Insight:** Config lives outside containers. Change config without rebuilding images.
**Verify:** Pods pick up new DATABASE_URL from ConfigMap + Secret
**Time:** 15 minutes
**Going deeper:** Try `kubectl exec` to shell into a pod and see environment variables

#### 6. Persistent Storage
**Do:** Delete PostgreSQL pod, verify data survived
**Insight:** PersistentVolumeClaims decouple storage from pod lifecycle. Database survives restarts.
**Verify:** `kubectl get pvc` shows bound volume, data still there after pod deletion
**Time:** 10 minutes
**Going deeper:** [WHY_KUBERNETES.md](WHY_KUBERNETES.md) explains when persistence matters

---

### Track B: Infrastructure as Code (Alternative)

**For developers who prefer Python to YAML:**

#### 1-3. Same as Track A (understand the app first)

#### 4. Pulumi Deployment
**Do:** Follow "Pulumi" section—deploy with `pulumi up`
**Insight:** Same resources, different syntax. YAML is declarative, but Pulumi adds type checking and reusability.
**Verify:** `pulumi stack output base_url` shows the API URL
**Time:** 30 minutes
**When to use:** Multi-environment deployments, shared modules, CI/CD pipelines

---

### Next Steps

Once you've completed either track:

**Continue learning here (k8s-hack):**
- [WHY_KUBERNETES.md](WHY_KUBERNETES.md) - When (and when not) to use Kubernetes
- [LOGGING.md](LOGGING.md) - Structured logging and log aggregation
- [AUTH.md](AUTH.md) - Authentication and authorization patterns
- [GITOPS.md](GITOPS.md) - GitOps introduction (then go to gitops-lab)

**Graduate to production patterns (gitops-lab):**
- Deploy this same app with ArgoCD (GitOps)
- Add queue-based autoscaling (KEDA)
- Make cost/deployment decisions (single-box vs ASG vs EKS)

👉 **[Continue to gitops-lab](https://github.com/wware/gitops-lab)** for production deployment patterns

---

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

## Quick Start

Get started with Kubernetes in one command:

```bash
# One-command deployment and testing (requires Minikube)
./start.sh
```

This is the recommended first interaction - it shows you Kubernetes in action immediately.

## Alternative: Local Development

### With Docker Compose

For understanding the application architecture without Kubernetes:

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

### Understanding the Deployment

The `start.sh` script (recommended above) handles everything automatically. For manual deployment or using other clusters (kind, etc.):

```bash
# Build the image
docker build -t k8s-toy-api:local .

# Load into your local k8s cluster
kind load docker-image k8s-toy-api:local
# OR: minikube image load k8s-toy-api:local

# Deploy database first
kubectl apply -f postgres-configmap.yaml  # Non-sensitive config
kubectl apply -f postgres-secret.yaml     # Sensitive credentials
kubectl apply -f postgres-pvc.yaml        # Persistent storage
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

# Run comprehensive tests
./test-api.sh
```

### Understanding the manifests

**Database:**
- **`postgres-configmap.yaml`** - Non-sensitive configuration (host, port, database name, user)
- **`postgres-secret.yaml`** - Sensitive credentials (password only - best practice)
- **`postgres-pvc.yaml`** - PersistentVolumeClaim for database storage (survives pod restarts)
- **`postgres-statefulset.yaml`** - StatefulSet for PostgreSQL (stable identity, persistent storage)
- **`postgres-service.yaml`** - Headless Service for StatefulSet DNS

**API:**
- **`deployment.yaml`** - API deployment (2 replicas, health probes, resource limits)
  - Constructs `DATABASE_URL` from ConfigMap + Secret components
- **`service.yaml`** - NodePort service for external access

**Automation:**
- **`start.sh`** - One-command deployment script (build, load, deploy, test)
- **`test-api.sh`** - Comprehensive API test suite (CRUD operations + error handling)

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

Once your cluster is running, use the automated script:

```bash
# One-command deployment and testing (recommended for minikube)
./start.sh
```

Or manually for kind/other clusters:

```bash
# Build and load the image
docker build -t k8s-toy-api:local .
kind load docker-image k8s-toy-api:local  # or: minikube image load k8s-toy-api:local

# Deploy everything
kubectl apply -f postgres-configmap.yaml -f postgres-secret.yaml -f postgres-pvc.yaml
kubectl apply -f postgres-statefulset.yaml -f postgres-service.yaml
kubectl apply -f deployment.yaml -f service.yaml

# Wait for pods
kubectl wait --for=condition=ready pod -l app=postgres --timeout=120s
kubectl wait --for=condition=ready pod -l app=toy-api --timeout=60s

# Test the API
kubectl port-forward svc/toy-api 8000:8000 &
sleep 2
./test-api.sh

# Or test manually
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
