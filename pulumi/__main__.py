"""Pulumi program for the graph-api exercise -- a code-first equivalent of
../configmap.yaml + ../deployment.yaml + ../service.yaml. Same resources,
same names, so it's a drop-in alternative to `kubectl apply -f ...`.

Not part of the tg-core package; see ../README.md.
"""

import pulumi
import pulumi_kubernetes as k8s

labels = {"app": "graph-api"}

config_map = k8s.core.v1.ConfigMap(
    "graph-api-config",
    metadata=k8s.meta.v1.ObjectMetaArgs(name="graph-api-config"),
    data={
        # uvicorn's CLI reads UVICORN_-prefixed env vars automatically.
        "UVICORN_LOG_LEVEL": "info",
        "UVICORN_PORT": "8000",
    },
)

deployment = k8s.apps.v1.Deployment(
    "graph-api",
    metadata=k8s.meta.v1.ObjectMetaArgs(name="graph-api", labels=labels),
    spec=k8s.apps.v1.DeploymentSpecArgs(
        replicas=1,
        selector=k8s.meta.v1.LabelSelectorArgs(match_labels=labels),
        template=k8s.core.v1.PodTemplateSpecArgs(
            metadata=k8s.meta.v1.ObjectMetaArgs(labels=labels),
            spec=k8s.core.v1.PodSpecArgs(
                containers=[
                    k8s.core.v1.ContainerArgs(
                        name="graph-api",
                        image="tg-core-graph-api:local",
                        # side-loaded via `minikube image load`, never pulled from a registry.
                        image_pull_policy="IfNotPresent",
                        ports=[k8s.core.v1.ContainerPortArgs(container_port=8000)],
                        env_from=[
                            k8s.core.v1.EnvFromSourceArgs(
                                config_map_ref=k8s.core.v1.ConfigMapEnvSourceArgs(
                                    name=config_map.metadata.name,
                                )
                            )
                        ],
                        liveness_probe=k8s.core.v1.ProbeArgs(
                            http_get=k8s.core.v1.HTTPGetActionArgs(
                                path="/healthz", port=8000
                            ),
                            period_seconds=10,
                            timeout_seconds=3,
                            failure_threshold=3,
                        ),
                        readiness_probe=k8s.core.v1.ProbeArgs(
                            http_get=k8s.core.v1.HTTPGetActionArgs(
                                path="/healthz", port=8000
                            ),
                            period_seconds=10,
                            timeout_seconds=3,
                            failure_threshold=3,
                        ),
                    )
                ],
            ),
        ),
    ),
)

service = k8s.core.v1.Service(
    "graph-api",
    metadata=k8s.meta.v1.ObjectMetaArgs(name="graph-api"),
    spec=k8s.core.v1.ServiceSpecArgs(
        # NodePort, not ClusterIP, so the API is reachable from the host without
        # a `kubectl port-forward` babysitter -- and so `base_url` below can be a
        # real address rather than a hardcoded localhost guess.
        type="NodePort",
        selector=labels,
        # No explicit node_port: the API server allocates one from 30000-32767.
        # That's the point of the output -- the port isn't knowable until apply.
        ports=[k8s.core.v1.ServicePortArgs(port=8000, target_port=8000)],
    ),
)

# The node's IP is the other half of the external address. Node.get adopts the
# already-existing node read-only (no create/update/delete); the name is the
# single-node cluster's, minikube's default, overridable for kind etc. via
# `pulumi config set node_name kind-control-plane`.
node_name = pulumi.Config().get("node_name") or "minikube"
node = k8s.core.v1.Node.get("cluster-node", node_name)

node_ip = node.status.apply(
    lambda s: next(a.address for a in s.addresses if a.type == "InternalIP")
)
node_port = service.spec.apply(lambda s: str(s.ports[0].node_port))

pulumi.export("deployment_name", deployment.metadata.name)
pulumi.export("service_name", service.metadata.name)
pulumi.export("configmap_name", config_map.metadata.name)
# Outputs are futures, so the URL has to be assembled with Output.concat --
# an f-string here would interpolate the repr of the Output object, silently.
pulumi.export("base_url", pulumi.Output.concat("http://", node_ip, ":", node_port))

# --- Prometheus: scrapes graph-api's /metrics (added via prometheus-fastapi- ---
# --- instrumentator in app.py) using a static target, no RBAC/service-      ---
# --- discovery needed since there's exactly one thing to scrape.           ---
prometheus_labels = {"app": "prometheus"}

prometheus_config = k8s.core.v1.ConfigMap(
    "prometheus-config",
    metadata=k8s.meta.v1.ObjectMetaArgs(name="prometheus-config"),
    data={
        "prometheus.yml": """\
global:
  scrape_interval: 10s
scrape_configs:
  - job_name: graph-api
    static_configs:
      - targets: ["graph-api:8000"]
  - job_name: prometheus
    static_configs:
      - targets: ["localhost:9090"]
""",
    },
)

