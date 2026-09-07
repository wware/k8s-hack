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

## Writing Chapter 1 (From Pet Servers to Cattle) in Will's voice

### SSH in, hand-edit, restart, hope

The old workflow doesn't need much reconstruction because most people who'd
pick up this book have lived some version of it: `ssh` into the box, `vim`
the config file, restart the service, watch the logs scroll by for a
minute to confirm nothing's on fire, log out. It works. It's also the
entire deployment process, in the sense that nothing about it exists
anywhere except in that terminal session and, if you're lucky, in
whatever you remember about it later.

That's the part worth sitting with, not the SSH command itself. The
change you just made -- what config value moved, why, what it was before
-- lives in exactly one place: your memory of doing it, maybe backed by a
comment you left in the file, if you left one. Six months later, "why is
this set to 30 instead of the default of 10" has one honest answer: ask
whoever did it, if they still work there, if they remember.

### Snowflakes, and the gap between "works" and "works reliably"

Do this enough times, on enough servers, and every server drifts into
being slightly different from every other one -- not because anyone
planned it that way, but because each one accumulated its own particular
sequence of hand-applied fixes, each one applied under time pressure, to
whatever that specific box happened to need at whatever moment someone
was looking at it. Server A got a kernel parameter tuned during an
incident eighteen months ago. Server B didn't, because it wasn't part of
that incident. Nobody wrote either change down anywhere both servers
would show up.

"It works on my machine" is the famous version of this joke, but the
sharper version, and the one that actually costs money, is "it works on
this production server" -- meaning specifically this one, the one that's
been hand-tuned by three different people responding to three different
emergencies, and not the one you just brought up from the same base image
that's supposedly identical to it. Two servers built from the same
starting point stop being identical the first time someone touches one of
them by hand and not the other. There's no mechanism forcing them back
into agreement, so unless someone is deliberately auditing for drift --
and auditing for drift by hand doesn't scale past a small number of
servers -- they just keep diverging.

### Describe, don't do

Puppet, Chef, and Ansible were the first widely-adopted answer to this,
and the shift they represent is worth naming precisely, because it's the
same shift Kubernetes makes later, just at a smaller scope. The old
workflow is a sequence of commands: SSH in, run this, run that, check if
it worked. A Puppet manifest or an Ansible playbook is a description of
what the machine should look like -- this package installed, this file
containing this content, this service running -- and the tool's job is to
look at the machine, compare it to the description, and make only the
changes needed to close the gap. Run the same playbook twice and the
second run should do nothing, because the machine already matches the
description. That property -- safe to reapply, because it only acts on
the difference -- is the whole reason these tools were an improvement,
and it's the same property Chapter 5 is going to name explicitly as a
control loop.

It wasn't a complete fix. These tools still ran on a schedule, or on
demand, not continuously, so drift could reopen between runs, and someone
still had to remember to run them. But the core move -- write down what
the machine should look like, then let a tool make it true -- is the same
move every chapter after this one keeps making at a larger scope.

### Physical servers to orchestrated containers, briefly

The rest of this progression is really the same idea, applied one layer
up each time, as the unit being managed keeps shrinking and multiplying:
physical servers you could touch, one OS per machine, one workload's
mistake capable of taking down everything else sharing that hardware.
Virtual machines split one physical box into several isolated ones,
solving the sharing problem but still booting a full OS per workload,
still slow to provision, still something you patched and drifted the same
way individual servers had. Containers dropped the "boot a full OS"
requirement -- share the host kernel, isolate everything else -- and
suddenly a workload went from something that took minutes to provision to
something that took seconds, and from one process per physical or virtual
machine to dozens of processes safely sharing one machine.

That last shift is what makes orchestration necessary rather than
optional. Provisioning a VM was slow and rare enough that a human
deciding where it should run was fine. Once workloads are containers that
start in under a second and a single host might run dozens of them, "a
person decides where each one goes" stops being a workflow and starts
being the bottleneck. Something has to decide placement, notice failures,
and keep desired counts correct, continuously, faster than any person
could do it by hand. That something is the subject of the rest of this
book.

## Writing Chapter 2 (The Security Case for Systematized Infrastructure) in Will's voice

### Ad-hoc ops was always risky

Chapter 1 made the productivity case against hand-edited servers: drift,
lost context, nobody quite sure what's actually running. All of that is
also, separately, a security problem, and it was one even before the
threat landscape got worse. A server that's been hand-patched by three
different people over two years has no record of what was changed, which
means it also has no record of *whether every change was supposed to
happen*. An unauthorized change and an authorized-but-undocumented change
look identical from the outside -- neither one shows up anywhere except
in what the server is currently doing.

### Why it's worse now

Two things changed the stakes on top of that baseline risk. First, attack
tooling industrialized. Scanning the entire public IPv4 address space for
a specific vulnerable service configuration used to be a research project;
it's now a background process, running constantly, from multiple
directions at once. A misconfiguration that used to be safe because
nobody was likely to stumble onto it in the time it took you to notice
and fix it is no longer safe on that assumption -- something is checking,
right now, and will check again in an hour.

Second, the supply chain became a target in its own right. A compromised
build dependency, a poisoned base image, a maintainer's stolen credentials
on a widely-used package -- these don't require finding a hole in your
infrastructure at all. They ride in through the normal process of
building and deploying software, the same process every other chapter in
this book is about making safer, not riskier. Ransomware-as-a-service
turned the profit motive behind all of this into something available to
anyone willing to pay for access, not just a small number of technically
sophisticated actors. The threat model isn't "a skilled attacker might
target us specifically" anymore. It's "automated tooling will find
whatever's exposed, and someone downstream will monetize it."

### No diff, no review, no rollback

