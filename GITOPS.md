# GitOps: Understanding the Architecture

## TL;DR

GitOps is Kubernetes' control-loop pattern applied one level up: instead of reconciling cluster state to etcd, you reconcile cluster state to git. The key architectural insight is that **all the active machinery lives in the Kubernetes cluster itself**—git is just a passive file store.

---

## Where Does the Active Machinery Live?

This is the question that clarifies the entire GitOps architecture.

**The git server is completely passive.** It stores YAML files. It serves them when asked. It has no idea Kubernetes exists. It doesn't poll anything, trigger anything, or apply anything.

**All the active work happens inside your Kubernetes cluster**, in a GitOps controller (ArgoCD, Flux, etc.) running as a pod:

```
Git server (passive storage)
    ↑
    | Controller polls every few minutes (git fetch)
    |
GitOps controller pod IN the K8s cluster (active)
    ↓
    | Compares, diffs, applies changes (kubectl apply)
    |
Cluster state
```

The GitOps controller is doing exactly what every Kubernetes controller does:
1. **Watch** a source of truth (in this case, a git repository)
2. **Compare** desired state (what's in git) to actual state (what's in the cluster)
3. **Reconcile** the difference (apply/update/delete resources)
4. **Repeat** continuously (typically every 1-5 minutes)

## The Symmetry with Kubernetes Itself

This is why GitOps fits so naturally with Kubernetes—it's the same pattern at a different layer:

| Layer | Passive Source of Truth | Active Controller | What It Reconciles |
|-------|-------------------------|-------------------|-------------------|
| Kubernetes core | etcd (key-value store) | kubelet, scheduler, replication controller | Pods, containers, node assignments |
| GitOps | git (file store) | ArgoCD / Flux | Deployments, Services, ConfigMaps, all K8s resources |

In both cases:
- The "source of truth" is **passive storage** (etcd, git)
- The **intelligence lives in the control loop**
- The system **continuously re-asserts** desired state
- **Drift is automatically detected** (and optionally corrected)

## Pull vs. Push: Why This Architecture Matters

Traditional CI/CD is **push-based**—your CI system has cluster credentials and runs `kubectl apply` from outside:

```
Git webhook triggers CI
    ↓
CI system (outside cluster, has write credentials)
    ↓ kubectl apply
Cluster (passive receiver)
```

GitOps is **pull-based**—the controller lives inside the cluster and pulls from git:

```
Git (read-only access needed)
    ↑
GitOps controller (inside cluster, already has access)
    ↓
Cluster
```

### Security Benefits

| Concern | Push (CI/CD) | Pull (GitOps) |
|---------|--------------|---------------|
| Who needs cluster write credentials | External CI system | Nobody external—controller is in-cluster |
| Blast radius of leaked credential | Full cluster write access | None (no external write path exists) |
| Credential rotation | Update CI secrets across all pipelines | Nothing to rotate externally |

### Operational Benefits

| Concern | Push (CI/CD) | Pull (GitOps) |
|---------|--------------|---------------|
| Drift detection | None—manual changes persist unnoticed | Continuous—controller notices and reverts or alerts |
| State visibility | "What did we last deploy?" (ask CI) | "What should be running?" (look at git) |
| Rollback | Re-run old pipeline or craft manual fix | `git revert` + wait for next reconcile |
| Multi-cluster | Separate pipeline logic per cluster | Same controller, pointed at different repos/branches |

The drift detection point is huge: in a push model, someone can `kubectl edit` during an incident and the change lives forever unless they remember to backport it to git. In a pull model, the controller re-applies git every few minutes—unauthorized changes either get auto-reverted or surface as an alert.

## One Repo, Many Clusters: The Inherent One-to-Many Model

Because git is passive and all the active machinery lives on the K8s side, GitOps is **inherently one-to-many**. A single git repository can be watched by any number of clusters, each running its own GitOps controller, each reconciling independently.

