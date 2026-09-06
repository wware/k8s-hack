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
     That gap is Chapter 9's subject

7. **Self-Healing and Scaling**
   - Deleting a pod on purpose and watching Kubernetes notice
   - Declarative intent: "2 replicas" as a standing order, not a one-time command
   - Horizontal scaling for stateless apps vs. why stateful scaling is hard
   - Load balancing across replicas, observed via logs

8. **Configuration, Secrets, and Storage**
   - ConfigMaps and Secrets: config outside the image, decoupled from rebuilds
   - PersistentVolumeClaims: storage that outlives the pod
   - Hands-on: editing config, restarting pods, confirming the new values land

9. **Infrastructure as Code, Take One: Pulumi**
   - Same resources, different syntax: YAML manifests vs. a real programming language
   - Type checking, reusable modules, and why this starts to matter at scale
   - When Pulumi (or Terraform, CDK, etc.) earns its complexity over plain manifests

10. **When *Not* to Use Kubernetes**
    - Referenced doc: `WHY_KUBERNETES.md`
    - Operational cost: what running K8s well actually requires (a team, not a weekend)
    - Signs you don't need it yet, and signs you're about to

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
    - A decision framework, not a default answer: matching infrastructure to actual need (echoes Chapter 10)

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

## Writing Chapter 6 (Your First Deployment) in Will's voice

### `./start.sh`: containers + orchestration, not magic

The shell script `start.sh` establishes the prerequisites you'll need for a
small local Kubernetes setup with Minikube. Simply running this script and
watching the messages it produces is illuminating.  Useful, important stuff is
happening, but there is nothing incomprehensible going on.

### Deployments, Services, and the separation of "what runs" from "how it's reached"

Open `deployment.yaml` and `service.yaml` side by side. They're two different
objects because they answer two different questions.

```yaml
# deployment.yaml, abbreviated
kind: Deployment
spec:
  replicas: 2
  template:
    spec:
      containers:
        - name: api
          image: k8s-toy-api:local
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
            ... etc
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 256Mi
```

`deployment.yaml` answers "what should be running." It says: run 2 copies of
the `k8s-toy-api:local` image, give each one a container port of 8000, give
it these environment variables, and check `/api/v1/healthz` periodically to
decide if it's alive and ready. That's it. Nothing in this file knows or
cares how anything outside the pod finds these containers. A Deployment's
job ends at "keep this many copies of this container running and healthy."

```yaml
# service.yaml, abbreviated
kind: Service
spec:
  type: NodePort
  selector:
    app: toy-api
  ports:
    - port: 8000
      targetPort: 8000
      name: http
```

`service.yaml` answers "how do I reach it." The `toy-api` Service doesn't
run any code -- it's a stable address and a routing rule. It has a
`selector: app: toy-api`, meaning it forwards traffic to whatever pods
currently carry that label, whatever their names or IPs happen to be at
the moment. Pods come and go -- they get deleted and recreated with new
names and new IPs constantly, that's normal -- but the Service's name and
address don't change. Anything that wants to talk to the toy API talks to
the Service, never to a specific pod.

This split matters because the two things change on different schedules.
Scaling the Deployment from 2 replicas to 5, or rolling out a new image,
happens often and shouldn't require touching how the app is addressed.
Meanwhile the Service's job -- routing to whatever's currently healthy -- has
to keep working through all of that churn without being told about it
directly. Separating "what runs" from "how it's reached" is what makes
that possible.

The `toy-api` Service in this repo is `type: NodePort`, which opens a port
on the Minikube node itself (something in the 30000-32767 range, allocated
automatically) so you can hit the API from outside the cluster without
port-forwarding. `postgres-service.yaml` uses `type: ClusterIP` instead,
with `clusterIP: None` -- that's a headless Service, and it exists for a
different reason covered in the next section.

One more thing worth flagging in `deployment.yaml`: it sets
`imagePullPolicy: IfNotPresent` against the tag `k8s-toy-api:local`, with a
comment that the image is built locally and never pulled from a registry.
That combination -- a mutable tag plus "don't repull if you already have
something under this name" -- is a known trap: rebuild the image, run
`minikube image load` again, and it can silently no-op if a running pod is
still holding the old image under that same tag. The fix is to scale the
Deployment to zero, let the old pods actually go away, then reload the
image and scale back up. Real deployments avoid the whole problem with
immutable, content-addressed tags -- a git SHA or build digest -- so the
tag itself is proof of what's running, not just a label that might be stale.