Put those two together and the hand-edited server from Chapter 1 stops
being merely inefficient and starts being a liability, for a specific,
mechanical reason: a manual change has no diff. Nobody reviewed it before
it went live, because there was no artifact to review -- the "change" was
a person typing commands into a terminal, not a pull request. If it turns
out to have been a mistake, or worse, if it turns out to have been made by
someone who shouldn't have had that access in the first place, there's no
clean way to know what it changed or to undo it, because undoing it means
remembering, by hand, what it was before.

Version-controlled infrastructure closes that gap by construction, not by
policy. When the desired state of a server or a cluster lives in a git
repository, every change is a commit: who made it, when, exactly what
changed, and -- if the review discipline from ordinary software
engineering gets applied here too -- someone else looked at it before it
took effect. A bad change is `git revert`, not an afternoon of
archaeology. This isn't a new security control bolted onto infrastructure
that used to lack one. It's the existing discipline of code review and
version control, already trusted for the application, extended to cover
the infrastructure that application runs on.

### If it's not in git, it shouldn't be running

That's the principle worth carrying into every chapter after this one,
because it's going to come back explicitly more than once: version
control isn't a convenience for infrastructure, it's the mechanism that
makes infrastructure auditable at all. A system where every running
change traces back to a reviewed commit is a system where "what's running
and why" always has an answer. A system where changes can still be made
by hand, outside that record, has a permanent, unfixable gap between what
the repository says and what's actually true -- and that gap is exactly
where both Chapter 1's drift problem and this chapter's security problem
live. Chapter 9 is going to spend real time on what happens once that gap
gets automated away entirely, git no longer just describing infrastructure
but actively defending it. Everything between here and there is really
this same idea, worked out at increasing scale.

## Writing Chapter 3 (Docker: Packaging Reality) in Will's voice

### What a container actually is, briefly

A container is not a lightweight virtual machine, even though it gets
described that way often enough that the description sticks. A VM
virtualizes hardware and boots a full second kernel on top of it. A
container is just an ordinary process on the host, running under the
same kernel as everything else, made to believe it's alone through three
mechanisms working together: **namespaces** hide everything the process
shouldn't see -- its own process ID space, its own network interfaces,
its own filesystem mounts, so `ps` inside the container shows a handful
of processes, not the host's real few hundred. **cgroups** cap what the
process is allowed to consume -- CPU, memory, I/O -- so one runaway
container can't starve everything else on the box. And a **union
filesystem** layers a stack of read-only image layers under one
writable layer on top, so the container appears to have its own private
filesystem without needing to actually copy the whole thing.

None of that is magic, and none of it requires believing anything about
containers being a fundamentally new kind of computing. It's namespacing,
resource limiting, and clever filesystem layering, and Docker's actual
contribution in 2013 wasn't inventing any of these three mechanisms --
Linux had namespaces and cgroups already, and LXC had been wiring them
together for years before Docker existed. Docker's contribution was
making the packaging and distribution of the result trivial: a
`Dockerfile`, a build command, and an image anyone else can pull and run
without caring how any of those three mechanisms actually work.

### Images vs. containers, and the Dockerfile as a recipe

The distinction that trips people up first: an image is not a container,
it's what a container is made from. This repo's `Dockerfile` is short
enough to read as a whole:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Six meaningful lines, and each one -- `FROM`, `COPY`, `RUN`, `COPY` again
-- adds one more layer to the union filesystem the previous section
described. `docker build` doesn't run this file the way a shell script
runs; it produces an image, a stack of those layers, and it's worth
seeing that stack for real rather than taking "layered" as an abstract
claim:

```shell
docker history k8s-toy-api:local
```

```
IMAGE          CREATED        CREATED BY                                      SIZE
57163a50e75e   ...            CMD ["uvicorn" "app:app" ...                    0B
<missing>      ...            EXPOSE [8000/tcp]                               0B
<missing>      ...            COPY app.py ./ # buildkit                       11.3kB
<missing>      ...            RUN /bin/sh -c pip install --no-cache-dir -r…   62.1MB
<missing>      ...            COPY requirements.txt ./ # buildkit             115B
<missing>      ...            WORKDIR /app                                    0B
                              [... python:3.12-slim base layers below ...]
```

`COPY app.py ./` is 11.3 kilobytes -- that's the entire application, one
file. Everything above a few hundred kilobytes in that list belongs to
either the `pip install` layer or the Debian base image underneath it,
none of which this repo wrote. That's the actual payoff of layering, made
concrete instead of asserted: change `app.py` and rebuild, and Docker
only has to redo the `COPY app.py` layer and whatever comes after it in
the file -- the `pip install` layer, unchanged since `requirements.txt`
didn't change, gets reused straight from cache. A Dockerfile is a recipe
in the specific sense that each step describes an incremental change to
apply on top of the last one, not a script that runs top to bottom and
discards its intermediate state.

### A short history, and why "works in the container" is a stronger claim

`chroot` gave a process its own root filesystem view in 1979 -- the
oldest of these three mechanisms by a wide margin, and proof this idea
isn't new. LXC, starting around 2008, was the first attempt to wire
namespaces and cgroups together into something usable as "a container,"
and it worked, but using it meant understanding all three mechanisms
individually and assembling them by hand. Docker's 2013 release didn't
replace any of that machinery -- early Docker used LXC directly under
the hood -- it replaced the assembly step with a `Dockerfile` and a
single `docker build`, and that packaging leap is what actually took off.
The OCI (Open Container Initiative) standardization that followed
formalized the image format itself, which is why an image built by
Docker runs fine under containerd or Podman today -- the format outlived
the tool that popularized it.

