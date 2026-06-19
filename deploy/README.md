# Deploying roshan-harf-mcp

This server is stateless, so it scales horizontally: run multiple replicas
behind a load balancer using the `streamable-http` transport. Below are four
deployment paths.

Configuration is always the same set of `ROSHAN_HARF__…` environment variables
(see the [root README](../README.md#configuration)). Non-secret values (base
URLs, default instance, verify_ssl) belong in a ConfigMap; secrets (tokens)
belong in a Secret.

## Docker / Compose

```bash
docker build -t roshan-harf-mcp:latest .
docker run --rm -p 8000:8000 \
  -e ROSHAN_HARF_BASE_URL=https://harf.roshan-ai.ir \
  -e ROSHAN_HARF_TOKEN=... \
  roshan-harf-mcp:latest

# or two pre-wired instances:
docker compose up
```

## Helm

```bash
helm install roshan-harf ./helm/roshan-harf-mcp \
  --set image.repository=ghcr.io/you/roshan-harf-mcp \
  --set image.tag=0.1.0 \
  --set-string instances.default.base_url=https://harf.roshan-ai.ir \
  --set-string instances.default.token=...
```

Key `values.yaml` sections: `image`, `replicaCount`, `service`, `ingress`,
`resources`, `autoscaling`, `instances` (per-instance base URLs + tokens), and
`existingSecret` (to supply secrets out-of-band instead of via values).

## Raw Kubernetes

```bash
cp kubernetes/secret.example.yaml kubernetes/secret.yaml
# edit kubernetes/secret.yaml with real tokens (secret.yaml is gitignored)
kubectl apply -k kubernetes/
```

Manifests: `namespace`, `configmap`, `secret.example`, `deployment`, `service`,
`ingress`, `hpa`, and a `kustomization.yaml`.

## Terraform

```bash
cd terraform
terraform init
terraform apply \
  -var 'image=ghcr.io/you/roshan-harf-mcp:0.1.0' \
  -var 'instances={ default = { base_url = "https://harf.roshan-ai.ir", token = "t" }, onprem = { base_url = "https://harf.internal.local", token = "t2", verify_ssl = false } }'
```

The module creates a namespace, ConfigMap, Secret, Deployment, Service, and
(optionally) an Ingress and HorizontalPodAutoscaler.
