{{- define "arkhe.platform.values" -}}
{{- $platform := .Values.platform.type | default "kubernetes" -}}
{{- $values := dict -}}

{{- if eq $platform "azure" -}}
  {{- $_ := set $values "image.repository" "ghcr.io/arkhe-os/cert-operator-azure" -}}
  {{- $_ := set $values "replicaCount" 3 -}}
  {{- $_ := set $values "affinity.podAntiAffinity.requiredDuringSchedulingIgnoredDuringExecution"
    (list (dict
      "labelSelector" (dict "matchExpressions" (list (dict
        "key" "app.kubernetes.io/name"
        "operator" "In"
        "values" (list "arkhe-cert-operator")
      )))
      "topologyKey" "kubernetes.io/hostname"
    ))
  -}}
  {{- $_ := set $values "resources.limits.cpu" "1000m" -}}
  {{- $_ := set $values "resources.limits.memory" "512Mi" -}}

{{- else if eq $platform "gcp" -}}
  {{- $_ := set $values "image.repository" "ghcr.io/arkhe-os/cert-operator-gcp" -}}
  {{- $_ := set $values "replicaCount" 3 -}}
  {{- $_ := set $values "affinity.nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution"
    (dict "nodeSelectorTerms" (list (dict "matchExpressions" (list (dict
      "key" "cloud.google.com/gke-nodepool"
      "operator" "In"
      "values" (list "arkhe-system")
    )))))
  -}}
  {{- $_ := set $values "resources.limits.cpu" "1" -}}
  {{- $_ := set $values "resources.limits.memory" "512Mi" -}}

{{- else if eq $platform "apple" -}}
  {{- $_ := set $values "image.repository" "ghcr.io/arkhe-os/cert-operator-apple" -}}
  {{- $_ := set $values "replicaCount" 1 -}}  # Typically single-node on edge
  {{- $_ := set $values "nodeSelector" (dict "kubernetes.io/arch" "arm64") -}}
  {{- $_ := set $values "resources.limits.cpu" "500m" -}}
  {{- $_ := set $values "resources.limits.memory" "256Mi" -}}

{{- else if eq $platform "oracle" -}}
  {{- $_ := set $values "image.repository" "ghcr.io/arkhe-os/cert-operator-oracle" -}}
  {{- $_ := set $values "replicaCount" 3 -}}
  {{- $_ := set $values "affinity.nodeAffinity.preferredDuringSchedulingIgnoredDuringExecution"
    (list (dict
      "weight" 100
      "preference" (dict "matchExpressions" (list (dict
        "key" "oci.oraclecloud.com/fault-domain"
        "operator" "Exists"
      )))
    ))
  -}}
  {{- $_ := set $values "resources.limits.cpu" "1" -}}
  {{- $_ := set $values "resources.limits.memory" "512Mi" -}}
{{- end -}}

{{- /* Merge platform-specific values with base values */ -}}
{{- $merged := mergeOverwrite .Values $values -}}
{{- toYaml $merged -}}
{{- end -}}