"Works on my machine" was never a claim about the code; it was a claim
about everything *surrounding* the code on that one machine -- library
versions, OS packages, environment variables nobody wrote down. "Works in
the container" is a stronger claim because the image is that entire
surrounding environment, made explicit in a file, checked into git next
to the code it runs. `python:3.12-slim` at the base of this repo's image
is a specific, named, versioned thing, not "whatever Python happens to be
installed on this box today." The whole rest of this book is going to
keep leaning on that same move -- take something that used to live only
in one person's memory of what they did to a machine, and make it a
committed file instead -- so it's worth having Chapter 3 be the place
that move first gets named plainly, at the smallest possible scale, one
image.

### Further reading

Docker's own "Get Started" guide is still the fastest way to build the
muscle memory for `build`/`run`/`exec` before any of the orchestration
chapters pile more on top of it. *The Docker Book* (James Turnbull) goes
deeper into the daemon and networking model than this chapter needs to.
The OCI image spec itself, for anyone who wants to see exactly what
"layer" and "manifest" mean at the level of actual JSON on disk, is short
enough to read in one sitting and worth it once namespaces and cgroups
stop being new.

## Writing Chapter 4 (Docker Compose: Orchestration's Training Wheels) in Will's voice

### One file, two services, one command

`docker-compose.yml` in this repo describes the same two-service app
Chapter 3 built one image for -- `postgres` and `api` -- as a single YAML
file instead of two separate `docker run` invocations someone would
otherwise have to remember and re-type correctly every time:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: toyapi
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5

  api:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: "postgresql://postgres:postgres@postgres:5432/toyapi"
    depends_on:
      postgres:
        condition: service_healthy
```

`docker compose up -d --build` builds the image from Chapter 3's
Dockerfile, starts both containers, and waits:

```shell
docker compose up -d --build
```

```
 Container k8s-hack-postgres-1  Starting
 Container k8s-hack-postgres-1  Started
 Container k8s-hack-postgres-1  Waiting
 Container k8s-hack-postgres-1  Healthy
 Container k8s-hack-api-1  Starting
 Container k8s-hack-api-1  Started
```

That "Waiting" line is `depends_on: condition: service_healthy` actually
doing something, not just documentation -- `api` doesn't start until
`postgres`'s own `healthcheck` (`pg_isready`) reports healthy, because
`api` connects to the database on startup and gains nothing by racing it.
Both containers come up healthy, and the API works exactly as it did
under Kubernetes in Chapter 6:

```shell
curl -s http://localhost:8000/api/v1/healthz
curl -s http://localhost:8000/api/v1/items
```

```json
{"status":"ok","database":"connected"}
[{"id":"item1","name":"First Item","value":100},{"id":"item2","name":"Second Item","value":200}]
```

Same image, same app code, same `JSONFormatter` from Chapter 11 --
`docker compose logs api` shows the identical structured JSON, down to
the same `pod` field the app writes into every log line, just holding a
container ID (`f2e4d42dc861`) instead of a Kubernetes pod name, because
`app.py` reads that field from `HOSTNAME` and Docker sets `HOSTNAME` to
the container ID the same way Kubernetes sets it to the pod name. The
logging code doesn't know or care which one it's running under.

### What Compose gets right

This is the whole deployment: one file, one command, and a `docker-compose.yml`
that a new developer can read top to bottom in under a minute and
understand exactly what's going to run. There's no cluster to provision
first, no separate image-loading step the way `minikube image load`
needed one in Chapter 6 -- Compose builds straight from the Dockerfile
and runs it on the same Docker daemon, immediately. That's real, and it's
why Compose is still the right answer for local development even on a
project that deploys to Kubernetes in production: the fastest path from
"clone the repo" to "the app is running and I can poke at it" almost
never runs through a cluster.

### Where the ceiling actually is

Push on it a little and the ceiling stops being theoretical. Ask Compose
for three copies of `api` instead of one:

```shell
docker compose up -d --scale api=3
```

```
 Container k8s-hack-api-3  Starting
Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint k8s-hack-api-3 (80c154af11f7...): Bind for 0.0.0.0:8000 failed: port is already allocated
```

```shell
docker compose ps -a
```

```
NAME                  STATUS                    PORTS
k8s-hack-api-1        Up 19 seconds (healthy)   0.0.0.0:8000->8000/tcp
k8s-hack-api-2        Created
k8s-hack-api-3        Created
k8s-hack-postgres-1   Up 25 seconds (healthy)
```

`api-2` and `api-3` exist, as containers, and go no further --
`Created`, never `Up`. `docker-compose.yml` maps `api`'s port with
`"8000:8000"`, a literal host port, and a host only has one port 8000.
The first container to claim it wins; everything after that fails to
bind. This isn't a bug or a missing flag. `docker-compose.yml`'s port
mapping is written as "this container's port 8000 goes on this host's
port 8000," and that sentence has no meaning once there's more than one
container trying to be the answer to it. Chapter 5's Service object
exists specifically to answer a different question -- "route to whichever
of these pods is healthy right now" -- and that question doesn't have a
sensible answer inside a single `docker-compose.yml` file at all, because
Compose has no concept of "a stable address in front of more than one
container." Multi-host scheduling has the same shape of problem one level
up: Compose has one Docker daemon to talk to, on one host, so "which of N
machines should this container run on" isn't a question Compose is even
positioned to ask.

Rolling updates hit a version of the same wall. `docker compose up
--build` after changing `app.py` stops the old `api` container and starts
a new one -- not simultaneously, not with the old one kept alive until the
new one proves itself healthy, the way Chapter 8 watched a bad
`ConfigMap` change get rejected by Kubernetes without ever taking `toy-api`
down. Compose's healthcheck exists and works, as `postgres`'s did above,
but nothing in Compose reads it to decide whether it's safe to remove an
old container yet. That gating logic is exactly what a Deployment's
rolling update adds on top of the same healthcheck idea.

### The right tool until it isn't

None of this makes `docker-compose.yml` worse than the seven YAML files
from Chapter 9's comparison -- it's 41 lines against 201, and for a
single host running two containers, it is a strictly better fit. The
honest way to hold both facts at once: Compose describes an application
on one machine, completely and well, and every one of the gaps above --
one host, a fixed port that can't be shared, no gating on rollouts -- is
a gap that only matters once there's more than one machine, more than one
copy of a service, or an update that has to happen without taking
anything down. Chapter 9 will come back to this exact tradeoff once
there's a full Kubernetes deployment to compare it against squarely. For
now, the ceiling is the point: everything Compose can't do in this
chapter is a preview of what the next several chapters exist to fix.

## Writing Chapter 5 (What Kubernetes Actually Is) in Will's voice

### The control loop, not the orchestrator

Chapter 4 ended at Compose's ceiling: one host, and nothing watching over
it once `docker compose up` returns. That second part is the real gap.
`docker-compose.yml` describes what should run, `docker compose up` makes
it run, and then the description's job is finished. If a container dies
five minutes later, nothing goes back and checks the file again. You find
out because the app is down, not because anything noticed the file said
otherwise.

Kubernetes' actual job is to keep noticing. Not once, at apply time, but
continuously, forever, until you change your mind. `deployment.yaml`
doesn't say "start 2 containers" -- Chapter 6 covers this file in detail,
but the shape of it matters here first -- it says `replicas: 2`, a fact
about how the world ought to look. Something is always comparing that
fact against how the world actually looks, and closing the gap whenever
the two disagree:

```
loop forever:
    desired = read the spec
    actual  = observe the cluster
    if desired != actual:
        act to close the gap
