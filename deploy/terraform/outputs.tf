output "namespace" {
  description = "Namespace the server is deployed into."
  value       = var.namespace
}

output "service_name" {
  description = "Name of the Kubernetes Service."
  value       = kubernetes_service.this.metadata[0].name
}

output "service_port" {
  description = "Service port for the streamable-http transport."
  value       = var.service_port
}

output "in_cluster_url" {
  description = "In-cluster URL for the MCP server."
  value       = "http://${kubernetes_service.this.metadata[0].name}.${var.namespace}.svc.cluster.local:${var.service_port}"
}

output "configured_instances" {
  description = "Names of the configured Harf instances."
  value       = keys(var.instances)
}

output "ingress_host" {
  description = "Ingress host (if enabled)."
  value       = var.ingress.enabled ? var.ingress.host : null
}
