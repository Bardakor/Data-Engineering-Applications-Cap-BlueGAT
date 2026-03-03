# Docker cleanup – reduce container usage

Your Final 4 app uses **docker-compose** (db, api, web). The extra containers you see come from **Docker Desktop’s built-in Kubernetes**, which you don’t need for this project.

## 1. Disable Kubernetes in Docker Desktop

This stops all `k8s_*` containers (etcd, kube-apiserver, coredns, etc.) and frees ~500MB+ RAM.

1. Open **Docker Desktop**
2. Go to **Settings** (gear icon)
3. Open **Kubernetes**
4. **Uncheck** “Enable Kubernetes”
5. Click **Apply & Restart**

After restart, only your Final 4 containers (db, api, web) will run.

## 2. Optional: stop BuildKit builder

The `buildx_buildkit_voyage-builder0` container is used for builds. You can stop it when not building:

```bash
docker buildx stop voyage-builder 2>/dev/null || true
```

It will start again automatically when you run `docker compose build`.

## 3. Prune unused resources

```bash
# Remove stopped containers
docker container prune -f

# Remove unused images (optional)
docker image prune -a -f

# Full system prune (optional, aggressive)
docker system prune -a -f
```

## Summary

| Container type        | Action                          |
|-----------------------|---------------------------------|
| `final4-*` (api, web, db) | Keep – your app                |
| `k8s_*` (Kubernetes)  | Disable Kubernetes in Docker Desktop |
| `buildx_buildkit_*`   | Optional: stop when not building    |
| Stopped containers    | `docker container prune -f`        |