```

That's the entire idea. Everything else in Kubernetes -- the scheduler
placing pods, the kubelet keeping containers running, the whole apparatus
Chapter 7 puts through its paces -- is one more instance of this same
loop, watching a different piece of the world. It's why deleting a pod on
purpose and a node crashing and killing that pod by accident produce the
identical outcome: the loop doesn't know or care why `actual` stopped
matching `desired`, only that it did. A Compose restart policy is a rule
about one specific failure you anticipated. A control loop has no list of
anticipated failures -- it just keeps rechecking, so anything that
knocks `actual` out of line with `desired` gets corrected the same way,
whether you predicted it or not.

### The control plane is not magic -- it's pods

Ask this cluster what's actually running its control plane:

```shell
kubectl get pods -n kube-system
```

```
NAME                               READY   STATUS    RESTARTS      AGE
coredns-7d764666f9-t5p4b           1/1     Running   0             25h
etcd-minikube                      1/1     Running   0             25h
kube-apiserver-minikube            1/1     Running   0             25h
kube-controller-manager-minikube   1/1     Running   0             25h
kube-proxy-dpl4j                   1/1     Running   0             25h
kube-scheduler-minikube            1/1     Running   0             25h
storage-provisioner                1/1     Running   2 (16h ago)   25h
```

`kube-apiserver-minikube`, `kube-scheduler-minikube`,
`kube-controller-manager-minikube`, `etcd-minikube` -- the four pieces
usually drawn as a special box labeled "control plane" in every
Kubernetes diagram -- are just pods, in this same `kubectl get pods`
output, next to `coredns` and a storage provisioner. Minikube runs them
as ordinary containers because that's what they are. A managed cluster
(EKS, GKE, AKS) hides these behind the cloud provider so you're not
responsible for keeping etcd alive, but hiding them doesn't change what
they are underneath -- four programs, each with one job, watching each
other's output the same way `toy-api`'s pods get watched by the
Deployment controller.

What each one actually does, briefly:

- **`kube-apiserver`** is the only thing that talks to `etcd` directly.
  Every other piece here, including `kubectl` itself, only ever talks to
  the API server. `kubectl apply -f deployment.yaml` is a write to the
  API server, nothing more.
- **`etcd`** is where the desired state actually lives -- not the YAML
  file on disk, which is only a copy, but this key-value store. The file
  is how you tell etcd what to remember.
- **`kube-scheduler`** watches for pods that exist in the desired state
  but haven't been assigned to a node yet, and picks one.
- **`kube-controller-manager`** runs the control loops themselves -- the
  one that keeps a Deployment's replica count correct is one of many
  bundled in here.

Down on the node, outside this control-plane list, two more pieces close
the loop: the **kubelet** watches the API server for pods assigned to
its own node and makes sure their containers are actually running, and
**kube-proxy** (also visible above, as `kube-proxy-dpl4j`) sets up the
networking rules that make a Service's stable address actually route to
the right pods. Nothing here is a black box. It's the same watch-diff-act
loop from the last section, six times, each instance responsible for one
slice of "does reality match the spec."

### Mapping what you already know

Chapter 4 walked through this repo's `docker-compose.yml` -- two
services, `postgres` and `api`, each described by roughly a dozen lines.
Every one of those lines has a direct Kubernetes equivalent; it's just
split across more files, because Kubernetes gives each concern its own
object instead of one file per application:

| Compose concept | Kubernetes equivalent |
|---|---|
| `services.api` | Deployment (`deployment.yaml`) |
| `services.postgres` | StatefulSet (`postgres-statefulset.yaml`) -- Chapter 6 covers why a database gets a different object than a stateless service |
| `ports: "8000:8000"` | Service (`service.yaml`) -- a stable address, decoupled from any one container |
| `environment:` (non-secret values) | ConfigMap (`postgres-configmap.yaml`) |
| `environment:` (`POSTGRES_PASSWORD`) | Secret (`postgres-secret.yaml`) |
| `volumes: postgres_data:...` | PersistentVolumeClaim (`postgres-pvc.yaml`) |
| `healthcheck:` | `livenessProbe` / `readinessProbe` on the pod spec |
| `depends_on: condition: service_healthy` | no direct equivalent -- Chapter 6 covers how `start.sh` handles this by waiting on readiness explicitly |

The table looks like Kubernetes just renamed things and split them into
more files, and at the level of "what fields exist," that's not wrong.
The actual difference is everything from the first two sections of this
chapter: Compose's version of this table describes a single `docker
compose up` invocation, done once. Kubernetes' version describes a
standing order that a handful of control loops keep enforcing against
whatever's actually running, on whichever of however many nodes happen
to be available, for as long as the cluster exists. Same information,
different verb tense -- Compose says "do this," Kubernetes says "keep
this true."

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

### ConfigMap and Secret, side by side

`postgres-configmap.yaml` holds four fields -- host, port, database name,
username. `postgres-secret.yaml` holds exactly one -- the password. Every
one of those five values ends up in the same place: `deployment.yaml`
reads all of them into environment variables on the `api` container, and
one more variable, `DATABASE_URL`, is built by string-substituting all
five together.

```yaml
# deployment.yaml, abbreviated
env:
  - name: POSTGRES_HOST
    valueFrom:
      configMapKeyRef:
        name: postgres-config
        key: POSTGRES_HOST
  # ...POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER the same way
  - name: POSTGRES_PASSWORD
    valueFrom:
      secretKeyRef:
        name: postgres-secret
        key: POSTGRES_PASSWORD
  - name: DATABASE_URL
    value: postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@$(POSTGRES_HOST):$(POSTGRES_PORT)/$(POSTGRES_DB)
