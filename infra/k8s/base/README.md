# Kubernetes

## Docker Desktop

```bash
kubectl config use-context docker-desktop
kubectl cluster-info
```

## Build images

```bash
docker build -t hse-c_sharp-gamification-backend:latest -f Backend/docker/app.Dockerfile Backend
docker build -t hse-c_sharp-gamification-frontend:latest -f Frontend/c-s-game/dockerfile Frontend/c-s-game
```

## Minikube

```bash
eval "$(minikube docker-env)"
docker build -t hse-c_sharp-gamification-backend:latest -f Backend/docker/app.Dockerfile Backend
docker build -t hse-c_sharp-gamification-frontend:latest -f Frontend/c-s-game/dockerfile Frontend/c-s-game
```

## Kind

```bash
docker build -t hse-c_sharp-gamification-backend:latest -f Backend/docker/app.Dockerfile Backend
docker build -t hse-c_sharp-gamification-frontend:latest -f Frontend/c-s-game/dockerfile Frontend/c-s-game
kind load docker-image hse-c_sharp-gamification-backend:latest
kind load docker-image hse-c_sharp-gamification-frontend:latest
```

## Apply

```bash
kubectl apply -k infra/k8s/base
```

## Wait

```bash
kubectl -n hse-csharp-gamification wait --for=condition=complete job/backend-migrate --timeout=180s
kubectl -n hse-csharp-gamification wait --for=condition=available deployment/backend --timeout=180s
kubectl -n hse-csharp-gamification wait --for=condition=available deployment/worker --timeout=180s
kubectl -n hse-csharp-gamification wait --for=condition=available deployment/frontend --timeout=240s
kubectl -n hse-csharp-gamification wait --for=condition=available deployment/nginx --timeout=180s
```

## Status

```bash
kubectl -n hse-csharp-gamification get pods
kubectl -n hse-csharp-gamification get deploy,hpa,pdb,job,svc,pvc
```

## Open

```bash
kubectl -n hse-csharp-gamification port-forward service/nginx 8080:80
```

```text
http://localhost:8080
http://localhost:8080/health/live
http://localhost:8080/docs
```

## Scale

```bash
kubectl -n hse-csharp-gamification scale deployment backend --replicas=3
kubectl -n hse-csharp-gamification scale deployment worker --replicas=2
```

## Autoscaling

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl -n kube-system patch deployment metrics-server --patch-file infra/k8s/addons/metrics-server/metrics-server-docker-desktop-patch.yaml
kubectl -n kube-system rollout status deployment/metrics-server --timeout=180s
kubectl top pods -n hse-csharp-gamification
kubectl -n hse-csharp-gamification get hpa
kubectl -n hse-csharp-gamification describe hpa backend
kubectl -n hse-csharp-gamification describe hpa worker
```

## Failure

```bash
kubectl -n hse-csharp-gamification delete pod -l app.kubernetes.io/name=backend
kubectl -n hse-csharp-gamification rollout status deployment/backend --timeout=180s
kubectl -n hse-csharp-gamification get pods
```

## Load test

```bash
kubectl -n hse-csharp-gamification delete job api-load-test --ignore-not-found
kubectl apply -f infra/k8s/addons/load-test/api-load-test-job.yaml
kubectl -n hse-csharp-gamification wait --for=condition=complete job/api-load-test --timeout=120s
kubectl -n hse-csharp-gamification logs job/api-load-test
kubectl -n hse-csharp-gamification get hpa
```

## KEDA

```bash
kubectl apply --server-side -f https://github.com/kedacore/keda/releases/download/v2.16.1/keda-2.16.1.yaml
kubectl wait --for=condition=available deployment/keda-operator -n keda --timeout=180s
kubectl apply -f infra/k8s/addons/keda/worker-scaledobject.yaml
kubectl -n hse-csharp-gamification get scaledobject
```

## Logs

```bash
kubectl -n hse-csharp-gamification logs deployment/backend
kubectl -n hse-csharp-gamification logs deployment/worker
kubectl -n hse-csharp-gamification logs deployment/frontend
kubectl -n hse-csharp-gamification logs deployment/nginx
kubectl -n hse-csharp-gamification get events --sort-by=.lastTimestamp
```

## Cleanup

```bash
kubectl delete -k infra/k8s/base
```
