#!/bin/bash

# Script de Limpeza para Cluster Sandbox
# Argus Agent - Remoção Completa

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

# Confirmar ação
confirm_cleanup() {
    echo -e "${YELLOW}⚠️  ATENÇÃO: Esta operação irá remover COMPLETAMENTE o Argus Agent do cluster sandbox.${NC}"
    echo -e "${YELLOW}   Isso inclui:${NC}"
    echo -e "${YELLOW}   • Todos os pods, services, ingress${NC}"
    echo -e "${YELLOW}   • Todos os volumes persistentes (dados serão perdidos)${NC}"
    echo -e "${YELLOW}   • Todos os secrets e configmaps${NC}"
    echo -e "${YELLOW}   • O namespace argus${NC}"
    echo ""
    read -p "Tem certeza que deseja continuar? (digite 'yes' para confirmar): " confirmation
    
    if [ "$confirmation" != "yes" ]; then
        log "Operação cancelada pelo usuário"
        exit 0
    fi
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
        success "Namespace argus encontrado"
        return 0
    else
        warning "Namespace argus não encontrado"
        return 1
    fi
}

# Remover release do Helm
remove_helm_release() {
    log "Removendo release do Helm..."
    
    if helm list -n argus | grep -q argus-agent; then
        helm uninstall argus-agent -n argus
        success "Release do Helm removida"
    else
        warning "Release do Helm não encontrada"
    fi
}

# Remover recursos restantes
remove_remaining_resources() {
    log "Removendo recursos restantes..."
    
    # Remover ingress
    if kubectl get ingress -n argus &> /dev/null; then
        kubectl delete ingress --all -n argus
        success "Ingress removidos"
    fi
    
    # Remover services
    if kubectl get services -n argus &> /dev/null; then
        kubectl delete services --all -n argus
        success "Services removidos"
    fi
    
    # Remover deployments
    if kubectl get deployments -n argus &> /dev/null; then
        kubectl delete deployments --all -n argus
        success "Deployments removidos"
    fi
    
    # Remover PVCs
    if kubectl get pvc -n argus &> /dev/null; then
        kubectl delete pvc --all -n argus
        success "PVCs removidos"
    fi
    
    # Remover secrets
    if kubectl get secrets -n argus &> /dev/null; then
        kubectl delete secrets --all -n argus
        success "Secrets removidos"
    fi
    
    # Remover configmaps
    if kubectl get configmaps -n argus &> /dev/null; then
        kubectl delete configmaps --all -n argus
        success "ConfigMaps removidos"
    fi
}

# Remover namespace
remove_namespace() {
    log "Removendo namespace argus..."
    
    if kubectl get namespace argus &> /dev/null; then
        kubectl delete namespace argus
        success "Namespace argus removido"
    else
        warning "Namespace argus não encontrado"
    fi
}

# Verificar limpeza
verify_cleanup() {
    log "Verificando limpeza..."
    
    # Verificar se o namespace foi removido
    if kubectl get namespace argus &> /dev/null; then
        warning "Namespace argus ainda existe"
        kubectl get all -n argus
    else
        success "Namespace argus removido com sucesso"
    fi
    
    # Verificar releases do Helm
    if helm list -n argus | grep -q argus-agent; then
        warning "Release do Helm ainda existe"
        helm list -n argus
    else
        success "Release do Helm removida com sucesso"
    fi
}

# Mostrar resumo
show_summary() {
    log "Resumo da limpeza:"
    echo ""
    echo "✅ Operações realizadas:"
    echo "  • Release do Helm removida"
    echo "  • Todos os recursos do namespace removidos"
    echo "  • Namespace argus removido"
    echo ""
    echo "⚠️  Dados perdidos:"
    echo "  • Todos os volumes persistentes foram removidos"
    echo "  • Dados do PostgreSQL foram perdidos"
    echo "  • Dados do ChromaDB foram perdidos"
    echo ""
    echo "🔄 Para fazer um novo deploy:"
    echo "  • Execute: ./scripts/deploy-sandbox.sh"
    echo ""
}

# Função principal
main() {
    log "Iniciando limpeza do Argus Agent no cluster sandbox..."
    echo ""
    
    # Confirmar ação
    confirm_cleanup
    
    # Verificar pré-requisitos
    check_prerequisites
    
    # Verificar namespace
    if ! check_namespace; then
        warning "Namespace argus não encontrado. Nada para limpar."
        exit 0
    fi
    
    # Remover release do Helm
    remove_helm_release
    
    # Remover recursos restantes
    remove_remaining_resources
    
    # Remover namespace
    remove_namespace
    
    # Verificar limpeza
    verify_cleanup
    
    # Mostrar resumo
    show_summary
    
    success "Limpeza concluída com sucesso! 🧹"
}

# Executar função principal
main "$@"
