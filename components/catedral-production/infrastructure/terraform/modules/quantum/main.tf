variable "regions" { type = any }
variable "qubit_architecture" { type = string }
variable "gate_fidelity_target" { type = number }
variable "coherence_time_target_ms" { type = number }
output "quantum_api_endpoint" { value = "https://quantum.internal" }