```

Same `env` list, same `valueFrom` mechanism, same moment at container
start when the value gets read in. If you only looked at timing, a
ConfigMap and a Secret are identical -- which is exactly what the earlier
experiment already proved for the ConfigMap half: edit it, and a running
pod keeps the old value until something restarts it. A Secret behaves no
differently on that score. So the split isn't about *when* Kubernetes
hands the value to the container. It's about what kind of thing the value
is once it's sitting in etcd or showing up in `kubectl` output.

Ask the cluster for the ConfigMap and it just tells you:

```shell
kubectl get configmap postgres-config -o yaml
```

```yaml
apiVersion: v1
data:
  POSTGRES_DB: toyapi
  POSTGRES_HOST: postgres
  POSTGRES_PORT: "5432"
  POSTGRES_USER: postgres
kind: ConfigMap
```

Ask for the Secret the same way:

```shell
kubectl get secret postgres-secret -o yaml
```

```yaml
apiVersion: v1
data:
  POSTGRES_PASSWORD: cG9zdGdyZXM=
kind: Secret
type: Opaque
```

`cG9zdGdyZXM=` is not encrypted -- it's base64, which anyone can decode in
one command (`echo cG9zdGdyZXM= | base64 -d` gets you back `postgres`).
Kubernetes isn't hiding the password from someone with access to read
Secrets in this namespace. What the Secret type actually buys you is
narrower and easy to undersell: it's excluded from `kubectl describe`'s
normal output, it can be RBAC-scoped separately from ConfigMaps so
"who can read config" and "who can read passwords" are different
permissions, and it signals to every tool in the ecosystem -- Sealed
Secrets, External Secrets, Vault integrations -- that this value belongs
to a different handling path than everything else in the pod's
environment. `describe pod` makes the distinction visible in one place:

```shell
kubectl describe pod toy-api-6fc5ddfd6d-7gn64   # use your own pod's name
```

```
Environment:
  POSTGRES_HOST:      <set to the key 'POSTGRES_HOST' of config map 'postgres-config'>  Optional: false
  POSTGRES_PORT:      <set to the key 'POSTGRES_PORT' of config map 'postgres-config'>  Optional: false
  POSTGRES_DB:        <set to the key 'POSTGRES_DB' of config map 'postgres-config'>    Optional: false
  POSTGRES_USER:      <set to the key 'POSTGRES_USER' of config map 'postgres-config'>  Optional: false
  POSTGRES_PASSWORD:  <set to the key 'POSTGRES_PASSWORD' in secret 'postgres-secret'>  Optional: false
  DATABASE_URL:       postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@$(POSTGRES_HOST):$(POSTGRES_PORT)/$(POSTGRES_DB)
```

Four lines name their ConfigMap and show nothing else to hide. The fifth
names its Secret and stops there -- `kubectl describe` won't print a
Secret's value even if you're staring right at the pod that consumes it.
Same list, same mechanism, one visibly different rule for one line, and
that line is the one line in this file that was never meant to be
readable in passing.

`postgres-secret.yaml` says the quiet part out loud in a comment: `stringData`
is used here "for readability," and in production you'd reach for Sealed
Secrets or External Secrets instead. Both of those close the actual gap --
neither etcd nor a `kubectl get -o yaml` from someone with namespace access
should be enough to read a real password -- but that's a problem for a
later chapter. What this repo demonstrates is the shape of the split, not
yet the hardened version of it.

## Writing Chapter 9 (When Not to Use Kubernetes) in Will's voice

### The same app, two ways

This repo has both versions sitting side by side. `docker-compose.yml` is
41 lines and two services:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: toyapi
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5

  api:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: "postgresql://postgres:postgres@postgres:5432/toyapi"
    depends_on:
      postgres:
        condition: service_healthy
```

`docker compose up` and both containers are running, `api` waiting for
`postgres`'s healthcheck before it starts, both reachable on their mapped
ports. That's the whole deployment.

