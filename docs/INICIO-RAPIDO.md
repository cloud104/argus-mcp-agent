# Guia de Início Rápido - Argus Agent

Coloque o Argus Agent em funcionamento em minutos.

## Pré-requisitos

- Python 3.13+
- Docker e Docker Compose (para desenvolvimento containerizado)
- kubectl e Helm (para deployment em Kubernetes)
- Tilt (opcional, para desenvolvimento aprimorado em K8s)

## 1. Configuração Inicial

```bash
# Clone o repositório
git clone <repository-url>
cd argus-mcp-agent

# Configure o ambiente
make setup

# Edite o .env com suas credenciais
nano .env  # ou vim, code, etc.
```

**Obrigatório no `.env`:**
```bash
# Pelo menos uma chave de API de LLM
OPENAI_API_KEY=sk-...

# Credenciais do Elasticsearch
ES_HOST=https://seu-elasticsearch-host
ES_USER=elastic
ES_PASSWORD=sua-senha
```

## 2. Escolha seu Método de Desenvolvimento

### Opção A: Desenvolvimento Local (Sem Containers)

**Mais rápido para testes iniciais:**

```bash
# Instale as dependências
source .venv/bin/activate
uv pip install -r requirements.txt

# Terminal 1: Inicie o servidor MCP
uvicorn tools.server:app --port 8002 --reload

# Terminal 2: Inicie a aplicação principal
uvicorn main:app --port 8000 --reload
```

**Acesso:**
- App: http://localhost:8000
- Servidor MCP: http://localhost:8002

---

### Opção B: Docker Compose (Recomendado para Desenvolvimento)

**Melhor para ambiente consistente:**

```bash
# Inicie todos os serviços
docker-compose up

# Ou com debugging
docker-compose -f docker-compose.dev.yml up

# Com ChromaDB standalone
docker-compose -f docker-compose.chromadb.yml up
```

**Acesso:**
- App: http://localhost:8000
- Servidor MCP: http://localhost:8002
- ChromaDB: http://localhost:8001 (se usar variante chromadb)

**Debugging:**
- Porta de debug da App: 5678
- Porta de debug do MCP Server: 5679

---

### Opção C: Tilt + Kubernetes (Melhor para Desenvolvimento K8s)

**Melhor para desenvolver em Kubernetes:**

```bash
# Certifique-se de que o .env está configurado
cat .env  # Verifique suas credenciais

# Inicie o Tilt
tilt up

# Pressione ESPAÇO ou visite http://localhost:10350
```

**Tilt automaticamente:**
- Lê o `.env` e cria secrets do K8s
- Constrói e faz deploy no Kubernetes
- Configura port forwarding
- Recarrega automaticamente ao mudar código

**Acesso:**
- App: http://localhost:8000 (via port-forward)
- Servidor MCP: http://localhost:8002 (via port-forward)
- UI do Tilt: http://localhost:10350

---

## 3. Verifique a Instalação

### Teste a API

```bash
# Verifique a app principal
curl http://localhost:8000/

# Verifique o servidor MCP
curl http://localhost:8002/
```

### Execute uma Análise Simples

```bash
curl -X POST http://localhost:8000/initial-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "msg": "Analisar logs",
    "index": "logs_protheus_v1",
    "window": "1h",
    "session_id": "test-session"
  }'
```

## 4. Workflow de Desenvolvimento

### Fazendo Alterações no Código

**Docker Compose:**
```bash
# Alterações no código são sincronizadas automaticamente (volume mount)
# Apenas edite e salve - uvicorn recarregará
```

**Tilt:**
```bash
# Alterações no código disparam rebuild e redeploy automático
# Acompanhe o progresso na UI do Tilt
```

### Executando Testes

```bash
# Docker Compose
docker-compose run --rm app pytest -v

# Ou use o Make
make test
```

### Formatação de Código

```bash
# Formate o código
make format

# Lint do código
make lint
```

### Visualizar Logs

**Docker Compose:**
```bash
docker-compose logs -f app
docker-compose logs -f mcp-server
```

**Tilt:**
```bash
# Use a UI do Tilt (http://localhost:10350)
# Ou via kubectl:
kubectl logs -n argus-dev -l app=argus-app -f
```

## 5. Tarefas Comuns

### Atualizar Dependências

```bash
# Adicione pacote ao requirements.txt
echo "novo-pacote==1.0.0" >> requirements.txt

# Docker Compose: Rebuild
docker-compose down
docker-compose up --build

# Tilt: Rebuilda automaticamente
```

### Mudar Configuração

```bash
# Edite os arquivos de config
vim config/models.json
vim config/settings.json

# Docker Compose: Restart
docker-compose restart

# Tilt: Reinicia pods automaticamente
```

### Atualizar Variáveis de Ambiente

```bash
# Edite o .env
vim .env

# Docker Compose: Restart
docker-compose down
docker-compose up

# Tilt: Restart
tilt down
tilt up
```

## 6. Solução de Problemas

### "Connection refused to MCP server"

```bash
# Verifique se o servidor MCP está rodando
curl http://localhost:8002/

# Docker Compose: Verifique os logs
docker-compose logs mcp-server

# Reinicie o servidor MCP
docker-compose restart mcp-server
```

### Erros de "Unauthorized" ou API Key

```bash
# Verifique se o .env tem as chaves corretas
grep OPENAI_API_KEY .env

# Certifique-se de que o .env foi carregado
docker-compose config | grep OPENAI

# Para Tilt, reinicie para recarregar .env
tilt down && tilt up
```

### Porta já em uso

```bash
# Encontre o que está usando a porta
lsof -i :8000

# Mate o processo ou mude a porta
docker-compose down
```

### Problemas com build do Docker

```bash
# Limpe e rebuilde
make clean-docker
docker-compose build --no-cache
docker-compose up
```

## 7. Próximos Passos

### Deploy em Produção

Veja o [Guia de Deployment](DEPLOYMENT.md) para:
- Construir imagens de produção
- Deploy no Kubernetes com Helm
- Configurar Ingress e SSL
- Configurar autoscaling

### Aprenda Mais

- [Guia de Variáveis de Ambiente](ENV-VARIABLES.md) - Configuração detalhada do .env
- [Guia de Containerização](README-CONTAINERIZATION.md) - Arquitetura Docker e K8s
- [Kubernetes README](../k8s/README.md) - Detalhes de deployment K8s
- [Documentação de Arquitetura](../app/docs/arquitetura.md) - Arquitetura do sistema

## Resumo

| Método | Melhor Para | Comando de Início | Acesso |
|--------|-------------|-------------------|--------|
| **Local** | Testes rápidos | `uvicorn main:app --reload` | localhost:8000 |
| **Docker Compose** | Desenvolvimento | `docker-compose up` | localhost:8000 |
| **Tilt** | Desenvolvimento K8s | `tilt up` | localhost:8000 |

**Recomendado:** Comece com Docker Compose para desenvolvimento, use Tilt quando trabalhar em features de K8s.
