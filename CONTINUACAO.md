# Prompt de Continuação - Argus Log Explorer UI

## Contexto do Projeto

**Projeto:** Argus Agent - Assistente SRE AI-powered para análise de logs TOTVS Protheus
**Branch Atual:** `feature/containerization`
**Último Commit:** `5aea38e` - feat: Add modern UI with copy buttons and responsive design

## Arquitetura Implementada

### Stack Tecnológica
- **Frontend:** Angular 18 (standalone components) + NGINX
- **Backend API:** FastAPI + Python 3.13
- **MCP Server:** FastMCP (porta 8002)
- **Banco Auth:** PostgreSQL 16
- **Vector DB:** ChromaDB
- **Containerização:** Docker + Docker Compose

### Estrutura de Diretórios
```
argus-mcp-agent/
├── api/              # FastAPI application
├── mcp-server/       # FastMCP tool server
├── ui/               # Angular 18 frontend
├── docs/             # Documentação
├── k8s/              # Kubernetes manifests (dev/staging/prod)
├── docker-compose.yml      # Produção
└── docker-compose.dev.yml  # Desenvolvimento
```

## O Que Foi Implementado Nesta Sessão

### 1. UI Moderno e Responsivo ✨

**Arquivos Principais Modificados:**
- `ui/src/app/features/log-explorer/log-explorer.component.html`
- `ui/src/app/features/log-explorer/log-explorer.component.scss` (12.58 kB)
- `ui/src/app/features/log-explorer/log-explorer.component.ts`
- `ui/src/index.html` (TOTVS favicon e título)
- `ui/angular.json` (budget aumentado para 13kB)

**Melhorias Visuais:**

1. **Sistema de Sombras Modernas**
   - Sombras em camadas sutis: `0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)`
   - Elevação dinâmica ao hover
   - Backdrop filters (`blur(10px)`)

2. **Transições Suaves**
   - Timing function: `cubic-bezier(0.4, 0, 0.2, 1)`
   - Transições em todos elementos interativos
   - Animações: `fadeIn`, `fadeInUp`, `expandDown`, `checkmark`

3. **Estados Interativos**
   - Log entries: `transform: translateX(2px)` ao hover
   - Botões: `transform: translateY(-2px)` + shadow increase
   - Cards: elevação progressiva
   - Inputs: lift effect ao focus

4. **Responsividade**
   - Breakpoints: 1024px, 768px, 480px
   - Mobile: stack vertical, chart reduzido (80px)
   - Tablet: painel 60vw
   - Desktop: painel 550px

### 2. Botões de Copiar nas Análises 📋

**Funcionalidade:**
- Aparecem ao hover sobre títulos de seções
- Ícone de clipboard SVG
- Feedback visual ao copiar (verde por 2 segundos)
- `copyToClipboard(text, event)` method no component
- Previne propagação de eventos

**Implementação CSS:**
```scss
.copy-btn {
  opacity: 0;  // Invisível por padrão
  transition: all 0.2s ease;

  summary:hover & {
    opacity: 0.6;  // Sutil ao hover na seção
  }

  &:hover {
    opacity: 1 !important;
    background: rgba(102, 126, 234, 0.1);
    color: #667eea;
  }

  &.copied {
    color: #10b981;  // Verde ao copiar
  }
}
```

### 3. Layout Otimizado

**Spacing Compacto:**
- Header padding: `sm` (reduzido de `md`)
- Chart height: 100px (reduzido de 160px)
- Log entries: padding `xs/sm`, margin `2px` (reduzido de 8px)
- Font sizes: 11px-13px (reduzido de 12-14px)

**One-Line Log Layout:**
```html
<div class="log-header">
  <button class="ai-explain-btn">AI</button>
  <span class="log-time">{{ log.timestamp }}</span>
  <span class="log-severity">{{ log.severity }}</span>
  <span class="log-appname">{{ log.appname }}</span>
  <span class="log-message">{{ log.message }}</span>  <!-- flex: 1 -->
</div>
```

## Estado Atual da Aplicação

### ✅ Funcionando
- **Frontend:** http://localhost:8080 (NGINX - produção)
- **API:** http://localhost:8000 (FastAPI - healthy)
- **PostgreSQL:** localhost:5433 (healthy)
- **MCP Server:** localhost:8002 (healthy)
- **ChromaDB:** localhost:8001

### Credenciais Padrão
- **Usuário:** `admin`
- **Senha:** `admin123`

### Como Rodar

**Produção (docker-compose.yml):**
```bash
docker-compose up -d
# Acesse: http://localhost:8080
```

**Desenvolvimento (docker-compose.dev.yml):**
```bash
docker-compose -f docker-compose.dev.yml up -d
# API: http://localhost:8000
# MCP: http://localhost:8002
# Frontend local: npm start (porta 4200)
```

## Configurações Importantes