### StatefulSets, and why databases aren't just "a Deployment with a volume"

The toy API is a Deployment. Postgres is a StatefulSet. They look almost
identical in the YAML -- same containers, same probes, same resource limits --
so it's worth being specific about why they're not interchangeable.

A Deployment's pods are disposable and identical. If you're running 2 replicas
of `toy-api` and one gets killed, Kubernetes starts a replacement with a new
name and a new IP, and nothing about the app cares which one you happen to be
talking to at a given moment -- that's exactly what the Service in the previous
section is for. The replicas don't have individual identities worth preserving.

Postgres can't work that way. It has exactly one replica here (`replicas: 1` in
`postgres-statefulset.yaml`), and it's bound to one specific
`PersistentVolumeClaim` -- `postgres-pvc`, defined separately in
`postgres-pvc.yaml`. A StatefulSet gives that one pod a stable name
(`postgres-0`) and reattaches the same volume to it every time it's recreated.
Delete `postgres-0` and Kubernetes brings back `postgres-0` again, not some
interchangeable replacement -- same name, same storage, same data.

```yaml
# postgres-pvc.yaml, abbreviated
kind: PersistentVolumeClaim
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi

# postgres-service.yaml, abbreviated
kind: Service
spec:
  ports:
    - port: 5432
      targetPort: 5432
      protocol: TCP
      name: postgres
  clusterIP: None

# postgres-statefulset.yaml, abbreviated
kind: StatefulSet
spec:
  serviceName: postgres
  replicas: 1
  template:
    spec:
      containers:
        - name: postgres
          image: postgres:16-alpine
          ports:
            - containerPort: 5432
              name: postgres
          volumeMounts:
            - name: postgres-storage
              mountPath: /var/lib/postgresql/data
      volumes:
        - name: postgres-storage
          persistentVolumeClaim:
            claimName: postgres-pvc
```

That's what "set" means here. It's easy to hear "StatefulSet" and picture
something structurally different from a Deployment. But it's the same idea, a
controller managing a group of pods from one template. The difference is that
the pods aren't just "N copies of this template," they're ordinal slots:
`postgres-0`, and if this were scaled to 3 replicas, `postgres-1` and
`postgres-2` alongside it, each with its own PersistentVolumeClaim and created
and torn down in order, 0 before 1 before 2. A Deployment's pods get random
suffixes because their identity doesn't matter. A StatefulSet's pods are
numbered because the number *is* the identity. It's how the same pod keeps
finding its way back to the same volume every time it's recreated. This repo
only ever runs one replica, so you only ever see `postgres-0`, but the indexing
is there waiting for the day you need `postgres-1`.

That's also why `postgres-service.yaml` is headless (`clusterIP: None`).
A normal Service load-balances across whatever pods match its selector,
but that won't work for a database you need to address specifically
rather than "any of the following." A headless Service instead gives each
StatefulSet pod its own stable DNS name, so other things in the cluster
can find `postgres-0` by name if they need to, not just "postgres,
whichever one answers."

Stateless replicas can be identical because there's nothing to lose by throwing
one away and starting fresh. A database can't be treated that way. Its whole
value is the data sitting on disk, tied to one specific process. The
StatefulSet exists to preserve exactly that identity: this pod, this volume,
every time.

### Hands-on: deploying the toy API + Postgres from this repo

`start.sh` runs all of the above, in the order it has to happen. Worth
reading top to bottom once, because the order isn't arbitrary:

1. `docker build -t k8s-toy-api:local .` -- build the image
2. `minikube image load k8s-toy-api:local` -- get that image into
   Minikube's own image store, since Minikube runs its own Docker daemon
   separate from your host's
3. Delete anything already deployed under these filenames, ignoring
   errors if nothing's there yet
4. Apply the ConfigMap and Secret first, then the PVC, then the Postgres
   StatefulSet and Service, then the API's Deployment and Service -- config
   before the things that consume it, storage before the thing that
   claims it, database before the app that connects to it
5. `kubectl wait --for=condition=ready pod -l app=postgres --timeout=120s`
   -- block here until Postgres actually reports ready via its
   `readinessProbe`, not just "created"
6. Same wait for the API pods
7. Print `kubectl get pods,svc,pvc` so you can see everything that exists
8. Run `test-api.sh` -- a full CRUD pass against the live API, over its
   NodePort or `localhost:8000` depending on what's running
9. Print instructions for reaching the API yourself afterward

