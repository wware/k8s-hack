# K8s/GitOps book

This repository, along with `../gitops-lab` and `../gitops_reconciler`, form an arc:

- Start with understanding k8s and how it works
- Understand how gitops extends the pattern into the devops space
- Generalize the k8s/gitops pattern beyond k8s to other deployments

I'm interested in making this a book with reference to these repositories on GitHub.

## Table of Contents (draft outline)

### Part I -- Why Any of This Exists

1. **From Pet Servers to Cattle**
   - The old world: SSH in, hand-edit a config, restart a service, hope you remember what you did
   - Snowflake servers and the "it works on my machine (in production)" problem
   - Configuration drift: why two "identical" servers never stay identical
   - The rise of automation: Puppet/Chef/Ansible as the first wave of "describe, don't do"
   - Brief history: physical servers → VMs → containers → orchestrated containers

2. **The Security Case for Systematized Infrastructure**
   - Why ad-hoc ops was always risky, and why it's *more* risky now
   - Bad actors have industrialized: automated scanning, supply-chain attacks, ransomware-as-a-service
   - Manual changes = unaudited changes: no diff, no review, no rollback
   - Version-controlled infrastructure as a security control, not just a convenience
   - Principle of least surprise: if it's not in git, it shouldn't be running
   - Preview of where this book is headed: version control as the spine connecting every chapter

### Part II -- Containers Before Orchestration

3. **Docker: Packaging Reality**
   - What a container actually is (namespaces, cgroups, union filesystems) -- just enough to demystify it
   - Images vs. containers; the Dockerfile as a recipe, not a script
   - A short history: chroot → LXC → Docker's breakout moment (2013) → OCI standardization
   - Why "works in the container" is a stronger claim than "works on my machine"
   - Learning links: Docker's own "Get Started" guide, *The Docker Book*, OCI spec overview

4. **Docker Compose: Orchestration's Training Wheels**
   - Multi-container apps without a cluster: `docker-compose.yml` as a mini-manifest
   - What Compose gets right: local dev parity, one-command spin-up, readable YAML
   - What Compose can't do: multi-host scheduling, self-healing across machines, rolling updates with real health gating, no built-in service mesh/networking across hosts
   - Walkthrough: this repo's `docker-compose.yml` (FastAPI + Postgres) as the running example
   - Why Compose is the right tool until it isn't -- and how you'll feel the ceiling

### Part III -- Kubernetes Fundamentals *(k8s-hack)*

5. **What Kubernetes Actually Is**
   - The control loop idea: desired state vs. observed state, reconciled continuously
   - Why this is fundamentally different from "run a script when something changes"
   - Anatomy of a cluster: API server, etcd, scheduler, controllers, kubelet -- at a glance
   - Mapping Compose concepts onto K8s: `docker-compose.yml` → Deployment + Service + ConfigMap + Secret

6. **Your First Deployment**
   - `./start.sh` and the "aha" moment: containers + orchestration, not magic
   - Deployments, Services, and the separation of "what runs" from "how it's reached"
   - StatefulSets and why databases aren't just "a Deployment with a volume"
   - Hands-on: deploying the toy API + Postgres from this repo
   - The YAML files as promises kept: walking every file in deployment order --
     ConfigMap, Secret, PVC, StatefulSet, headless Service, Deployment, Service
     -- as the visible evidence of one guarantee apiece, not just boilerplate
   - Where the promises run out: a bare StatefulSet's guarantees stop at
     identity and storage -- nothing about replication, failover, or backups.
     That gap is part of Chapter 9's subject

7. **Self-Healing and Scaling**
   - Deleting a pod on purpose and watching Kubernetes notice
   - Declarative intent: "2 replicas" as a standing order, not a one-time command
   - Horizontal scaling for stateless apps vs. why stateful scaling is hard
   - Load balancing across replicas, observed via logs

8. **Configuration, Secrets, and Storage**
   - ConfigMaps and Secrets: config outside the image, decoupled from rebuilds
   - PersistentVolumeClaims: storage that outlives the pod
   - Hands-on: editing config, restarting pods, confirming the new values land

9. **When *Not* to Use Kubernetes**
    - Referenced doc: `WHY_KUBERNETES.md`
    - Operational cost: what running K8s well actually requires (a team, not a weekend)
    - Signs you don't need it yet, and signs you're about to

10. **Infrastructure as Code, Take One: Pulumi**
    - Same resources, different syntax: YAML manifests vs. a real programming language
    - Type checking, reusable modules, and why this starts to matter at scale
    - When Pulumi (or Terraform, CDK, etc.) earns its complexity over plain manifests

11. **Observability Basics: Logging**
    - Referenced doc: `LOGGING.md`
    - stdout → DaemonSet → aggregator (Loki or similar) as the modern evolution of syslog
    - Structured JSON logs and why correlation across services depends on them

12. **Authentication and Authorization Patterns**
    - Referenced doc: `AUTH.md`
    - Where auth lives in a K8s-deployed app vs. where cluster RBAC lives -- two different concerns often confused

### Part IV -- GitOps: Extending the Pattern into DevOps *(gitops-lab)*