The Kubernetes version of the identical app -- same image, same Postgres,
same environment variables -- is seven YAML files totaling 201 lines
(`postgres-configmap.yaml`, `postgres-secret.yaml`, `postgres-pvc.yaml`,
`postgres-statefulset.yaml`, `postgres-service.yaml`, `deployment.yaml`,
`service.yaml`), plus `start.sh`, 63 lines of shell to apply them in the
right order and wait for each one to actually come up before moving on to
the next. That's not a criticism of either file -- both are doing what
they were designed to do, correctly. It's the actual, measured cost of
the thing Chapter 5 called a control loop: seven times more YAML, plus an
orchestration script Compose doesn't need at all, to run the same two
containers on the same one machine.

### What all that extra machinery is buying, here, right now

Go back through the "why Kubernetes" list from Chapter 5's control-loop
framing -- multi-host scheduling, self-healing across machines, rolling
updates with real health gating -- and check which of those this repo's
minikube setup actually has:

- **Multi-host scheduling?** No. Minikube is one node. Every pod in this
  repo, `toy-api` and `postgres` alike, lands on the same machine, every
  time.
- **Survives a node dying?** No, not meaningfully -- there's only the one
  node. If it goes down, everything on it goes down, StatefulSet or not.
- **Multiple teams sharing a cluster?** No. It's one person running one
  app on one laptop.
- **Autoscaling on real load?** Not configured, and there's no load to
  scale against.

What's actually being exercised is the Deployment controller replacing a
pod you killed on purpose (Chapter 7), and a rolling update refusing to
take down a healthy pod for a bad config change (Chapter 8). Both real,
both worth learning -- and both things `docker compose up --scale` and a
restart policy get you a version of, on one box, without seven YAML files.
The honest reading of this repo's own setup is that it's demonstrating
Kubernetes mechanics on a workload that doesn't yet need Kubernetes. That
was the point -- it's a learning exercise, not a counterargument to
Chapter 5. But it's also exactly the shape of the mistake `WHY_KUBERNETES.md`
warns about: reaching for the fleet-management tool before there's a
fleet.

### What running Kubernetes well actually requires

The 201 lines of YAML are the part you write once. The part that doesn't
show up in any file is what it costs to run this well past a learning
cluster: someone has to own etcd's health, because etcd is the one thing
in this whole system that has no fallback if it loses quorum. Someone has
to keep the control plane's Kubernetes version current, because managed
control planes still expect you to handle node-side upgrades. Someone has
to actually read `kubectl get pods` output and notice a `CrashLoopBackOff`
before a customer does, because Kubernetes will happily leave a broken
Deployment in that state forever without paging anyone on its own.
`WHY_KUBERNETES.md` puts the comparison plainly: a managed database (RDS,
Cloud SQL) makes the cloud provider your Operator; a bare StatefulSet like
`postgres-statefulset.yaml` in this repo makes *you* the Operator, and an
Operator's job is a lot more than the two guarantees -- stable identity,
stable storage -- that a StatefulSet actually provides. That's a team's
worth of ongoing attention, not a weekend project, and it's a cost that
exists whether or not you're using any of the capacity it buys you.

### Signs you don't need it yet, and signs you're about to

The `docker-compose.yml` in this repo is the honest baseline: one host,
one team, a healthcheck and a restart policy cover the failure modes that
actually happen. Stay there as long as it keeps being true. The signals
that it's stopped being true tend to show up as specific, concrete
events, not vague unease -- one host running out of headroom under real
load, a deploy that needs to happen without an outage because people are
actively using the thing, a second team that needs to ship independently
without stepping on the first team's containers, or a hardware failure
that actually took something down and everyone found out that "restart
policy" doesn't cover "the whole box is gone." Any one of those is a
specific problem Compose has no answer for and Kubernetes was built
around. Reaching for Kubernetes before any of them has actually happened
buys you 201 lines of YAML and an operational burden with nothing yet to
show for it -- which is exactly what this repo's minikube setup is,
deliberately, as a place to learn the mechanics before you need them for
real.

## Writing Chapter 10 (Infrastructure as Code, Take One: Pulumi) in Will's voice

### Same resources, different syntax

Everything in Chapters 6 through 8 came from YAML files applied with
`kubectl apply -f`. `pulumi/__main__.py` in this repo does the same kind
of thing -- describe a ConfigMap, a Deployment, a Service, hand it to
Kubernetes -- but as Python instead of YAML:

```python
config_map = k8s.core.v1.ConfigMap(
    "graph-api-config",
    metadata=k8s.meta.v1.ObjectMetaArgs(name="graph-api-config"),
    data={
        "UVICORN_LOG_LEVEL": "info",
        "UVICORN_PORT": "8000",
    },
)
```

Read past the class names and this is the same shape as
`postgres-configmap.yaml`: a name, a `data` dict. The difference isn't
what's being described, it's what's doing the describing -- a real
programming language instead of a document format. That distinction
sounds abstract until you hit the places where YAML has no good answer
and Python does.

One example already sitting in this file: the Service is `NodePort`
with no `node_port` pinned, so Kubernetes allocates one from the
30000-32767 range at apply time -- you don't know it in advance.
`start.sh`'s answer to that, back in Chapter 6, was a separate shell
command run after the fact: `kubectl get svc toy-api -o jsonpath=...`.
Pulumi's answer is to make the allocated port part of the program itself:

```python
node = k8s.core.v1.Node.get("cluster-node", node_name)

node_ip = node.status.apply(
    lambda s: next(a.address for a in s.addresses if a.type == "InternalIP")
)
node_port = service.spec.apply(lambda s: str(s.ports[0].node_port))

pulumi.export("base_url", pulumi.Output.concat("http://", node_ip, ":", node_port))
```

