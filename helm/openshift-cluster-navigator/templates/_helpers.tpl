{{/*
Expand the name of the chart.
*/}}
{{- define "openshift-cluster-navigator.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "openshift-cluster-navigator.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "openshift-cluster-navigator.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "openshift-cluster-navigator.labels" -}}
helm.sh/chart: {{ include "openshift-cluster-navigator.chart" . }}
{{ include "openshift-cluster-navigator.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "openshift-cluster-navigator.selectorLabels" -}}
app.kubernetes.io/name: {{ include "openshift-cluster-navigator.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "openshift-cluster-navigator.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "openshift-cluster-navigator.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the name of the secret to use for authentication
*/}}
{{- define "openshift-cluster-navigator.secretName" -}}
{{- if .Values.auth.existingSecret }}
{{- .Values.auth.existingSecret }}
{{- else }}
{{- include "openshift-cluster-navigator.fullname" . }}-auth
{{- end }}
{{- end }}

{{/*
Create the name of the config secret
*/}}
{{- define "openshift-cluster-navigator.configSecretName" -}}
{{- include "openshift-cluster-navigator.fullname" . }}-config
{{- end }}

{{/*
Create the name of the PVC
*/}}
{{- define "openshift-cluster-navigator.pvcName" -}}
{{- if .Values.persistence.existingClaim }}
{{- .Values.persistence.existingClaim }}
{{- else }}
{{- include "openshift-cluster-navigator.fullname" . }}-data
{{- end }}
{{- end }}