13. **Git as the Control Plane**
    - The inversion: `kubectl apply` (push) vs. "commit and let the cluster notice" (pull)
    - Why pull-based deployment is more secure and more auditable
    - ArgoCD's reconciliation loop, mapped back onto the control-loop idea from Chapter 5
    - Hands-on: kind + ArgoCD + Gitea local setup

14. **Drift Detection and Self-Healing at the Fleet Level**
    - Manually scaling a Deployment and watching ArgoCD flag it OutOfSync
    - Enabling self-heal: the cluster actively defends the git-declared state
    - Cluster state vs. git state as a permanent, visible diff -- not a one-time audit

15. **Multi-Environment Deployment Without the Copy-Paste**
    - ApplicationSets: one template, many environments (dev/staging/prod)
    - Why hand-maintained per-environment YAML rots, and how templating prevents it

16. **Autoscaling on Real Signal: KEDA**
    - CPU-based autoscaling's blind spot: bursty, queue-driven workloads
    - Scale 0→N on queue depth, and back to 0 -- paying for actual work, not idle capacity
    - Hands-on: RabbitMQ + KEDA-scaled workers

17. **The Cost/Complexity Decision**
    - Option A: Single-box autoscaling -- cheapest, simplest, no HA
    - Option B: AWS Auto Scaling Groups -- cheap, AWS-native, scaling lag
    - Option C: Real EKS -- expensive, complex, industry-standard, justified past a certain team/scale threshold
    - A decision framework, not a default answer: matching infrastructure to actual need (echoes Chapter 9)

18. **Side Quests**
    - EKS emulation on a home LAN (kubeadm + MetalLB): learning multi-node mechanics without AWS bills
    - Queue-based scaling as a portable pattern (SQS/Kafka/Redis -- same idea everywhere)

### Part V -- Beyond Kubernetes: Generalizing the Pattern *(gitops_reconciler)*

19. **GitOps Without a Cluster**
    - The insight: Kubernetes just happens to supply a free, live, self-diffing control plane
    - Every other target (Terraform, Pulumi, CloudFormation, Compose, a Raspberry Pi) needs the reconciliation loop built explicitly
    - Introducing the `BackEnd` ABC: `apply()`, `destroy()`, `get_outputs()` -- three methods, one shared shape

20. **Design Decisions, and Why They Were Made That Way**
    - Why there's no `plan()`/dry-run method: idempotent `apply()` already pays the diff cost
    - Why "refresh" logic lives inside each backend, not the shared interface
    - Why there's no human-approval gate on the interface itself (and where that gate *does* belong)
    - Why pull-vs-push scheduling is a wrapper concern, and convergence is a backend concern -- keeping layers honest

21. **Credentials and Blast Radius**
    - Why the reconciler should run on a separate control machine from what it manages
    - Short-lived STS/instance-role credentials over static keys
    - The exception that proves the rule: a Raspberry Pi managing itself, where there's no privilege boundary worth protecting

22. **Progressive Delivery Without New Abstractions**
    - Staging tracks `:latest`; production pins to a validated SHA
    - The promotion script: reading staging's last-applied SHA, rewriting prod's pin, committing
    - Why staging and prod never talk to each other directly -- git remains the only shared state
    - This is the same pattern as Chapter 14's drift detection, just with a human-gated promotion step inserted

### Part VI -- Putting It Together

23. **One Pattern, Three Substrates**
    - Recap: declare → observe → reconcile, instantiated in Docker Compose, Kubernetes/ArgoCD, and the generic reconciler
    - A comparison table: what each substrate buys you and what it costs
    - Choosing a substrate for a new project: a checklist derived from Chapters 10 and 17

24. **What Still Isn't Covered**
    - Secrets management at scale (External Secrets, SOPS)
    - Full observability stack (Prometheus, Grafana, Loki, AlertManager)
    - RBAC, network policies, image scanning, supply-chain attestation
    - Pointers for further reading, framed as the security posture argued for in Chapter 2

### Appendices

- **A. Command Reference** -- `docker`, `docker compose`, `kubectl`, `pulumi`, `argocd` cheat sheets
- **B. Glossary** -- reconciliation loop, desired state, drift, StatefulSet, ApplicationSet, etc.
- **C. Repository Map** -- how `k8s-hack`, `gitops-lab`, and `gitops_reconciler` relate, with a suggested reading order per chapter

## Trajectory for the book

Eventually I'll want something like a printed book you can hold in your hand,
with an ISBN, and a corresponding e-book in the Kindle store. For now it's more
practical to think in terms of an 8.5x11 home-made book that gets spiral-bound
at Staples. The spiral-bound book can be produced in small quantities, shared,
marked up by friendly readers.

I want to avoid AI-sounding language (em-dash, "load bearing', etc) and writing
tone that's very different from mine. Probably I'd have Claude write a preliminary
draft of the book, then rewrite pieces in my own voice over time, before going
to anything like a real printing or publishing.

But em-dashes and "load-bearing" are symptoms, not the disease. The deeper tell is
usually: every section has the same rhythm (setup / insight / payoff),
everything is hedged with "it's worth noting," and abstractions get restated
instead of just used. So later we will look at these structural patterns and try
to break them up.