Run it and read the output as it happens rather than skipping to the end.
The `⏳ Waiting for PostgreSQL to be ready` line means what it says --
until Postgres's own `pg_isready` check passes, nothing else is allowed to
proceed, because the API pods talk to Postgres on startup and gain nothing
by starting before there's a database to talk to. When it works, the
whole thing looks almost boring: build, load, apply, wait, test, done.
That's the point. There's no step in here that isn't something you could
explain to someone else in one sentence.

### The YAML files as promises kept

Go back through every file `start.sh` applied, but read them a second time
with a different question in mind: not "what does this field do" but "what
is Kubernetes promising to keep true, and for how long."

`postgres-configmap.yaml` and `postgres-secret.yaml` are the promise that
changing the database name or password never means touching `app.py` or
rebuilding an image -- config and code are separable, permanently, by
construction. `postgres-pvc.yaml` is the promise that the 1Gi of storage it
requests will still hold the same data no matter what happens to the pod
sitting on top of it. `postgres-statefulset.yaml` is the promise, covered
above, that `postgres-0` and its volume stay paired through every reschedule.
`postgres-service.yaml`'s headless setup is the promise that something can
always find that specific pod by name, not just "postgres, whichever one
answers." `deployment.yaml`'s probes are the promise that a container which
stops answering gets pulled out of rotation and replaced without anyone
watching for it. `service.yaml` is the promise that the address for reaching
the API doesn't move even while the pods behind it are constantly being
replaced.

None of this is a new set of facts -- it's the same seven files already
walked through above. What changes is the lens: every field in every one of
these manifests exists because it's holding up a specific guarantee, and
once you can name the guarantee, the YAML stops looking like configuration
syntax and starts looking like a list of promises with the evidence
attached.

It's also worth being honest about where those promises stop. A bare
StatefulSet's guarantees are exactly two: stable identity, stable storage.
That's all `postgres-statefulset.yaml` is promising. It says nothing about
replication, nothing about failover if the node running `postgres-0` dies,
nothing about backups. Real production databases close that gap with an
Operator sitting on top of the StatefulSet -- more on that later.

## Writing Chapter 7 (Self-Healing and Scaling) in Will's voice

### Deleting a pod on purpose and watching Kubernetes notice

With the toy API and Postgres both running, list the current pods and
delete one of the `toy-api` ones directly:

```shell
kubectl get pods -l app=toy-api
kubectl delete pod toy-api-6cf667676b-9477m   # use a name from your own output
```

Then watch what happens next:

```shell
kubectl get pods -l app=toy-api -w
```

A replacement pod appears within a second, in `Running` but not yet `1/1`
ready, and reaches `1/1` a few seconds later once its readiness probe
passes:

```
NAME                       READY   STATUS    RESTARTS      AGE
toy-api-6cf667676b-fwzzq   0/1     Running   0             1s
toy-api-6cf667676b-n5j7p   1/1     Running   1 (22h ago)   22h
toy-api-6cf667676b-fwzzq   1/1     Running   0             7s
```

The pod you deleted is gone for good -- it's a new name, not a
resurrection. Confirm you're back to the expected replica count and both
pods report ready:

```shell
kubectl get pods -l app=toy-api
```

Nobody ran a script to make that happen. Nothing in `deployment.yaml` says "if
a pod dies, start another one". That instruction doesn't need to exist
anywhere. It says `replicas: 2`, and the Deployment controller's whole job is
making the cluster's actual pod count match that number, continuously, forever,
regardless of why the count drifted. You deleting a pod on purpose and a node
crashing and killing a pod by accident look identical from the controller's
point of view: the observed state stopped matching the desired state, so it
acts.

### Declarative intent: a standing order, not a one-time command

This is different from a script triggered by a commit hook or a CI/CD pipeline.
A shell script that runs `docker run` twice starts two containers and then it's
done. Its job is finished the moment the command returns. `replicas: 2` in a
Deployment spec isn't a command that finishes; it's a standing order the
control loop keeps re-checking against reality, indefinitely, until someone
changes the spec. Nothing "runs" it on a schedule. It's just always being
checked.

That's why deleting a pod gets you a replacement but deleting the
Deployment itself does not -- the standing order is gone, so there's
nothing left to re-check against.

### Scaling out: easy for the API, meaningless for the database

Scaling the API is a one-line change in intent:

```shell
kubectl scale deployment/toy-api --replicas=4
```