`node.status`, `service.spec` -- these aren't plain Python values, they're
`Output`s, Pulumi's name for "a value that doesn't exist yet because the
resource that produces it hasn't been created yet." `.apply()` is how you
say "once this exists, do this with it." The comment right above the
export line in the actual file explains why that distinction can't be
skipped: `pulumi.Output.concat` is used deliberately instead of an
f-string, because an f-string would silently interpolate the Python
`repr()` of the `Output` object itself rather than the eventual string
value. That's not a hypothetical gotcha -- it's specific enough that
whoever wrote this file had clearly been bitten by it once. A YAML
manifest can't have this problem, because YAML has no concept of "a value
that will exist later." It also can't hand you a working URL without a
second, separate shell command to go find the allocated port -- the same
tradeoff in both directions.

### Type checking and reusable modules

`k8s.core.v1.ConfigMap(...)`, `k8s.apps.v1.DeploymentSpecArgs(...)` --
every one of these is a real Python class with a real constructor
signature. Misspell a field name in a YAML manifest and you find out at
`kubectl apply` time, if you're lucky, or at pod-crash time if you're not.
Misspell one of these and your editor tells you before you run anything,
because `DeploymentSpecArgs` doesn't have a `replicaz` parameter and
static analysis knows it. That's what "type checking" is actually buying
here -- not a vague quality signal, a concrete class of typo that never
reaches a cluster.

The same file demonstrates reuse too, if you look at how the Prometheus
and Grafana blocks lower down are built. They don't share a function with
the `graph-api` Deployment above them, but they share the same pattern --
`labels` dict, `Deployment`, `Service`, wired together the same way -- and
in Python that repetition is a standing invitation to extract a
`make_deployment(name, image, port, ...)` helper the moment a fourth
service shows up. A YAML manifest has no equivalent move. You can use
Helm templates or Kustomize overlays to fight the same duplication, but
that's reaching for a second tool to patch a gap in the first one. Pulumi
just uses the language you're already in.

### Where this file actually stands right now

This Pulumi program is not a clean parallel of the toy-api YAML from Chapters 6
through 8. It deploys an image called `tg-core-graph-api:local`, from a
different exercise (`tg-core`) than the `k8s-toy-api:local` this book has been
walking through, and along the way it's picked up a Prometheus deployment
scraping `graph-api`'s `/metrics` endpoint and a Grafana deployment wired to
that Prometheus as its one datasource. None of that was in the file when this
repo's `README.md` was written -- the README still describes it as creating
"the exact same ConfigMap + Deployment + Service as the YAML manifests," which
was true once and isn't anymore.

This is now a small, harmless instance of a problem, but it's one that gets
expensive at real scale: documentation describes the infrastructure as of
whenever someone last updated the doc, and the infrastructure-as-code keeps
moving. A YAML manifest and a Pulumi program are both supposed to be the source
of truth for what's running -- that's the entire pitch of this part of the book
-- but nothing enforces that a README stays truthful about either one. The fix
isn't clever tooling, it's the same discipline Chapter 2 argued for at the
start: *if a description of the system lives outside the system's own declared
state, it drifts, and the only real defense is noticing.*

### When Pulumi earns its complexity over plain manifests

None of this makes Pulumi strictly better than YAML. It's more machinery: a
language runtime, a package manager, a state backend that has to be reachable
and correctly authenticated before `pulumi up` does anything at all. The Pulumi
program in this repo is configured against a remote backend, and if that
backend is unreachable, `pulumi stack ls` fails outright before you get
anywhere near applying anything. `kubectl apply -f service.yaml` has no
equivalent failure mode; the manifest is the state.

This extra machinery becomes worthwhile when a project has more than a handful
of resources, when the same shapes (a Deployment plus a Service plus a
ConfigMap, over and over) start repeating across services, or when "I made a
typo in a field name" has actually cost someone a debugging session. That's
when a real language starts paying for itself. A single toy API with one
ConfigMap doesn't need it. This repo's own Pulumi file, three services deep and
still growing, is starting to sit right at that line.

## Writing Chapter 11 (Observability Basics: Logging) in Will's voice

### One line becomes three, and a pod name you didn't ask for

Hit the running API once, with a request ID attached so it's easy to
pick back out of the noise:

```shell
curl -s -H "X-Request-ID: book-demo-0001" \
  "http://${MINIKUBE_IP}:${NODE_PORT}/api/v1/items"
```

Then go looking for it in the logs of both `toy-api` pods:

```shell
for pod in $(kubectl get pods -l app=toy-api -o jsonpath='{.items[*].metadata.name}'); do
  echo "=== $pod ==="
  kubectl logs "$pod" --since=30s | grep book-demo-0001
done
```

```
=== toy-api-6fc5ddfd6d-7gn64 ===
=== toy-api-6fc5ddfd6d-b9kvv ===
{"timestamp": "2026-09-07T18:47:23.462567Z", "level": "info", "message": "request started", "request_id": "book-demo-0001", "pod": "toy-api-6fc5ddfd6d-b9kvv", "method": "GET", "path": "/api/v1/items", "client": "10.244.0.1"}
{"timestamp": "2026-09-07T18:47:23.469232Z", "level": "info", "message": "items listed", "request_id": "book-demo-0001", "pod": "toy-api-6fc5ddfd6d-b9kvv", "count": 2}
{"timestamp": "2026-09-07T18:47:23.471122Z", "level": "info", "message": "request completed", "request_id": "book-demo-0001", "pod": "toy-api-6fc5ddfd6d-b9kvv", "method": "GET", "path": "/api/v1/items", "status": 200}
```

One `curl`, three log lines, and nothing came out of `toy-api-...-7gn64`
at all -- the request landed on `b9kvv` because that's whichever pod
`kube-proxy` happened to route it to, same randomness from Chapter 7.
Nobody chose that pod on purpose and the request didn't care which one
answered, but once you're debugging instead of just calling the API, you
suddenly do care, and `request_id` is the only thing that ties the three
lines together as one event rather than three unrelated ones.

