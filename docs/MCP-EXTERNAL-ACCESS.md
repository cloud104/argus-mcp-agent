# Acesso Externo ao MCP Server

O MCP Server pode ser exposto externamente via Ingress, permitindo que outros serviços e aplicações acessem as ferramentas do Argus Agent.

## Configuração

### Helm Values

O Ingress do MCP Server é configurado separadamente do Ingress da aplicação principal:

```yaml
ingress:
  # Aplicação principal
  app:
    enabled: true
    hosts:
      - host: argus.example.com
        paths:
          - path: /
            pathType: Prefix
    tls:
      - secretName: argus-app-tls
        hosts:
          - argus.example.com

  # MCP Server (acesso externo às ferramentas)
  mcpServer:
    enabled: true
    hosts:
      - host: mcp.argus.example.com
        paths:
          - path: /
            pathType: Prefix
    tls:
      - secretName: argus-mcp-tls
        hosts:
          - mcp.argus.example.com
```

### DNS

Configure os seguintes registros DNS:

**Desenvolvimento:**
```
# /etc/hosts
127.0.0.1 argus-dev.local
127.0.0.1 mcp.argus-dev.local
```

**Staging/Produção:**
```
argus-staging.example.com      A    <INGRESS-IP>
mcp-staging.example.com        A    <INGRESS-IP>

argus.example.com              A    <INGRESS-IP>
mcp.argus.example.com          A    <INGRESS-IP>
```

## Segurança

### Rate Limiting

O MCP Server possui rate limiting mais restritivo:

```yaml
# Staging
nginx.ingress.kubernetes.io/rate-limit: "10"  # 10 req/s

# Produção
nginx.ingress.kubernetes.io/rate-limit: "20"  # 20 req/s
```

### Autenticação Básica (Recomendado para Produção)

1. **Criar secret com credenciais:**
   ```bash
   htpasswd -c auth mcp-user
   kubectl create secret generic mcp-basic-auth \
     --from-file=auth \
     --namespace=argus-production
   ```

2. **Habilitar no Ingress:**
   ```yaml
   ingress:
     mcpServer:
       annotations:
         nginx.ingress.kubernetes.io/auth-type: basic
         nginx.ingress.kubernetes.io/auth-secret: mcp-basic-auth
         nginx.ingress.kubernetes.io/auth-realm: "MCP Server - Authentication Required"
   ```

### Whitelist de IPs (Opcional)

Restringir acesso a IPs específicos:

```yaml
ingress:
  mcpServer:
    annotations:
      nginx.ingress.kubernetes.io/whitelist-source-range: "10.0.0.0/8,192.168.0.0/16"
```

## Uso

### Endpoints Disponíveis

**MCP Server (via Ingress):**
```
https://mcp.argus.example.com/
https://mcp.argus.example.com/mcp/
```

**Aplicação Principal:**
```
https://argus.example.com/
```

### Teste de Conectividade

```bash
# Desenvolvimento (sem SSL)
curl http://mcp.argus-dev.local/

# Produção (com SSL)
curl https://mcp.argus.example.com/

# Com autenticação básica
curl -u mcp-user:password https://mcp.argus.example.com/
```

### Uso com MCP Client Externo

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

# Configuração para MCP Server externo
config = {
    "argus": {
        "transport": "http",
        "url": "https://mcp.argus.example.com/mcp/",
        # Se usar autenticação básica:
        "headers": {
            "Authorization": "Basic <base64-encoded-credentials>"
        }
    }
}

client = MultiServerMCPClient(config)
tools = await client.get_tools()
```

## Ambientes

### Development
- **App:** http://argus-dev.local
- **MCP:** http://mcp.argus-dev.local
- **Segurança:** Básica (apenas Ingress)

### Staging
- **App:** https://argus-staging.example.com
- **MCP:** https://mcp-staging.example.com
- **Segurança:** SSL + Rate Limiting (10 req/s)

### Production
- **App:** https://argus.example.com
- **MCP:** https://mcp.argus.example.com
- **Segurança:** SSL + Rate Limiting (20 req/s) + Auth Básica (recomendado)

## Monitoramento

### Logs do Ingress

```bash
# Ver logs do NGINX Ingress
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx -f

# Filtrar por MCP Server
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx -f | grep mcp
```

### Métricas

O Ingress expõe métricas Prometheus:
```
nginx_ingress_controller_requests{host="mcp.argus.example.com"}
nginx_ingress_controller_request_duration_seconds{host="mcp.argus.example.com"}
```

## Troubleshooting

### Problema: 502 Bad Gateway

```bash
# Verificar se o MCP Server está rodando
kubectl get pods -n argus-production -l app=argus-mcp-server

# Verificar logs do MCP Server
kubectl logs -n argus-production -l app=argus-mcp-server --tail=50
```

### Problema: 503 Service Unavailable

```bash
# Verificar o serviço
kubectl get svc -n argus-production argus-mcp-server

# Verificar endpoints
kubectl get endpoints -n argus-production argus-mcp-server
```

### Problema: Certificate Issues

```bash
# Verificar certificado
kubectl describe certificate -n argus-production argus-mcp-tls

# Verificar cert-manager logs
kubectl logs -n cert-manager -l app=cert-manager -f
```

## Boas Práticas

1. ✅ **Use HTTPS em produção** (cert-manager)
2. ✅ **Habilite autenticação básica** em produção
3. ✅ **Configure rate limiting** apropriado
4. ✅ **Monitore acesso** via logs e métricas
5. ✅ **Use whitelist de IPs** quando possível
6. ⚠️ **Não exponha MCP Server** sem autenticação em produção
7. ⚠️ **Cuidado com CORS** se acessar de browsers

## Exemplo Completo de Deploy

```bash
# 1. Criar autenticação básica
htpasswd -c auth mcp-admin
kubectl create secret generic mcp-basic-auth \
  --from-file=auth \
  --namespace=argus-production

# 2. Deploy com Helm
helm install argus-prod ./helm/argus-agent \
  --namespace argus-production \
  --values k8s/prod/values.yaml \
  --set ingress.mcpServer.enabled=true \
  --set ingress.mcpServer.hosts[0].host=mcp.argus.example.com

# 3. Verificar Ingress
kubectl get ingress -n argus-production

# 4. Testar
curl -u mcp-admin:password https://mcp.argus.example.com/
```

## Referências

- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [Cert-Manager](https://cert-manager.io/)
- [Basic Authentication](https://kubernetes.github.io/ingress-nginx/examples/auth/basic/)
- [Rate Limiting](https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/annotations/#rate-limiting)
