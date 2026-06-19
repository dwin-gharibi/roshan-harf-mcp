variable "namespace" {
  description = "Kubernetes namespace to deploy into."
  type        = string
  default     = "roshan-harf-mcp"
}

variable "create_namespace" {
  description = "Whether to create the namespace."
  type        = bool
  default     = true
}

variable "image" {
  description = "Container image (repository:tag)."
  type        = string
  default     = "roshan-harf-mcp:0.2.0"
}

variable "replicas" {
  description = "Number of replicas (ignored when autoscaling is enabled)."
  type        = number
  default     = 2
}

variable "default_instance" {
  description = "Harf instance used when a tool call omits 'instance'."
  type        = string
  default     = "default"
}

variable "log_level" {
  description = "Log level."
  type        = string
  default     = "INFO"
}

variable "instances" {
  description = "Map of Harf instance name to connection config."
  type = map(object({
    base_url   = optional(string, "https://harf.roshan-ai.ir")
    username   = optional(string)
    password   = optional(string)
    token      = optional(string)
    verify_ssl = optional(bool, true)
    timeout    = optional(number, 60)
  }))
  sensitive = true
  default = {
    default = {
      base_url = "https://harf.roshan-ai.ir"
    }
  }
}

variable "service_port" {
  description = "Service port for the streamable-http transport."
  type        = number
  default     = 8000
}

variable "ingress" {
  description = "Optional ingress configuration."
  type = object({
    enabled     = bool
    class_name  = optional(string, "nginx")
    host        = string
    annotations = optional(map(string), {})
  })
  default = {
    enabled = false
    host    = "roshan-harf-mcp.example.com"
  }
}

variable "autoscaling" {
  description = "Optional horizontal pod autoscaler configuration."
  type = object({
    enabled      = bool
    min_replicas = optional(number, 2)
    max_replicas = optional(number, 6)
    target_cpu   = optional(number, 80)
  })
  default = {
    enabled = false
  }
}

variable "resources" {
  description = "Container resource requests/limits."
  type = object({
    requests = optional(map(string), { cpu = "100m", memory = "128Mi" })
    limits   = optional(map(string), { cpu = "1", memory = "512Mi" })
  })
  default = {}
}