prometheus_deployment = k8s.apps.v1.Deployment(
    "prometheus",
    metadata=k8s.meta.v1.ObjectMetaArgs(name="prometheus", labels=prometheus_labels),
    spec=k8s.apps.v1.DeploymentSpecArgs(
        replicas=1,
        selector=k8s.meta.v1.LabelSelectorArgs(match_labels=prometheus_labels),
        template=k8s.core.v1.PodTemplateSpecArgs(
            metadata=k8s.meta.v1.ObjectMetaArgs(labels=prometheus_labels),
            spec=k8s.core.v1.PodSpecArgs(
                containers=[
                    k8s.core.v1.ContainerArgs(
                        name="prometheus",
                        image="prom/prometheus:v2.55.1",
                        args=["--config.file=/etc/prometheus/prometheus.yml"],
                        ports=[k8s.core.v1.ContainerPortArgs(container_port=9090)],
                        volume_mounts=[
                            k8s.core.v1.VolumeMountArgs(
                                name="config", mount_path="/etc/prometheus"
                            )
                        ],
                        resources=k8s.core.v1.ResourceRequirementsArgs(
                            requests={"cpu": "100m", "memory": "128Mi"},
                            limits={"cpu": "250m", "memory": "256Mi"},
                        ),
                    )
                ],
                volumes=[
                    k8s.core.v1.VolumeArgs(
                        name="config",
                        config_map=k8s.core.v1.ConfigMapVolumeSourceArgs(
                            name=prometheus_config.metadata.name,
                        ),
                    )
                ],
            ),
        ),
    ),
)

prometheus_service = k8s.core.v1.Service(
    "prometheus",
    metadata=k8s.meta.v1.ObjectMetaArgs(name="prometheus"),
    spec=k8s.core.v1.ServiceSpecArgs(
        type="ClusterIP",
        selector=prometheus_labels,
        ports=[k8s.core.v1.ServicePortArgs(port=9090, target_port=9090)],
    ),
)

# --- Grafana: pre-wired with Prometheus as its one datasource. Anonymous ---
# --- admin access is enabled for convenience -- fine for a port-forward- ---
# --- only learning cluster, never do this on anything internet-facing.  ---
grafana_labels = {"app": "grafana"}

grafana_datasources = k8s.core.v1.ConfigMap(
    "grafana-datasources",
    metadata=k8s.meta.v1.ObjectMetaArgs(name="grafana-datasources"),
    data={
        "datasource.yml": """\
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
""",
    },
)

grafana_deployment = k8s.apps.v1.Deployment(
    "grafana",
    metadata=k8s.meta.v1.ObjectMetaArgs(name="grafana", labels=grafana_labels),
    spec=k8s.apps.v1.DeploymentSpecArgs(
        replicas=1,
        selector=k8s.meta.v1.LabelSelectorArgs(match_labels=grafana_labels),
        template=k8s.core.v1.PodTemplateSpecArgs(
            metadata=k8s.meta.v1.ObjectMetaArgs(labels=grafana_labels),
            spec=k8s.core.v1.PodSpecArgs(
                containers=[
                    k8s.core.v1.ContainerArgs(
                        name="grafana",
                        image="grafana/grafana:11.2.0",
                        ports=[k8s.core.v1.ContainerPortArgs(container_port=3000)],
                        env=[
                            k8s.core.v1.EnvVarArgs(
                                name="GF_AUTH_ANONYMOUS_ENABLED", value="true"
                            ),
                            k8s.core.v1.EnvVarArgs(
                                name="GF_AUTH_ANONYMOUS_ORG_ROLE", value="Admin"
                            ),
                        ],
                        volume_mounts=[
                            k8s.core.v1.VolumeMountArgs(
                                name="datasources",
                                mount_path="/etc/grafana/provisioning/datasources",
                            )
                        ],
                        resources=k8s.core.v1.ResourceRequirementsArgs(
                            requests={"cpu": "100m", "memory": "128Mi"},
                            limits={"cpu": "250m", "memory": "256Mi"},
                        ),
                    )
                ],
                volumes=[
                    k8s.core.v1.VolumeArgs(
                        name="datasources",
                        config_map=k8s.core.v1.ConfigMapVolumeSourceArgs(
                            name=grafana_datasources.metadata.name,
                        ),
                    )
                ],
            ),
        ),
    ),
)

grafana_service = k8s.core.v1.Service(
    "grafana",
    metadata=k8s.meta.v1.ObjectMetaArgs(name="grafana"),
    spec=k8s.core.v1.ServiceSpecArgs(
        type="ClusterIP",
        selector=grafana_labels,
        ports=[k8s.core.v1.ServicePortArgs(port=3000, target_port=3000)],
    ),
)

pulumi.export("prometheus_service_name", prometheus_service.metadata.name)
pulumi.export("grafana_service_name", grafana_service.metadata.name)