Four pods, each an independent copy of the same stateless process, each
capable of answering any request identically, because none of them are
holding onto anything the others don't have. The Service's label selector
picks up the two new pods automatically -- nothing about the Service
definition changes.

Trying the equivalent on Postgres exposes exactly why "stateful scaling"
isn't a smaller version of the same problem:

```shell
kubectl scale statefulset/postgres --replicas=2
```

`postgres-1` comes up, `1/1` Ready, looking exactly as healthy as
`postgres-0`. But check what it's actually connected to:

```shell
kubectl exec postgres-1 -- psql -U postgres -d toyapi -c "SELECT * FROM items;"
```

```
 id | name | value
----+------+-------
(0 rows)
```

Empty. `postgres-1` isn't a replica of `postgres-0` with a copy of its
data -- it's a second, completely independent Postgres process that
happens to be running the same image. Prove it by inserting a row into
`postgres-1` and checking whether `postgres-0` ever sees it:

```shell
kubectl exec postgres-1 -- psql -U postgres -d toyapi -c \
  "INSERT INTO items (id, name, value) VALUES ('probe', 'from postgres-1', 777);"
kubectl exec postgres-0 -- psql -U postgres -d toyapi -c \
  "SELECT * FROM items WHERE id='probe';"
```

The insert succeeds against `postgres-1`. The `SELECT` against `postgres-0`
comes back empty: `(0 rows)`. They don't know about each other. Nothing in a
bare StatefulSet spec says "and also replicate the data between instances,"
because a StatefulSet's job stops at stable identity and stable storage, the
same two guarantees from the previous section, and not one guarantee more.
Getting actual replication requires either an application that knows how to
replicate itself (Postgres does, but it has to be configured to) or an Operator
that automates that configuration.  `replicas: 2` on a StatefulSet gets you two
databases, not one database with a backup.

Scale back down and confirm `postgres-0`'s data was never touched in the
first place:

```shell
kubectl scale statefulset/postgres --replicas=1
kubectl wait --for=condition=ready pod -l app=postgres --timeout=60s
kubectl exec postgres-0 -- psql -U postgres -d toyapi -c "SELECT * FROM items;"
```

```
  id   |    name     | value
-------+-------------+-------
 item1 | First Item  |   100
 item2 | Second Item |   200
```

Same two rows as before the experiment started. `probe` never existed as
far as `postgres-0` is concerned, because it never did -- it was inserted
into a different process's disk entirely, and that process is gone now
that `postgres-1` has been scaled away.

### Load balancing across replicas, observed via logs

Back on the API side, scale up again and send a batch of requests at the
Service, hitting its NodePort directly rather than any one pod:

```shell
kubectl scale deployment/toy-api --replicas=4
kubectl wait --for=condition=ready pod -l app=toy-api --timeout=60s

NODE_PORT=$(kubectl get svc toy-api -o jsonpath='{.spec.ports[0].nodePort}')
MINIKUBE_IP=$(minikube ip)
for i in $(seq 1 20); do
  curl -s -o /dev/null "http://${MINIKUBE_IP}:${NODE_PORT}/api/v1/items"
done
```

Then check each pod's own logs for how many of those twenty requests it
answered, using the `"items listed"` line that `list_items` logs on every
call:

```shell
for pod in $(kubectl get pods -l app=toy-api -o jsonpath='{.items[*].metadata.name}'); do
  count=$(kubectl logs "$pod" --since=60s | grep -c '"items listed"')
  echo "$pod: $count requests"
done
```

```
toy-api-6cf667676b-4bv8l: 6 requests
toy-api-6cf667676b-fwzzq: 2 requests
toy-api-6cf667676b-j867p: 6 requests
toy-api-6cf667676b-n5j7p: 6 requests
```

Every pod got some traffic, but not an even split. `kube-proxy` is
choosing a backend at random for each connection, not round-robining --
so with only twenty requests, some unevenness is expected, and it would
smooth out over a few thousand. The behavior worth internalizing isn't
"perfectly balanced" -- it's "any of these four processes can answer, and
the caller never had to know or care which one did."

## Writing Chapter 8 (Configuration, Secrets, and Storage) in Will's voice

### Editing a ConfigMap live, and finding the edge of "hot reload"

`postgres-config` holds the non-secret pieces of the database connection --
host, port, database name, username -- and `deployment.yaml` wires each one
into the API container as an environment variable via `configMapKeyRef`.
Patch the ConfigMap while the app is running:

```shell
kubectl patch configmap postgres-config --type merge \
  -p '{"data":{"POSTGRES_USER":"postgres_renamed"}}'
kubectl get configmap postgres-config -o jsonpath='{.data.POSTGRES_USER}'
```

```
postgres_renamed
```

The ConfigMap object shows the new value immediately. But check the same
variable inside an already-running pod:

```shell
POD=$(kubectl get pods -l app=toy-api -o jsonpath='{.items[0].metadata.name}')
kubectl exec "$POD" -- env | grep POSTGRES_USER
```

```
POSTGRES_USER=postgres
```

Still the old value. This is the edge of what a ConfigMap actually
promises: Kubernetes updates the object right away, but a container's
environment variables are set once, at container start, from whatever the
ConfigMap said at that moment -- nothing pushes changes into a running
process's environment afterward. `env` isn't a live view of the ConfigMap;
it's a snapshot taken once.

Getting the new value into the app means restarting the pods that read it:

```shell
kubectl rollout restart deployment/toy-api
```

Except in this case the new value is `postgres_renamed`, and Postgres was
never told that role exists -- `POSTGRES_USER` only sets up Postgres's own
initial role at first-ever startup, and `postgres-0` had already been
initialized long before this edit. Watch it happen in real time:

```shell
kubectl get pods -l app=toy-api -w
```

```
NAME                       READY   STATUS             RESTARTS
toy-api-6cf667676b-fwzzq   1/1     Running            0
toy-api-6cf667676b-n5j7p   1/1     Running            1 (22h ago)
toy-api-76c48f9b5c-5t9q6   0/1     CrashLoopBackOff   3 (17s ago)
```

Check why the new pod is unhappy:

```shell
kubectl logs toy-api-76c48f9b5c-5t9q6 --tail=5   # use your own new pod's name
```

```
asyncpg.exceptions.InvalidPasswordError: password authentication failed for user "postgres_renamed"
ERROR:    Application startup failed. Exiting.
```

Both old pods stay `1/1 Running` the entire time, and the Service keeps
answering `200` on every health check throughout:

```shell
NODE_PORT=$(kubectl get svc toy-api -o jsonpath='{.spec.ports[0].nodePort}')
MINIKUBE_IP=$(minikube ip)
curl -s -o /dev/null -w "%{http_code}\n" "http://${MINIKUBE_IP}:${NODE_PORT}/api/v1/healthz"
```

```
200
```

Nothing about the API went down. That's `RollingUpdate` doing exactly what
it's specified to do (`maxUnavailable: 25%`, `maxSurge: 25%` by default):
it won't remove an old, healthy pod until a new one proves itself ready,
and a pod stuck crash-looping never gets there. A bad config change here
fails safely -- loudly, in `kubectl get pods`, but without taking anything
down.

Revert and confirm the rollout completes cleanly this time:

```shell
kubectl patch configmap postgres-config --type merge \
  -p '{"data":{"POSTGRES_USER":"postgres"}}'
kubectl rollout restart deployment/toy-api
kubectl rollout status deployment/toy-api --timeout=60s
```

```
deployment "toy-api" successfully rolled out
```

Both pods have new names now -- the crash-looping one is gone, and so is
the previously-healthy old pod it never managed to replace, cleaned up in
the same rollout once a working replacement finally passed its
readiness probe.

### PersistentVolumeClaims: storage that outlives the pod

Chapter 6 covered why `postgres-pvc.yaml` exists -- the promise that data
survives independent of any particular pod. Worth actually watching that
promise get kept:

```shell
kubectl exec postgres-0 -- psql -U postgres -d toyapi -c "SELECT * FROM items;"
```

```
  id   |    name     | value
-------+-------------+-------
 item1 | First Item  |   100
 item2 | Second Item |   200
```

Now delete the pod and wait for its replacement:

```shell
kubectl delete pod postgres-0
kubectl wait --for=condition=ready pod -l app=postgres --timeout=60s
kubectl exec postgres-0 -- psql -U postgres -d toyapi -c "SELECT * FROM items;"
```

```
  id   |    name     | value
-------+-------------+-------
 item1 | First Item  |   100
 item2 | Second Item |   200
```

Same rows, before and after. The pod that answers the second query isn't
the same process as the one that answered the first -- it was deleted and
recreated in between -- but the StatefulSet reattached the same
`postgres-pvc` volume to the new `postgres-0`, so from the data's
perspective nothing happened. This is the actual mechanism behind "storage
outlives the pod": not magic persistence, just the same PVC getting
claimed again by whatever process the StatefulSet starts under that name
next.