That correlation isn't automatic. Open `app.py` and it's exactly two
pieces of machinery: a `ContextVar` holding the current request's ID, and
`RequestIDMiddleware`, which reads `X-Request-ID` off the incoming
request (or generates a UUID if the caller didn't send one), sets it in
that ContextVar, and echoes it back in the response headers. Every
`logger.info(...)` call downstream, in every endpoint, picks it up for
free through `JSONFormatter`, because the formatter reads the same
ContextVar on every single line it emits:

```python
request_id = request_id_ctx.get()
if request_id:
    log_data["request_id"] = request_id
```

That's the whole trick. No log line anywhere in `app.py` passes
`request_id` explicitly -- `logger.info("items listed", extra={"count": len(items)})`
in the items endpoint has no idea what request it's part of. The
formatter fills that in from context, on every line, unconditionally.
Miss wiring that ContextVar into some new code path -- a background task,
a second thread -- and its log lines quietly stop carrying a `request_id`
at all, with nothing to warn you.

### The line the endpoint wrote vs. the line the formatter added

Try a request that fails on purpose:

```shell
curl -s -o /dev/null -w "%{http_code}\n" \
  -H "X-Request-ID: book-demo-404" \
  "http://${MINIKUBE_IP}:${NODE_PORT}/api/v1/items/does-not-exist"
```

```
404
```

```json
{"timestamp": "2026-09-07T18:47:33.879184Z", "level": "info", "message": "request started", "request_id": "book-demo-404", "method": "GET", "path": "/api/v1/items/does-not-exist", "client": "10.244.0.1"}
{"timestamp": "2026-09-07T18:47:33.881006Z", "level": "warning", "message": "item not found", "request_id": "book-demo-404", "item_id": "does-not-exist"}
{"timestamp": "2026-09-07T18:47:33.881569Z", "level": "info", "message": "request completed", "request_id": "book-demo-404", "method": "GET", "path": "/api/v1/items/does-not-exist", "status": 404}
```

The middle line is the one that actually says something -- `logger.warning("item not found", extra={"item_id": item_id})`,
written by hand in the `get_item` endpoint, one call, one string, one
extra field. Everything else on that line -- `timestamp`, `level`,
`service`, `pod`, `request_id` -- came from `JSONFormatter` without the
endpoint author having to think about any of it. That split is the actual
point of structured logging: the application code stays down at "here's
what happened" (`item not found`, `does-not-exist`), and the formatter's
job is making sure every line, no matter which of the dozen or so
`logger.info`/`logger.warning` calls scattered through `app.py` produced
it, comes out shaped the same way and carries the same request-level
context. `grep`-ing plain text for an error means guessing at a string.
Piping this through `jq 'select(.level=="warning")'` means asking a
question the log already knows the answer to.

Not every field on that line is one you'd choose on purpose, though.
Look closely at the full JSON as it actually comes out of the pod --
there's a `taskName` field in there too, something like
`"taskName": "starlette.middleware.base.BaseHTTPMiddleware.__call__.<locals>.call_next.<locals>.coro"`.
That's `JSONFormatter` doing exactly what it's written to do -- copying
every attribute off the `LogRecord` that isn't on its exclusion list --
and asyncio happens to stash the current task's name on the record under
a key nobody thought to exclude. It's harmless here, just noise, but it's
a fair warning about the "log everything on the record" approach: the
formatter doesn't know the difference between a field you meant to add
and one the runtime left lying around.

### Where the trail actually ends

Send one more request, note which pod answers, and delete that pod on
purpose:

```shell
curl -s -o /dev/null -H "X-Request-ID: book-demo-vanish" \
  "http://${MINIKUBE_IP}:${NODE_PORT}/api/v1/items"
kubectl logs toy-api-6fc5ddfd6d-7gn64 --since=30s | grep book-demo-vanish
```

```json
{"timestamp": "2026-09-07T18:47:43.309449Z", "level": "info", "message": "request started", "request_id": "book-demo-vanish", "pod": "toy-api-6fc5ddfd6d-7gn64", ...}
{"timestamp": "2026-09-07T18:47:43.312656Z", "level": "info", "message": "items listed", "request_id": "book-demo-vanish", "pod": "toy-api-6fc5ddfd6d-7gn64", "count": 2}
{"timestamp": "2026-09-07T18:47:43.313184Z", "level": "info", "message": "request completed", "request_id": "book-demo-vanish", "pod": "toy-api-6fc5ddfd6d-7gn64", ...}
```

The line's there, plainly, with the pod's name right on it. Now delete
that pod the same way Chapter 7 did, wait for its replacement, and ask
for the same logs again:

```shell
kubectl delete pod toy-api-6fc5ddfd6d-7gn64
kubectl wait --for=condition=ready pod -l app=toy-api --timeout=60s
kubectl logs toy-api-6fc5ddfd6d-7gn64
```

```
error: error from server (NotFound): pods "toy-api-6fc5ddfd6d-7gn64" not found in namespace "default"
```

Gone. Not "gone from the default view, still there if you dig" -- gone.
`kubectl logs` reads from the node, keyed on a pod that no longer exists,
and the Deployment controller's whole job, going all the way back to
Chapter 7, is making sure that pod's replacement gets a new name. The
same mechanism that makes Kubernetes self-healing is what makes
`kubectl logs` alone useless for anything you need to look back on. A
crash worth debugging is exactly the kind of event likely to have killed
the pod that logged it.

`LOGGING.md` calls this "node-level logging" and lists Loki or the EFK
stack as the fix: ship every line off the node to something with its own
retention, before the pod that wrote it disappears. Nothing about that
requires changing a single line in `app.py`. The JSON is already there,
already structured, already carrying `request_id` and `pod` on every
line -- Promtail or Fluentd's whole job is reading what's already being
written to stdout and shipping it somewhere that outlives the pod. The
logging code in this repo was written for that day already; today it's
just not running yet.