```
                    GitHub repo (one copy)
                          ↑
         ┌────────────────┼────────────────┐
         │                │                │
         │                │                │
    Prod cluster    Staging cluster   Local minikube
    (pulls main)    (pulls staging)   (pulls your-branch)
         │                │                │
    Each has its    Each reconciles  Each is completely
    own ArgoCD      independently    independent
```

This is fundamentally different from push-based CI/CD, where you need separate pipeline configurations, credentials, and orchestration for each environment.

### What This Enables

**1. Risk-free experimentation**

Spin up a local minikube cluster, install ArgoCD, point it at the same repo as production (or a fork, or a different branch), and watch what happens. Production has no idea you're doing this. You can:
- Test GitOps behavior without touching prod
- See exactly how production deployments work on your laptop
- Experiment with sync policies, auto-prune, self-heal settings
- Learn from production's repo structure in complete safety

**2. Branch-based environments**

Each cluster can watch a different branch:
- Production cluster watches `main`
- Staging cluster watches `staging` branch
- Dev cluster watches `dev` branch
- Your laptop watches `feature/experiment` branch

Changes flow through environments via PR merges between branches. This is GitOps' version of "promote through environments."

**3. Path-based multi-tenancy**

Multiple clusters can watch the same branch but different paths:

```
gitops-repo/
  clusters/
    prod/
      app-a.yaml
      app-b.yaml
    staging/
      app-a.yaml
      app-b.yaml
    dev/
      app-a.yaml
      app-b.yaml
```

- Prod cluster watches `clusters/prod/`
- Staging watches `clusters/staging/`
- Dev watches `clusters/dev/`

Promotion = copy files from `dev/` to `staging/` to `prod/` via PR.

**4. Multi-region deployments**

One repo, N regional clusters, all pulling the same manifests:

```
clusters/
  us-east-1/    # pulled by us-east-1 EKS cluster
  us-west-2/    # pulled by us-west-2 EKS cluster
  eu-west-1/    # pulled by eu-west-1 EKS cluster
```

Or all regions pull identical manifests from the same path, giving you deployment consistency across regions by default.

**5. Learning playground alongside production**

You can run a production setup and simultaneously run a local staging/dev setup to see what GitOps does with changes before they hit prod:

```bash
# On your laptop
minikube start
kubectl create namespace argocd
kubectl apply -n argocd -f \
  https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Point it at your fork or branch of the prod repo
# (prod watches main, you watch experiment-branch)
```

Now you have a complete GitOps learning environment that mirrors production's patterns without any risk.

### The Key Insight

With push-based CI/CD, adding another environment means:
- New pipeline configuration
- New credentials/secrets to manage
- New deployment logic to maintain
- New failure modes to debug

With GitOps, adding another environment means:
- Spin up another cluster (or use minikube)
- Install ArgoCD/Flux
- Point it at the repo (same one, different branch/path, or a fork)
- Done

The git repo doesn't care how many clusters are watching it. Each cluster independently reconciles what it sees in git. This "accidentally" gives you multi-cluster, multi-environment, and safe experimentation almost for free.

## What GitOps Controllers Actually Do

Beyond "watch git, run kubectl apply," controllers like ArgoCD and Flux add:

### 1. Smart Diffing
- Show exactly what's out of sync before applying
- Ignore expected differences (e.g., status fields, replicas changed by HPA)
- Respect resource-specific diff semantics (e.g., ConfigMap data changes)

### 2. Sync Policies
- **Auto-sync**: apply changes immediately when git updates
- **Manual sync**: require human approval (common for production)
- **Self-healing**: revert manual `kubectl` changes back to git
- **Pruning**: delete resources removed from git (dangerous, usually opt-in)

### 3. Multi-Tenancy ("App of Apps")
A repo structure where one root manifest fans out to many apps:

```
apps/
  app-of-apps.yaml        # Root Application, points to everything below
  platform/
    ingress-nginx.yaml
    cert-manager.yaml
  team-a/
    service-1.yaml
    service-2.yaml
  team-b/
    service-3.yaml
```

