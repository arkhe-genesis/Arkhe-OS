{{- define "arkhe.platform.annotations" -}}
{{- if eq .Values.platform.type "azure" }}
arkhe.azure.workload-identity: "true"
azure.workload.identity/use: "true"
{{- else if eq .Values.platform.type "gcp" }}
iam.gke.io/gcp-service-account: {{ .Values.platform.gcp.serviceAccount }}
{{- else if eq .Values.platform.type "oracle" }}
oci.oraclecloud.com/vault-id: {{ .Values.platform.oracle.vaultId }}
{{- end }}
{{- end -}}
