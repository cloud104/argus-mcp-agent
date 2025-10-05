#!/bin/bash

# Script de Deploy para Cluster Sandbox
# Argus Agent - Deploy Automatizado

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar pré-requisitos
check_prerequisites() {
    log "Verificando pré-requisitos..."
    
    # Verificar kubectl
    if ! command -v kubectl &> /dev/null; then
        error "kubectl não encontrado. Instale o kubectl primeiro."
        exit 1
    fi
    
    # Verificar helm
    if ! command -v helm &> /dev/null; then
        error "helm não encontrado. Instale o Helm 3.x primeiro."
        exit 1
    fi
    
    # Verificar contexto kubectl
    if ! kubectl config current-context &> /dev/null; then
        error "Nenhum contexto kubectl configurado."
        exit 1
    fi
    
    success "Pré-requisitos verificados"
}

# Verificar se o namespace existe
check_namespace() {
    log "Verificando namespace argus..."
    
    if kubectl get namespace argus &> /dev/null; then
        success "Namespace argus já existe"
    else
        log "Criando namespace argus..."
        kubectl create namespace argus
        success "Namespace argus criado"
    fi
}

# Aplicar secrets
apply_secrets() {
    log "Aplicando secrets..."
    
    if [ -f "k8s/dev/secret.yaml" ]; then
        kubectl apply -f k8s/dev/secret.yaml
        success "Secrets aplicados"
    else
        error "Arquivo k8s/dev/secret.yaml não encontrado"
        exit 1
    fi
}

# Verificar secrets
verify_secrets() {
    log "Verificando secrets..."
    
    # Verificar se os secrets foram criados
    if kubectl get secret argus-secrets -n argus &> /dev/null; then
        success "Secret argus-secrets encontrado"
    else
        error "Secret argus-secrets não encontrado"
        exit 1
    fi
    
    if kubectl get secret gcr-json-key -n argus &> /dev/null; then
        success "Secret gcr-json-key encontrado"
    else
        error "Secret gcr-json-key não encontrado"
        exit 1
    fi
}

# Deploy via Helm
deploy_helm() {
    log "Fazendo deploy via Helm..."
    
    # Navegar para o diretório do Helm chart
    cd helm/argus-agent
    
    # Verificar se o chart existe
    if [ ! -f "Chart.yaml" ]; then
        error "Chart.yaml não encontrado. Verifique se está no diretório correto."
        exit 1
    fi
    
    # Fazer deploy
    helm upgrade --install argus-agent . \
        --namespace argus \
        --create-namespace \
        --values values-sandbox.yaml \
        --wait \
        --timeout=10m
    
    success "Deploy via Helm concluído"
    
    # Voltar ao diretório original
    cd ../..
}

# Verificar status do deploy
verify_deploy() {
    log "Verificando status do deploy..."
    
    # Verificar pods
    log "Verificando pods..."
    kubectl get pods -n argus
    
    # Verificar services
    log "Verificando services..."
    kubectl get services -n argus
    
    # Verificar ingress
    log "Verificando ingress..."
    kubectl get ingress -n argus
    
    # Verificar PVCs
    log "Verificando PVCs..."
    kubectl get pvc -n argus
    
    success "Verificação do deploy concluída"
}

# Verificar saúde dos pods
check_pod_health() {
    log "Verificando saúde dos pods..."
    
    # Aguardar pods ficarem prontos
    log "Aguardando pods ficarem prontos..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argus-agent -n argus --timeout=300s
    
    # Verificar status dos pods
    local failed_pods=$(kubectl get pods -n argus --field-selector=status.phase=Failed --no-headers | wc -l)
    
    if [ "$failed_pods" -gt 0 ]; then
        warning "Alguns pods falharam. Verificando logs..."
        kubectl get pods -n argus --field-selector=status.phase=Failed
    else
        success "Todos os pods estão rodando"
    fi
}

# Mostrar informações de acesso
show_access_info() {
    log "Informações de acesso:"
    echo ""
    echo "🌐 URLs de Acesso:"
    echo "  • UI Principal: https://sandbox.tcloud-devops.cloudtotvs.com.br/"
    echo "  • API: https://sandbox.tcloud-devops.cloudtotvs.com.br/api/"
    echo "  • MCP Server: https://sandbox.tcloud-devops.cloudtotvs.com.br/mcp/"
    echo ""
    echo "🔧 Comandos Úteis:"
    echo "  • Ver pods: kubectl get pods -n argus"
    echo "  • Ver logs: kubectl logs -n argus deployment/argus-agent-app"
    echo "  • Port forward: kubectl port-forward -n argus service/argus-agent-app 8000:8000"
    echo ""
    echo "📊 Monitoramento:"
    echo "  • Status: kubectl get all -n argus"
    echo "  • Recursos: kubectl top pods -n argus"
    echo "  • Eventos: kubectl get events -n argus"
}

# Função principal
main() {
    log "Iniciando deploy do Argus Agent no cluster sandbox..."
    echo ""
    
    # Verificar pré-requisitos
    check_prerequisites
    
    # Verificar namespace
    check_namespace
    
    # Aplicar secrets
    apply_secrets
    
    # Verificar secrets
    verify_secrets
    
    # Deploy via Helm
    deploy_helm
    
    # Verificar deploy
    verify_deploy
    
    # Verificar saúde dos pods
    check_pod_health
    
    # Mostrar informações de acesso
    show_access_info
    
    success "Deploy concluído com sucesso! 🎉"
}

# Executar função principal
main "$@"
