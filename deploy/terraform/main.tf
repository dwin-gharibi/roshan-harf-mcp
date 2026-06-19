locals {
  app_labels = {
    "app.kubernetes.io/name"       = "roshan-harf-mcp"
    "app.kubernetes.io/managed-by" = "terraform"
  }

  config_env = merge(
    {
      "ROSHAN_HARF__DEFAULT_INSTANCE" = var.default_instance
      "ROSHAN_HARF__LOG_LEVEL"        = var.log_level
    },
    merge([
      for name, inst in var.instances : {
        "ROSHAN_HARF__INSTANCES__${upper(name)}__BASE_URL"   = inst.base_url
        "ROSHAN_HARF__INSTANCES__${upper(name)}__VERIFY_SSL" = tostring(inst.verify_ssl)
        "ROSHAN_HARF__INSTANCES__${upper(name)}__TIMEOUT"    = tostring(inst.timeout)
      }
    ]...)
  )

  secret_env = { for k, v in merge([
    for name, inst in var.instances : {
      "ROSHAN_HARF__INSTANCES__${upper(name)}__TOKEN" = inst.token
    }
  ]...) : k => v if v != null }
}

resource "kubernetes_namespace" "this" {
  count = var.create_namespace ? 1 : 0
  metadata {
    name   = var.namespace
    labels = local.app_labels
  }
}

resource "kubernetes_config_map" "this" {
  metadata {
    name      = "roshan-harf-mcp"
    namespace = var.namespace
    labels    = local.app_labels
  }
  data       = local.config_env
  depends_on = [kubernetes_namespace.this]
}

resource "kubernetes_secret" "this" {
  metadata {
    name      = "roshan-harf-mcp"
    namespace = var.namespace
    labels    = local.app_labels
  }
  data       = local.secret_env
  type       = "Opaque"
  depends_on = [kubernetes_namespace.this]
}

resource "kubernetes_deployment" "this" {
  metadata {
    name      = "roshan-harf-mcp"
    namespace = var.namespace
    labels    = local.app_labels
  }
  spec {
    replicas = var.autoscaling.enabled ? null : var.replicas
    selector {
      match_labels = local.app_labels
    }
    template {
      metadata {
        labels = local.app_labels
        annotations = {
          "checksum/config" = sha256(jsonencode(local.config_env))
        }
      }
      spec {
        security_context {
          run_as_non_root = true
          run_as_user     = 10001
        }
        container {
          name              = "roshan-harf-mcp"
          image             = var.image
          image_pull_policy = "IfNotPresent"
          args = [
            "--transport", "streamable-http",
            "--host", "0.0.0.0",
            "--port", tostring(var.service_port),
          ]
          port {
            name           = "http"
            container_port = var.service_port
          }
          env_from {
            config_map_ref {
              name = kubernetes_config_map.this.metadata[0].name
            }
          }
          env_from {
            secret_ref {
              name = kubernetes_secret.this.metadata[0].name
            }
          }
          liveness_probe {
            tcp_socket {
              port = "http"
            }
            initial_delay_seconds = 10
            period_seconds        = 20
          }
          readiness_probe {
            tcp_socket {
              port = "http"
            }
            initial_delay_seconds = 5
            period_seconds        = 10
          }
          security_context {
            allow_privilege_escalation = false
            read_only_root_filesystem  = true
            capabilities {
              drop = ["ALL"]
            }
          }
          resources {
            requests = var.resources.requests
            limits   = var.resources.limits
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "this" {
  metadata {
    name      = "roshan-harf-mcp"
    namespace = var.namespace
    labels    = local.app_labels
  }
  spec {
    selector = local.app_labels
    port {
      name        = "http"
      port        = var.service_port
      target_port = "http"
      protocol    = "TCP"
    }
    type = "ClusterIP"
  }
}

resource "kubernetes_horizontal_pod_autoscaler_v2" "this" {
  count = var.autoscaling.enabled ? 1 : 0
  metadata {
    name      = "roshan-harf-mcp"
    namespace = var.namespace
    labels    = local.app_labels
  }
  spec {
    scale_target_ref {
      api_version = "apps/v1"
      kind        = "Deployment"
      name        = kubernetes_deployment.this.metadata[0].name
    }
    min_replicas = var.autoscaling.min_replicas
    max_replicas = var.autoscaling.max_replicas
    metric {
      type = "Resource"
      resource {
        name = "cpu"
        target {
          type                = "Utilization"
          average_utilization = var.autoscaling.target_cpu
        }
      }
    }
  }
}

resource "kubernetes_ingress_v1" "this" {
  count = var.ingress.enabled ? 1 : 0
  metadata {
    name        = "roshan-harf-mcp"
    namespace   = var.namespace
    labels      = local.app_labels
    annotations = var.ingress.annotations
  }
  spec {
    ingress_class_name = var.ingress.class_name
    rule {
      host = var.ingress.host
      http {
        path {
          path      = "/"
          path_type = "Prefix"
          backend {
            service {
              name = kubernetes_service.this.metadata[0].name
              port {
                number = var.service_port
              }
            }
          }
        }
      }
    }
  }
}
