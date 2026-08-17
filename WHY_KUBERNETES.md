# Kubernetes: What It Is and Why It Exists

## 1. What Kubernetes Actually Is

Kubernetes (K8s) is a **distributed control system for running containers across a fleet of machines**. That's a more useful definition than "container orchestrator," because the orchestration part is really just the visible symptom of the underlying design: Kubernetes is fundamentally a *reconciliation engine*. You tell it what you want the world to look like (desired state), and a set of independent control loops continuously work to make reality match that description (actual state). Everything else — pods, services, deployments, autoscaling — is built on top of that one idea.

It descends directly from Google's internal systems, **Borg** and its successor **Omega**, which ran Google's production workloads for over a decade before Kubernetes was open-sourced in 2014. The lineage matters: Kubernetes wasn't designed by guessing what small companies might need — it's a distillation of lessons from running literally millions of containers across shared clusters, including things like priority-based preemption, bin-packing, and the operational reality that any node can die at any time.

## 2. The Core Design Philosophy

A few foundational decisions shape everything else in the system.

### 2.1 Declarative over imperative

You don't tell Kubernetes "start 3 containers." You tell it "there should be 3 replicas of this pod running," and it figures out the *how* — which nodes, in what order, what to do if one crashes. This is the single most important design decision in the whole system. Imperative scripts (start this, then that, then check if it worked, then retry) are brittle and don't compose. Declarative state plus a reconciliation loop is idempotent by construction: you can apply the same manifest a thousand times and get the same result, and the system self-heals from almost any failure without bespoke error-handling logic.

### 2.2 Control loops (the "operator pattern")

Nearly every component in Kubernetes follows the same pattern:

```
watch(desired_state, actual_state):
    diff = desired_state - actual_state
    if diff:
        take_action_to_reduce_diff()
    sleep briefly, repeat forever
```

The scheduler does this for pod placement. The replication controller does this for pod counts. The kubelet on each node does this for containers. This uniformity is deliberate — it means the system's failure modes are well understood and consistent, and it's why Kubernetes is *extensible*: anyone can write a new controller that watches some resource and reconciles it (this is the basis of the entire "operator" ecosystem — Postgres operators, cert-manager, etc.).

### 2.3 Everything is an API object, stored in one place

All cluster state — desired and observed — lives in **etcd**, a distributed key-value store using the Raft consensus algorithm. The API server is the only thing that talks to etcd directly; every other component (scheduler, controllers, kubelet, `kubectl`) only ever talks to the API server. This gives you a single consistent source of truth, a uniform audit/authorization choke point, and a clean extension model (Custom Resource Definitions are just new object types the API server knows how to store and watch).

### 2.4 The Pod, not the container, is the atomic unit

This trips people up coming from plain Docker. A Pod is a group of one or more containers that share a network namespace (same IP, same localhost) and optionally storage volumes, and are always scheduled together on the same node. Why not just schedule individual containers?

- **Sidecar pattern**: a log shipper, service mesh proxy (Envoy/Istio), or config-reloader often needs to live right next to your app container, sharing its network and filesystem, but should be independently versioned and restartable as its own image.
- **Tight coupling with independent lifecycles**: sometimes you want two processes that must colocate but can be updated/crash independently — the Pod abstraction gives you that without merging them into one image.
- **Simplifies networking**: the scheduler only needs to think about placement at the Pod granularity, and every Pod gets its own cluster-routable IP, which sidesteps the port-mapping mess of running many containers on one Docker host.

### 2.5 Immutable infrastructure, mutable desired state

Containers are treated as disposable. You don't patch a running container — you change the desired state (e.g., bump the image tag in a Deployment) and Kubernetes replaces pods to converge on it. This is what makes rolling updates, canaries, and rollbacks tractable: rollback is just "reapply the old desired state."

## 3. Why Not Just Docker Compose?

This is the right question to lead with, because Compose is a perfectly good tool — Kubernetes isn't a "better Compose," it's solving a different problem.

Docker Compose's job is: **define and run a multi-container application on one Docker host.** It's declarative for a single machine. That's its whole scope, and it's great at it for local dev and small single-server deployments.

Kubernetes's job is: **maintain a desired state for workloads across an arbitrary, changing set of machines, where any machine or process can fail at any time, and workload demand changes over time.** Concretely, things Compose has no real answer for:

| Concern | Docker Compose | Kubernetes |
|---|---|---|
| Multi-host scheduling | No — one host | Yes — scheduler bin-packs pods across the whole cluster |
| Self-healing | No (a crashed container restarts on the same host, if configured) | Yes — a dead node's pods get rescheduled elsewhere automatically |
| Horizontal autoscaling | No | Yes — Horizontal Pod Autoscaler, Cluster Autoscaler |
| Rolling updates / rollback | Manual/limited | Built-in, with configurable surge/unavailability and one-command rollback |
| Service discovery across hosts | No | Built-in DNS + virtual IPs (Services) that survive pod rescheduling |
| Load balancing | No | Built-in, integrates with cloud LBs |
| Declarative, git-ops-friendly state for a *fleet* | Partial | Yes — the whole point |
| Multi-tenant resource isolation/quotas | No | Namespaces, ResourceQuotas, LimitRanges |
| Secrets/config management at scale | Minimal | First-class objects (Secrets, ConfigMaps) with RBAC |
| Extensibility for new resource types | No | CRDs + controllers — this is how the entire cloud-native ecosystem plugs in |

The honest summary: **Compose describes an application; Kubernetes describes and continuously enforces a cluster.** If your entire deployment target really is "one box," Kubernetes is overkill and Compose (or even just `docker run` with a process supervisor) is the right tool — a lot of Kubernetes' complexity exists specifically to solve problems that only appear once you have more than one machine, changing load, or a team bigger than one person deploying independently. Kubernetes becomes worth its considerable operational overhead once you have: multiple machines, a need for zero/low-downtime deploys, workloads that need to survive hardware failure, autoscaling requirements, or multiple teams that need to share a cluster safely.

## 4. Core Architecture

### Control plane (the "brain," usually 1 set per cluster, often 3 nodes for HA)
- **kube-apiserver** — the front door; stateless REST API, all reads/writes to cluster state go through it
- **etcd** — the distributed, Raft-based data store holding all cluster state
- **kube-scheduler** — watches for unscheduled pods, assigns them to nodes based on resource requests, affinity/anti-affinity rules, taints/tolerations, etc.
- **kube-controller-manager** — runs the built-in control loops (node controller, replication controller, endpoint controller, etc.)
- **cloud-controller-manager** — the pluggable bit that talks to the specific cloud provider's APIs (this is where AWS/Azure/GCP differ — see below)

### Nodes (the "muscle," where your workloads actually run)
- **kubelet** — the agent on each node; watches the API server for pods assigned to its node and makes sure their containers are running (talks to the container runtime)
- **kube-proxy** — implements the Service networking abstraction on each node (traditionally iptables/IPVS rules, increasingly eBPF-based)
- **Container runtime** — anything implementing the Container Runtime Interface (CRI) — typically **containerd** or **CRI-O** today (Docker Engine itself was deprecated as a direct runtime in 2020; Docker-built images still work fine, since OCI image format is the actual standard)

### Key objects you build with
- **Pod** — smallest deployable unit (see 2.4)
- **Deployment** — manages a ReplicaSet of pods, gives you rolling updates/rollback
- **StatefulSet** — like a Deployment but for workloads needing stable identity/storage (databases, etc.)
- **DaemonSet** — ensures a pod runs on every (or a selected subset of) node — log collectors, node-level monitoring
- **Service** — a stable virtual IP + DNS name in front of a set of pods, decoupling "who's calling" from "which pod is currently answering"
- **Ingress / Gateway API** — L7 HTTP(S) routing into the cluster from outside
- **ConfigMap / Secret** — externalized configuration and sensitive values, injected as env vars or mounted files
- **Namespace** — a soft multi-tenancy boundary for organizing and isolating resources within one cluster
- **PersistentVolume / PersistentVolumeClaim** — an abstraction decoupling "I need 20Gi of storage" from the actual storage backend (EBS, Azure Disk, PD, NFS, etc.)

## 5. The Networking Model (worth understanding, since it's unusual)

Kubernetes mandates a flat network model via the Container Network Interface (CNI):

1. Every Pod gets its own cluster-wide routable IP.
2. Pods can reach all other pods without NAT, regardless of which node they're on.
3. Nodes can reach all pods without NAT.

This is a deliberate simplification versus Docker's default per-host NAT'd networking — it eliminates a whole class of port-mapping/NAT-traversal bugs, at the cost of needing a real network plugin (Calico, Cilium, AWS VPC CNI, Azure CNI, etc.) to actually implement it across hosts. Cilium in particular has become popular because it implements this at the eBPF level rather than iptables, which scales much better on large clusters.

