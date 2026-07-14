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
kubectl -n hse-csharp-gamification get deploy,job,svc,pvc
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

## Logs

```bash
kubectl -n hse-csharp-gamification logs deployment/backend
kubectl -n hse-csharp-gamification logs deployment/worker
kubectl -n hse-csharp-gamification logs deployment/frontend
kubectl -n hse-csharp-gamification logs deployment/nginx
```

## Cleanup

```bash
kubectl delete -k infra/k8s/base
```
