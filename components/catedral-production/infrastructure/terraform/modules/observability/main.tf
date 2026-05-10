variable "regions" { type = list(string) }
variable "prometheus_retention_days" { type = number }
variable "loki_retention_days" { type = number }
variable "jaeger_sampling_rate" { type = number }
variable "alerting" { type = any }