### Environment Variables (.env)
```bash
POSTGRES_HOST=postgres  # Nome do serviço no docker-compose
POSTGRES_PORT=5432
POSTGRES_USER=argus
POSTGRES_PASSWORD=argus123
POSTGRES_DB=argus_auth

MCP_SERVER_URL=http://argus-mcp-server:8002/mcp/
```

### Angular Build Budgets
```json
{
  "type": "anyComponentStyle",
  "maximumWarning": "13kB",
  "maximumError": "18kB"
}
```

## Problemas Conhecidos e Soluções

### 1. Conectividade Docker
**Problema:** VPN pode bloquear acesso às portas do Docker do host
**Solução:** Desabilitar VPN ou rodar frontend localmente (`npm start`)

### 2. MCP Server Unhealthy
**Problema:** Healthcheck falha por falta de Elasticsearch externo
**Solução:** Ignorar (não é crítico para frontend) ou configurar ES_HOST

### 3. Permissões no Dev Mode
**Problema:** `PermissionError` no watchfiles (--reload)
**Solução:** Usar imagens de produção ou ajustar permissões de volumes

## Próximos Passos Sugeridos

### Features Pendentes
1. **Integração Elasticsearch Real**
   - Configurar conexão com ES de produção
   - Testar busca de logs real

2. **Testes da Análise IA**
   - Validar fluxo completo: busca → análise → chat
   - Testar botões de copiar com dados reais

3. **Melhorias UX**
   - Loading states mais elaborados
   - Tratamento de erros mais visual
   - Tooltips informativos

4. **Performance**
   - Lazy loading de componentes
   - Virtual scrolling para grandes listas de logs
   - Cache de análises

### Melhorias Técnicas
1. **Testes**
   - Unit tests (Jest)
   - E2E tests (Playwright)
   - Testes de acessibilidade

2. **CI/CD**
   - GitHub Actions para build e deploy
   - Testes automáticos
   - Deploy automático para K8s

3. **Monitoramento**
   - Métricas de uso
   - Error tracking (Sentry)
   - Performance monitoring

## Comandos Úteis

### Git
```bash
git status
git log --oneline -5
git diff HEAD~1
```

### Docker
```bash
# Ver logs
docker logs argus-ui -f
docker logs argus-api -f

# Restart específico
docker-compose restart api

# Rebuild
docker-compose up --build -d

# Cleanup
docker-compose down
docker system prune -f
```

### Frontend
```bash
cd ui/

# Dev local
npm start

# Build produção
npm run build

# Testes
npm test
```

## Referências de Código

### Componente Principal
**Localização:** `ui/src/app/features/log-explorer/log-explorer.component.ts`

**Métodos Importantes:**
- `copyToClipboard(text, event)` - Copia texto com feedback visual
- `onExplainLog(message, index)` - Explica linha de log com IA
- `onDeepDive()` - Análise profunda dos logs
- `startChat()` - Inicia chat sobre análise

### Estilos Principais
**Localização:** `ui/src/app/features/log-explorer/log-explorer.component.scss`

**Classes Chave:**
- `.copy-btn` - Botão de copiar (linha 620)
- `.log-entry` - Entrada de log com animação (linha 218)
- `.analysis-section` - Seções expansíveis (linha 529)
- `.chat-bubble` - Mensagens do chat (linha 691)
- `.insights-panel` - Painel lateral (linha 441)

### Tema TOTVS
**Localização:** `ui/src/styles/_totvs-theme.scss`

**Variáveis:**
- Cores: `$totvs-primary`, `$totvs-gray-*`
- Spacing: `$totvs-spacing-xs` até `$totvs-spacing-2xl`
- Sombras: `$totvs-shadow-sm` até `$totvs-shadow-xl`
- Border radius: `$totvs-radius-sm` até `$totvs-radius-xl`

## Documentação Adicional

**Arquivos de Referência:**
- `CLAUDE.md` - Instruções para Claude Code
- `docs/AUTH_TESTING.md` - Testes de autenticação
- `docs/DEPLOY_GUIDE.md` - Guia de deploy
- `docs/DOCKER_PUSH_GUIDE.md` - Como fazer push de imagens

## Para o Próximo Claude

**Perguntas a Fazer ao Usuário:**
1. Qual funcionalidade específica quer implementar?
2. Precisa conectar ao Elasticsearch real ou usar dados mock?
3. Quer continuar melhorando UI ou focar no backend?
4. Há issues específicos para resolver?

**Arquivos a Ler Primeiro:**
1. `ui/src/app/features/log-explorer/log-explorer.component.ts`
2. `ui/src/app/features/log-explorer/log-explorer.component.scss`
3. `api/main.py` (se trabalhar no backend)
4. `.env` (configurações)

**Comandos para Verificar Estado:**
```bash
docker ps
docker-compose logs api --tail 20
curl http://localhost:8000/health/ready
curl http://localhost:8080
```

---

**Última atualização:** 2025-10-04
**Branch:** `feature/containerization`
**Commit:** `5aea38e`
