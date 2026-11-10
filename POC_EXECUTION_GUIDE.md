# Guia de Execução da Prova de Conceito (PoC): Token Tracker (FinOps de IA)

Este documento estabelece o roteiro técnico e executivo para a implantação da Prova de Conceito (PoC) da plataforma **Token Tracker**, com foco em governança orçamentária, transparência financeira (*Chargeback*) e controle de custos de Inteligência Artificial Generativa.

---

## 1. Visão Geral e Arquitetura Técnica

O **Token Tracker** opera como um pedágio inteligente (*Smart AI Gateway*) posicionado entre as aplicações corporativas e os provedores de modelos de linguagem (Anthropic Claude, OpenAI, Google Gemini, DeepInfra, etc.).

```
                                      ┌────────────────────────────────────────────────────────┐
                                      │              Aplicações / IDEs / Agentes               │
                                      │  (Claude CLI, Kiro, Cursor, Scripts Python, Backends)  │
                                      └──────────────────────────┬─────────────────────────────┘
                                                                 │ HTTP POST /v1/messages ou
                                                                 │ HTTP POST /v1/chat/completions
                                                                 │ Headers: X-Department-ID, X-User-ID
                                                                 ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   TOKEN TRACKER GATEWAY (Go 1.24 / FastAPI)                          │
│                                                                                                      │
│  1. Ingress & Identificação:                                                                         │
│     - Extração de tenant, departamento e usuário via Headers/IP.                                     │
│     - Estimativa de tokens no payload: ~1 token / 4 caracteres (Prompt + Contexto).                  │
│                                                                                                      │
│  2. Avaliação de Orçamento em Tempo Real:                                                            │
│     - Consulta O(1) no Redis para saldo da quota do departamento.                                    │
│     - Se saldo excedido (100%): Intercepta e responde HTTP 429 ("Monthly budget cap exceeded").      │
│     - Se alerta (80% a 99%): Registra flag `budget_warning=true` e prossegue.                        │
│                                                                                                      │
│  3. Forwarding & Streaming Proxy:                                                                    │
│     - Encaminhamento com injeção segura de credenciais de cofre (Vaulted API Keys).                  │
│     - Streaming SSE transparente (Zero latência perceptível ao usuário).                             │
└───────────────────┬────────────────────────────────────────────────────────────┬─────────────────────┘
                    │                                                            │
                    ▼                                                            ▼
    ┌───────────────────────────────┐                            ┌───────────────────────────────┐
    │     Redis 7 (In-Memory)       │                            │  TimescaleDB / PostgreSQL 15  │
    │  - Quotas por departamento    │                            │  - Histórico de chamadas      │
    │  - Contadores atômicos        │                            │  - Métricas de geração        │
    │  - Bloqueio em < 1ms          │                            │  - Auditoria & Chargeback     │
    └───────────────────────────────┘                            └───────────────┬───────────────┘
                                                                                 │
                                                                                 ▼
                                                                 ┌───────────────────────────────┐
                                                                 │      Frontend Angular 19      │
                                                                 │  - Dashboard de Chargeback    │
                                                                 │  - Gráficos de Projeção USD   │
                                                                 │  - Gestão de Quotas e Teto    │
                                                                 └───────────────────────────────┘
```

---

## 2. Modelo de Rateio Departamental (*Chargeback*)

Para a demonstração da PoC, são configurados quatro centros de custo com limites orçamentários mensais no banco de dados e Redis:

| Departamento | ID de Referência | Quota Mensal (USD) | Nível de Alerta (80%) | Política em 100% |
| :--- | :--- | :--- | :--- | :--- |
| **Tecnologia & TI** | `dept-ti-01` | $ 1.500,00 | $ 1.200,00 | Alerta aos gestores |
| **Marketing & Criação** | `dept-mkt-02` | $ 600,00 | $ 480,00 | Bloqueio Preventivo (HTTP 429) |
| **Recursos Humanos** | `dept-rh-03` | $ 250,00 | $ 200,00 | Bloqueio Preventivo (HTTP 429) |
| **Vendas & SDRs** | `dept-vendas-04` | $ 400,00 | $ 320,00 | Bloqueio Preventivo (HTTP 429) |

---

## 3. Fases de Implementação da PoC (10 Dias Úteis)

### Fase 1: Observabilidade Passiva (Dias 1 a 4)
* **Objetivo:** Estabelecer a linha de base (*baseline*) de consumo sem gerar atrito ou interrupções.
* **Operação:** O gateway opera em modo de auditoria total (`was_enforceable=false`), registrando tokens de entrada/saída, modelos utilizados e latência.
* **Resultado:** Descoberta do gasto real diário e identificação de *Shadow AI*.

### Fase 2: Alertas e Notificações Preventivas (Dias 5 a 7)
* **Objetivo:** Informar as lideranças de negócio antes que o teto financeiro seja violado.
* **Operação:** Quando o contador atinge 80% da quota, o sistema injeta o cabeçalho `X-Budget-Warning: true` e emite evento de webhook para os canais de FinOps.
* **Resultado:** Gestores podem ajustar o ritmo de uso ou solicitar suplementação orçamentária prévia.

### Fase 3: Governança Ativa e Bloqueio Preventivo (Dias 8 a 10)
* **Objetivo:** Garantir a disciplina orçamentária do CFO sem risco de estouro de fatura (*Hard Enforcement*).
* **Operação:** Ao atingir 100% da quota, o gateway rejeita imediatamente as novas chamadas do departamento com erro HTTP 429 em formato padronizado.
* **Resultado:** Previsibilidade financeira de 100% no fechamento contábil.

---

## 4. Roteiro Prático de Teste e Validação (Quick Start)

### 4.1. Subindo a infraestrutura local
```bash
cd token-tracker
docker compose up --build -d
```

### 4.2. Cenário 1: Chamada de rotina dentro do orçamento
```bash
curl -X POST http://localhost:8000/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "X-Project-ID: 00000000-0000-0000-0000-000000000000" \
  -H "X-Source: curl-test" \
  -d '{
    "model": "claude-3-haiku-20240307",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "Olá, resuma em uma frase o objetivo de FinOps."}]
  }'
```
*Retorno esperado:* HTTP 200 OK com o texto gerado e débito registrado no TimescaleDB.

### 4.3. Cenário 2: Simulação de estouro de orçamento (Bloqueio 429)
Quando a conta ou usuário ultrapassa o limite orçamentário configurado em `budgets`:
```bash
curl -X POST http://localhost:8000/v1/messages \
  -H "Content-Type: application/json" \
  -H "X-User-ID: 11111111-1111-1111-1111-111111111111" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "messages": [{"role": "user", "content": "Analise detalhada com alto consumo de contexto..."}]
  }'
```
*Retorno imediato (sem gastar tokens na API externa):*
```json
{
  "type": "error",
  "error": {
    "type": "rate_limit_error",
    "message": "Budget limit ($250.00) exceeded."
  }
}
```

---

## 5. Indicadores de Sucesso (KPIs de ROI)

1. **Previsibilidade Financeira:** Redução de variância orçamentária de IA de ±45% para menos de 2%.
2. **Tempo de Atribuição de Custos:** Redução de 5 dias úteis (fechamento contábil manual) para visualização em tempo real (< 1 segundo).
3. **Economia em Desperdícios:** Estimativa de 20% a 35% de economia direta através da identificação de loops em scripts e consultas redundantes.
