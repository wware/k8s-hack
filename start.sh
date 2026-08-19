#!/bin/bash
set -e

echo "🔄 Starting Minikube..."
if ! minikube status &>/dev/null; then
    minikube start
else
    echo "✓ Minikube already running"
fi

echo ""
echo "🏗️ Building Docker image..."
docker build -t k8s-toy-api:local .

echo ""
echo "📦 Loading image into Minikube..."
minikube image load k8s-toy-api:local

echo ""
echo "🧹 Cleaning up existing deployments..."
kubectl delete -f deployment.yaml --ignore-not-found
kubectl delete -f service.yaml --ignore-not-found
kubectl delete -f postgres-statefulset.yaml --ignore-not-found
kubectl delete -f postgres-service.yaml --ignore-not-found
kubectl delete -f postgres-configmap.yaml --ignore-not-found
kubectl delete -f postgres-secret.yaml --ignore-not-found
kubectl delete -f postgres-pvc.yaml --ignore-not-found

echo ""
echo "📦 Applying Kubernetes manifests..."
kubectl apply -f postgres-configmap.yaml
kubectl apply -f postgres-secret.yaml
kubectl apply -f postgres-pvc.yaml
kubectl apply -f postgres-statefulset.yaml
kubectl apply -f postgres-service.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

echo ""
echo "⏳ Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres --timeout=120s

echo ""
echo "⏳ Waiting for API pods to be ready..."
kubectl wait --for=condition=ready pod -l app=toy-api --timeout=60s

echo ""
echo "✅ Deployment complete!"
echo ""
kubectl get pods,svc,pvc

echo ""
echo "🧪 Running API tests..."
./test-api.sh

echo ""
echo "✨ All done! Access the API:"
echo "  Port-forward: kubectl port-forward svc/toy-api 8000:8000"
echo "  Then visit: http://localhost:8000/api/v1/docs"
echo ""
echo "  Or use NodePort: minikube service toy-api --url"
echo ""
echo "To tear down: kubectl delete -f . && minikube delete"