Platform team manages `platform/`, app teams own their own directories. One GitOps controller watches the root.

### 4. Progressive Delivery
Integration with Argo Rollouts or Flagger for canary/blue-green deployments:
- Git commit triggers new version
- Controller deploys canary (e.g., 10% traffic)
- Monitors metrics (error rate, latency)
- Auto-promotes or auto-rolls back based on metrics

### 5. Multi-Cluster Orchestration
One ArgoCD instance can manage many clusters:

```
clusters/
  dev/
    app.yaml
  staging/
    app.yaml
  prod/
    app.yaml
```

Promotion = PR that copies `staging/app.yaml` to `prod/app.yaml`. Same GitOps controller applies to different clusters.

## ArgoCD vs. Flux

Both implement the same pull-based model. Key differences:

| Feature | ArgoCD | Flux |
|---------|--------|------|
| UI | Rich web UI with diff viewer, sync controls | No UI (CLI + Grafana dashboards) |
| Architecture | Single controller pod | Toolkit of specialized controllers (source-controller, kustomize-controller, helm-controller) |
| CRDs | `Application` (one CRD for everything) | Multiple (`GitRepository`, `HelmRelease`, `Kustomization`) |
| Helm support | Native, with UI | Via helm-controller |
| Multi-cluster | Built-in (one ArgoCD manages many clusters) | Separate Flux install per cluster |
| Adoption | Wider (especially for multi-cluster) | Strong in Flux v2, favored by some for modularity |
| Complexity | Heavier (needs Redis, Dex for SSO) | Lighter (just controllers) |

**Rule of thumb**: ArgoCD if you want a UI and multi-cluster from one control plane. Flux if you want minimal overhead and like the GitOps Toolkit's composability.

## Bootstrapping: GitOps-ing the GitOps Controller

Chicken-and-egg problem: how do you GitOps the deployment of ArgoCD/Flux itself?

### ArgoCD Approach
1. Install ArgoCD manually once: `kubectl apply -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml`
2. Create an ArgoCD `Application` that points to a git repo containing... ArgoCD's own configuration
3. From then on, updates to ArgoCD config live in git and ArgoCD manages itself

### Flux Approach
`flux bootstrap` CLI does this in one command:
1. Installs Flux controllers into the cluster
2. Creates a `GitRepository` and `Kustomization` pointing at your repo
3. Commits Flux's own manifests to that repo
4. Flux takes over managing itself from git

Both achieve the same end: after initial bootstrap, the GitOps controller's own config lives in git and is reconciled like everything else.

## Secrets in Git: The Problem and Solutions

**Never commit plaintext secrets to git.** But you need secrets defined declaratively alongside your apps. Solutions:

### 1. Sealed Secrets (Bitnami)
- Encrypt secrets locally with a public key
- Commit encrypted `SealedSecret` to git
- Controller in-cluster decrypts with private key and creates real `Secret`
- Pro: Simple, no external dependencies
- Con: Key rotation is manual, no audit trail of who decrypted what

### 2. External Secrets Operator
- Store secrets in external vault (AWS Secrets Manager, HashiCorp Vault, Azure Key Vault)
- Commit `ExternalSecret` to git, which references the vault path
- Controller fetches from vault and creates `Secret`
- Pro: Secrets never in git at all, vault handles rotation/auditing
- Con: Dependency on external system, more moving parts

### 3. SOPS (Mozilla)
- Encrypt individual fields in YAML with age or PGP keys
- Commit encrypted YAML to git
- Flux `Kustomization` has native SOPS support, decrypts on apply
- Pro: Familiar YAML workflow, field-level encryption
- Con: Key management, not ArgoCD-native (needs plugin)

**Recommendation**: External Secrets Operator for production (proper vault + audit), Sealed Secrets for learning/small teams.

## Common Pitfalls