## 6. Cloud Provider Differences (EKS vs AKS vs GKE)

The Kubernetes API itself is standardized (that's the point of the CNCF conformance program), so a Deployment manifest is portable everywhere. The differences are in **how the control plane is managed, default networking, node provisioning, and how deeply cloud-native services are integrated.**

### Amazon EKS
- Control plane is fully managed but historically felt the most "bolted on" — EKS shipped years after GKE and it shows in some rough edges (e.g., IAM integration for pods required an add-on, **IRSA — IAM Roles for Service Accounts**, rather than being native from day one).
- Default CNI is the **AWS VPC CNI**, which is notably different from most other CNIs: it assigns pods *real VPC IP addresses* out of your subnet's IP pool rather than an overlay network. This gives great performance and lets security groups/VPC flow logs work naturally on pods, but it means you can run out of IPs on nodes with small instance types (each ENI has a limited number of secondary IPs) — a very AWS-specific operational gotcha.
- Node provisioning: traditionally self-managed or "managed node groups" (still just EC2 ASGs under the hood); **Fargate** support lets you run pods without managing nodes at all (serverless, pay-per-pod).
- Karpenter (AWS-originated but now broader) is increasingly the preferred autoscaler over the older Cluster Autoscaler — it provisions right-sized nodes just-in-time rather than scaling predefined node group shapes.
- Generally requires the most manual assembly of surrounding pieces (logging, ingress controller, autoscaler) compared to the other two, though this gap has narrowed.

### Google GKE
- The most "native" implementation, unsurprisingly — Google wrote Kubernetes, and GKE was first to market (2015).
- **Autopilot mode** is the standout differentiator: a fully hands-off mode where you don't manage nodes at all — you submit pods, GKE handles node provisioning, sizing, and OS patching, and you're billed per-pod-resource rather than per-node. Standard mode (self-managed nodes) is still available for more control.
- Fastest to get new upstream Kubernetes features and the most mature release-channel model (rapid/regular/stable channels for control plane auto-upgrades).
- Networking uses **VPC-native clusters** by default now (alias IP ranges), conceptually similar to the AWS VPC CNI approach — pods get real VPC-routable IPs.
- Tightest integration with Google Cloud IAM via Workload Identity, generally considered the smoothest of the three for binding a pod's identity to a cloud IAM identity.

### Azure AKS
- Free control plane (no charge for the management plane itself, unlike EKS/GKE which charge a small hourly fee per cluster) — a real cost consideration if you run many small clusters.
- Two CNI choices with a real tradeoff: **kubenet** (pods get non-VPC-routable IPs, NAT'd out — conserves VPC IP space but adds complexity for anything needing direct pod routability) vs. **Azure CNI** (pods get real VNet IPs, similar to AWS/GCP's model, but consumes VNet address space faster). This choice is more front-and-center in AKS than the equivalent decision on the other two.
- Deep integration with Azure AD (Entra ID) for both cluster RBAC and workload identity.
- Historically had a reputation for being somewhat behind on newest Kubernetes minor versions and having more control-plane hiccups than GKE, though this has improved substantially in recent years.

### The general pattern across all three
- All three now offer some flavor of "serverless" / node-less pods (Fargate, Autopilot, and Azure's Container Apps / virtual nodes) — the industry direction is clearly toward hiding node management entirely.
- All three now default to (or strongly encourage) "VPC-native" pod networking rather than overlay networks, because overlay networks (like the classic Flannel VXLAN approach) add latency and complicate observability — this used to be a real differentiator and has mostly converged.
- All three implement the identical Kubernetes API and CRDs, so tools like Helm, ArgoCD, cert-manager, and Prometheus all work identically regardless of provider — the differences are almost entirely at the infrastructure layer below the API, not in how you interact with Kubernetes itself.

## 7. Things Worth Flagging as "Gotchas" for Learners

- **Requests vs. limits** are the single most misunderstood concept for newcomers. `requests` is what the scheduler uses for bin-packing (guaranteed); `limits` is an enforced ceiling. Setting limits too low causes CPU throttling or OOMKills that look like mysterious crashes.
- **A Deployment does not equal high availability by itself** — you need `replicas > 1`, pod anti-affinity or topology spread constraints to avoid all replicas landing on one node/zone, and a PodDisruptionBudget to survive voluntary node maintenance.
- **`kubectl apply` is not transactional** across multiple objects — partial failures during a multi-resource apply are a real operational hazard, which is part of why GitOps tools (ArgoCD, Flux) with reconciliation loops of their own have become the standard deployment pattern rather than raw `kubectl apply` from CI.
- **etcd is the single point of catastrophic failure** for a cluster — it's why managed control planes (all three clouds) are worth the money for anything beyond a learning cluster; running your own HA etcd correctly is genuinely hard.

## 8. GitOps: Git as the Source of Truth

GitOps is really just Kubernetes' own control-loop idea, extended one level up the stack — and that's exactly why it fits so naturally. This is the answer to the gotcha flagged in section 7 — `kubectl apply` isn't transactional and has no memory of what should be true. GitOps is the ecosystem's answer: move the source of truth to something versioned, reviewable, and diff-able, and let a controller do continuously what `kubectl apply` only does once, on-demand, by a human who might forget.

### The core idea

Recall the reconciliation pattern: a controller watches desired state, compares it to actual state, and acts to close the gap. GitOps applies that same pattern, but changes *where the desired state lives*. Instead of desired state living only in "whatever's currently in the API server / etcd," it lives in a **git repository** — YAML manifests (or Helm charts, or Kustomize overlays) committed like code. A controller running *inside the cluster* continuously watches that repo and reconciles the live cluster to match it.

So the mental model becomes:

```
git repo (desired state, versioned, reviewed)
        ↓ (pull, not push)
GitOps controller in-cluster (ArgoCD / Flux)
        ↓ reconciliation loop
Live cluster state
```

### Why this fits Kubernetes specifically (and not, say, a pile of servers you SSH into)

- **Everything is already declarative YAML.** A Deployment manifest describes an end state, not a sequence of steps — so "the end state lives in git" is a small conceptual jump, not a paradigm shift. You can't meaningfully GitOps a bash deploy script the same way, because there's no idempotent "current state" to diff against.
- **The API server already exposes the mechanism for watching/diffing.** ArgoCD and Flux aren't inventing anything new — they're just another controller in the pattern from section 2.2 of the doc, watching an external source (git) instead of another API object.
- **Rollback is trivial and meaningful.** Because state is fully described declaratively, `git revert` + a resync *is* a rollback. Compare that to imperative infrastructure where "rollback" often means someone remembering what they typed.

### Pull vs. push — the important architectural distinction

Traditional CI/CD is **push-based**: your CI pipeline has cluster credentials and runs `kubectl apply` or `helm upgrade` from outside the cluster. GitOps flips this to **pull-based**: the controller lives inside the cluster and pulls from git — nothing outside the cluster needs write access to it at all.

This matters more than it sounds:

| | Push (traditional CI/CD) | Pull (GitOps) |
|---|---|---|
| Who needs cluster credentials | CI system (external) | Nobody external — controller is in-cluster |
| Drift detection | None — if someone runs `kubectl edit` by hand, CI never finds out | Continuous — controller notices and reverts, or flags it |
| Blast radius of a leaked CI credential | Full cluster access | None (no external write path exists) |
| Multi-cluster fan-out | Separate pipeline logic per cluster | Same controller pattern, just pointed at more repos/clusters |

The drift detection point is the one people underestimate: in a push model, the cluster's actual state and git can silently diverge forever (someone does a manual hotfix during an incident and never backports it). In a pull model, the controller *keeps re-asserting* git as truth on every reconcile cycle (typically every few minutes), so drift either gets auto-corrected or surfaced as an alert, depending on config.

### What ArgoCD / Flux actually add on top of "watch git, apply"

- **Diffing and visualization** — ArgoCD's UI shows you exactly what's out of sync between git and the live cluster before it acts (or you can require manual sync approval).
- **App-of-apps / multi-tenancy** — a repo structure where one root manifest fans out to many teams'/services' manifests, so a platform team can manage cluster-wide policy while app teams own their own subtrees.
- **Progressive delivery hooks** — integration with Argo Rollouts / Flagger for canary or blue-green rollouts driven by the same git-triggered reconciliation, with automatic rollback on metric regressions.
- **Multi-cluster fleets** — one GitOps controller (or one control plane like Argo CD's) can manage many clusters, each pointed at its own path/branch in the same repo, which is how "promote through dev → staging → prod" often gets modeled as a PR moving a change between directories.
