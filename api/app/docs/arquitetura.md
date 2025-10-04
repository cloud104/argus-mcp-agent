Documento de Arquitetura e Implementação: Argus Agent SRE
1.0 Visão Geral e Arquitetura
O Argus Agent é um assistente SRE de nível profissional para a análise de ambientes TOTVS Protheus. A arquitetura desacoplada consiste em:

Frontend: Uma aplicação Single-Page em Angular com a biblioteca de componentes @dev-tcloud/tcloud-ui, focada em apresentar dashboards interativos e visualizações de dados complexas.

Backend: Um servidor Python/FastAPI que orquestra os fluxos de análise. O núcleo do backend é um agente construído com LangGraph, que utiliza um conjunto de ferramentas para interagir com as fontes de dados.

Servidor de Ferramentas: Um processo Python independente que expõe as ferramentas de acesso a dados (Elasticsearch, InfluxDB) através de um endpoint MCP (Model Context Protocol), garantindo a separação de responsabilidades.

2.0 Fluxo de Interação do Utilizador
O caso de uso principal é desenhado para ser intuitivo e poderoso, evoluindo de uma visão geral para uma investigação profunda.

Login e Seleção de Ambiente:

O utilizador autentica-se (admin / totvs$!OLAKGA>#$)$@).

A interface apresenta um campo de busca (tc-rev-search-input-container) para que o utilizador insira um ccode e topology_id.

Dashboard de Análise Inicial (Automático e Interativo):

Após a seleção do ambiente, o agente executa a Análise Inicial.

O backend gera um objeto JSON estruturado com uma análise rica, baseada nos logs.

O frontend Angular renderiza um dashboard completo com componentes T-Cloud.

Interatividade (KPIs como Filtros): Os cartões de KPI (ex: "2 Erros Críticos") são clicáveis. Ao clicar, o frontend refaz a busca de logs com um filtro adicional (ex: severity: "ERROR") e atualiza dinamicamente os outros componentes do dashboard (timeline, trechos de log) para refletir a seleção.

Análise Profunda (Investigação Assistida por IA):

O dashboard inicial apresenta um botão de "Análise Profunda" que pode ser dinâmico. Se a análise inicial detetar um padrão específico (ex: múltiplos deadlocks), o botão pode sugerir "Investigar Deadlocks de Thread".

Ao ser acionado, um fluxo de agente LangGraph mais complexo é iniciado.

Este fluxo utiliza ferramentas avançadas para gerar novas visualizações, como grafos de relação ou análises de causa raiz (Ishikawa), que são adicionadas ao dashboard como novos componentes.

3.0 Definição das Ferramentas e Implementação
As ferramentas são o coração do agente, permitindo-lhe aceder e processar dados.

3.1 Ferramentas de Coleta de Dados
get_environment_info(ccode: str, topology: str): Mapeia o ambiente para a infraestrutura. Saída: { "machines": ["..."], "es_index": "..." }.

search_es_logs(index: str, time_window: str, filters: dict): Busca logs no Elasticsearch. O parâmetro filters permite refinar a busca.

query_influxdb(query: str): Executa uma query Flux diretamente no InfluxDB.

search_zendesk(query: str): Procura por tickets relevantes no Zendesk.

3.2 Ferramentas de Análise e IA (Análise Profunda)
extract_protheus_entities(logs: list):

Implementação: Usa um LLM para ler logs e extrair entidades do Protheus (Usuários, Threads, Funções, BTs, Conexões).

Saída: Um JSON com listas de entidades, ex: {"users": ["CSALVA7"], "threads": [1080, 584], ...}.

run_anomaly_detection(data: list): Aplica um algoritmo de ML (ex: Isolation Forest) para detetar anomalias.

generate_ishikawa_analysis(context: str): Usa um LLM para preencher um diagrama de causa raiz.

generate_relationship_graph(entities: dict):

Implementação: Usa um LLM para inferir as relações entre as entidades extraídas.

Saída: Um JSON estruturado para uma biblioteca de grafos, como a Vis.js. Exemplo:

{
  "nodes": [
    {"id": "user_CSALVA7", "label": "Usuário CSALVA7"},
    {"id": "bt_recalc", "label": "BT Recálculo Custo"}
  ],
  "edges": [
    {"from": "user_CSALVA7", "to": "bt_recalc", "label": "executou"}
  ]
}


4.0 Frontend e Visualizações
4.1 Validação da Resposta do LLM
Problema: O modelo de linguagem por vezes retorna o template do prompt em vez dos dados.

Solução: O JavaScript do frontend deve implementar uma verificação robusta. Antes de tentar renderizar o dashboard, ele deve validar a resposta da API:

Verificar se a resposta é um objeto JSON válido.

Verificar se as chaves principais esperadas (ex: resumo_geral, kpis) existem.

Se a validação falhar, deve exibir um componente de erro T-Cloud, informando que "A análise da IA não pôde ser processada", em vez de renderizar um template quebrado.

4.2 Biblioteca de Grafos (Análise Profunda)
Para renderizar os grafos de relação, o frontend Angular deverá integrar uma biblioteca de visualização de grafos.

Recomendação: Vis.js (vis-network) é uma excelente opção por ser poderosa e interativa.

5.0 Anexo: Análise Inicial Detalhada (Exemplo de Saída)
A análise inicial deve ir além de "tudo ok". O objetivo é gerar um relatório em texto (renderizado a partir do JSON) que se pareça com isto:

Severidade: INFORMACIONAL
Resumo: Sistema operando normalmente com processamento de recálculo de custo médio concluído com sucesso. Servidor apresenta métricas saudáveis de memória e conectividade SSL/TLS funcionando adequadamente.
Agregados: 1 host ativo (203089-core-instance), 2 usuários conectados, múltiplos logs de BTMonitor indicando processamento de transação "

EST
 PROCESSA O RECALCULO DO CUSTO MEDIO" com 149.8 segundos de duração.
Hipóteses:

Conectividade com banco de dados Oracle e License Server está estável.

Uso de memória está dentro de parâmetros normais (350MB resident, 954MB addressed).
Próximos passos: Nenhuma ação necessária.

6.0 Anexo: Métricas Disponíveis no InfluxDB
Oracle: oracle_cx_top_queries_memory, oracle_cx_top_queries_duration

SQL Server: sqlserver_cx_top10_cpu_usage_queries, sqlserver_cx_top10_memory_usage_queries

TSS: cx_tss_notas_pendentes_count, cx_tss_notas_recusadas_count, cx_tss_notas_erro_count

Windows: win_cpu, win_mem, win_disk, win_net

Linux: cpu, mem, disk, diskio, net

Protheus: protheus_process, app_data_size_history