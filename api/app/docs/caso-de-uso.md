Documento de Projeto: Argus Agent SRE Avançado
1.0 Visão Geral
O Argus Agent será um assistente SRE (Engenheiro de Fiabilidade de Sistemas) avançado, movido por IA, especializado na análise e diagnóstico de ambientes TOTVS Protheus. A aplicação irá fornecer dois níveis de análise através de uma interface de dashboard moderna e interativa, construída com Angular e componentes T-Cloud.

Análise Inicial: Um dashboard gerado automaticamente que fornece uma visão geral rica e informativa da saúde do sistema com base nos logs.

Análise Profunda: Um fluxo de investigação interativo que utiliza um agente LangGraph para cruzar dados de múltiplas fontes (logs, métricas, tickets), aplicar algoritmos de Machine Learning e gerar análises de causa raiz avançadas, como grafos de relação e diagramas de Ishikawa.

2.0 Caso de Uso Principal
O fluxo de interação do utilizador será o seguinte:

Login: O utilizador acede à aplicação e entra com as credenciais (admin / totvs$!OLAKGA>#$)$@).

Seleção de Ambiente: A interface apresenta um campo de busca onde o utilizador insere um ccode e topology_id.

Dashboard de Análise Inicial (Automático):

Imediatamente após a seleção, o agente é acionado.

Ele identifica as máquinas e o índice do Elasticsearch associado ao ambiente.

Executa a análise inicial.

Renderiza um dashboard completo na interface, com KPIs, timelines e um resumo analítico, sem necessidade de mais interação.

Ação de Análise Profunda (Interativa):

O dashboard inicial contém botões de ação dinâmicos. Por exemplo, se forem detetados erros, um botão "Investigar Erros Críticos" aparecerá.

Ao clicar, o utilizador inicia o fluxo de análise profunda. O agente executa uma investigação mais complexa, usando ferramentas avançadas.

O resultado (ex: um grafo de relação ou um diagrama de causa raiz) é exibido num novo componente, como um modal ou uma secção de dropdown, enriquecendo a visão do dashboard.

3.0 Arquitetura e Tecnologias
Frontend: Aplicação Single-Page construída em Angular, utilizando a biblioteca de componentes @dev-tcloud/tcloud-ui.

Backend: Servidor Python com FastAPI, orquestração de agentes com LangGraph.

Fontes de Dados:

Elasticsearch: Para logs de aplicação Protheus.

InfluxDB: Para métricas de performance (Oracle, SQL Server, Windows, Linux).

Zendesk (opcional): Para dados sobre tickets de suporte.

4.0 Definição das Ferramentas (As "Skills" do Agente)
Para executar as análises, o agente LangGraph terá acesso a um conjunto de ferramentas (funções) bem definidas:

get_environment_info(ccode: str, topology: str)

Função: Mapeia o ccode/topology para a infraestrutura.

Saída: Um objeto JSON com os nomes das máquinas e o nome do índice do Elasticsearch a ser consultado. (Pode ser um mock na fase inicial).

search_es_logs(index: str, time_window: str, query: str)

Função: Busca e retorna logs brutos do Elasticsearch.

query_influxdb(metric: str, time_window: str, filters: dict)

Função: Consulta métricas de séries temporais do InfluxDB. Essencial para a análise profunda.

search_zendesk(query: str)

Função: Procura por tickets relevantes no Zendesk.

extract_protheus_entities(logs: list)

Função: Usa um LLM para ler uma lista de logs e extrair entidades chave do Protheus (Usuários, Threads, Funções, Erros, etc.). Fundamental para os grafos de relação.

run_anomaly_detection(data: list)

Função: Aplica um algoritmo de Machine Learning (ex: Isolation Forest) a uma série temporal para detetar anomalias.

5.0 Fluxos de Análise (Workflows)
5.1 Workflow de Análise Inicial
Este fluxo é acionado automaticamente e tem como objetivo preencher o dashboard principal.

Passo 1: Coleta de Dados. O agente usa get_environment_info para encontrar o índice e search_es_logs para obter os logs brutos.

Passo 2: Agregação de KPIs. O backend processa os logs em Python para calcular KPIs básicos (contagem de erros, avisos, utilizadores únicos, threads ativas, etc.).

Passo 3: Síntese do Dashboard. O LLM recebe os logs brutos e os KPIs agregados. A sua tarefa é gerar um objeto JSON estruturado que representa o dashboard completo, incluindo resumos, hipóteses e timelines.

5.2 Sugestões para o Workflow de Análise Profunda
Este fluxo é mais complexo e pode ser adaptado com base no que se pretende investigar.

Análise de Grafo de Relação (Causa Raiz):

Gatilho: Utilizador clica para investigar um erro específico.

Extração de Entidades: O agente usa extract_protheus_entities nos logs em torno do erro.

Busca de Métricas: Usa query_influxdb para obter métricas de CPU, memória e queries de base de dados no mesmo timestamp.

Síntese do Grafo: O LLM recebe todas estas informações e gera um JSON com "nós" (as entidades) e "arestas" (as relações), que o frontend renderiza como um grafo interativo.

Deteção de Anomalias em Métricas:

Gatilho: Utilizador clica para investigar o "Uso de CPU".

Coleta de Série Temporal: O agente usa query_influxdb para obter a série temporal completa da métrica de CPU.

Execução do ML: Os dados são passados para a ferramenta run_anomaly_detection.

Visualização: O backend retorna a série temporal com os pontos de anomalia marcados. O frontend renderiza um gráfico de linhas com estes pontos destacados.

6.0 Estrutura de Dados (JSON Schema da API)
Para garantir a comunicação entre o frontend Angular e o backend, a API deve seguir um schema JSON bem definido.

Saída da /initial-analysis e /deep-dive:

{
  "dashboard_data": {
    "resumo_geral": {
      "titulo": "Análise do console_appserver.log",
      "periodo_analisado": "...",
      "severidade": "WARNING", // CRITICAL, WARNING, INFORMATIONAL
      "alerta_principal": "O principal padrão observado foi..."
    },
    "kpis": [
      {"metrica": "Erros Críticos", "valor": 2, "icone": "critical_errors"},
      {"metrica": "Avisos", "valor": 0, "icone": "warnings"}
    ],
    "categorizacao_problemas": [
      {"categoria": "Thread Issues", "ocorrencias": 1020, "descricao": "Problemas relacionados a deadlocks..."}
    ],
    "timeline_eventos": [
      {"timestamp": "2025-09-25T22:46:56Z", "nivel": "CRITICAL", "descricao": "Connection reset by peer..."}
    ],
    // ... outras chaves para grafos, etc.
  },
  "evidencias": {
    "logs_brutos": [...]
  }
}

Este documento deve servir como um guia sólido para o desenvolvimento do Argus Agent. Podemos agora discutir cada ponto em mais detalhe para refinar ainda mais o plano.