### 1. Not Handling Drift Correctly
- **Auto-sync + self-heal**: cluster always matches git (dangerous if misconfigured)
- **Manual sync**: drift accumulates, defeats the purpose
- **Middle ground**: auto-sync with Slack/email alerts on out-of-sync, manual approval for prod

### 2. Pruning Resources Without Care
If you enable auto-prune and remove a Deployment from git, GitOps **deletes it from the cluster**. Great for true GitOps, catastrophic if someone refactored the repo structure and didn't mean to delete anything.

### 3. Not Separating App Config from GitOps Config
Don't put ArgoCD `Application` manifests in the same repo as app code—makes it hard to manage multi-env (dev/staging/prod) without complex branching.

**Better structure**:
- `app-repo`: your app code + Dockerfile
- `gitops-repo`: K8s manifests, Helm charts, ArgoCD Applications

CI builds image → updates `gitops-repo` image tag → GitOps applies.

### 4. Forgetting the Controller Needs Git Access
If your git repo is private, the GitOps controller needs credentials (SSH key or token). Commonly done via a `Secret` containing SSH private key, referenced by the `Application` or `GitRepository`.

### 5. Image Tag `latest` Defeats Declarative State
If your Deployment uses `image: myapp:latest`, git can't tell you what's actually deployed—two clusters with identical manifests might run different images. **Always use immutable tags** (`myapp:v1.2.3` or `myapp:sha-abc123`).

## When NOT to Use GitOps

GitOps isn't always the right answer:

- **Very early prototyping**: `kubectl apply` from laptop is faster for tight iteration
- **Secrets-heavy, vault-light**: if you have many secrets and no proper vault, GitOps secret management is painful
- **Single developer, single cluster**: the overhead might not pay off
- **Stateful workloads with manual intervention**: if your deploy process involves "run this SQL migration, wait, check, then deploy," pure GitOps won't capture that workflow (though you can combine GitOps for the manifests with manual steps for data)

GitOps shines when you have: multiple environments, multiple team members, compliance/audit requirements, or a need to recover quickly from "someone `kubectl`'d something in production and now it's broken."

## Hands-On: Try It Yourself

### Quick Start with ArgoCD on Minikube

```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for it to be ready
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

# Access the UI (password is the argocd-initial-admin-secret)
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Get password: kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Login: https://localhost:8080 (admin / <password from above>)
```

### Create an Application

Point ArgoCD at this repository:

```yaml
# argocd-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: toy-api
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/wware/k8s-hack
    targetRevision: main
    path: .
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    automated:
      prune: false
      selfHeal: false
```

```bash
kubectl apply -f argocd-app.yaml
```

Now:
1. Edit a manifest in the repo (e.g., change replicas in `deployment.yaml`)
2. Commit and push
3. Watch ArgoCD detect the diff (refresh in UI or wait ~3 min)
4. Click "Sync" to apply

### Experiment with Drift

```bash
# Manually change replicas
kubectl scale deployment/toy-api --replicas=10

# ArgoCD UI will show "OutOfSync"
# If selfHeal: true, it reverts back to git's value
# If selfHeal: false, it alerts but doesn't auto-fix
```

## Next Steps

- Read [ArgoCD Best Practices](https://argo-cd.readthedocs.io/en/stable/user-guide/best_practices/)
- Read [Flux documentation](https://fluxcd.io/docs/)
- Try [GitOps Toolkit](https://fluxcd.io/flux/components/) to understand Flux's modular architecture
- Explore [Argo Rollouts](https://argoproj.github.io/argo-rollouts/) for progressive delivery
- Watch [GitOps Guide to the Galaxy](https://www.youtube.com/playlist?list=PLj6h78yzYM2P8S2D0E2YFLS2NjHK0K_sD) (great video series)

---

The key insight: **GitOps is not magic—it's the same reconciliation pattern you already learned about Kubernetes, just pointed at git instead of etcd.** Once you see that, the entire architecture clicks into place.
