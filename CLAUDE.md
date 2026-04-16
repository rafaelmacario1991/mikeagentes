# Projeto Agentes de IA — MK AutoSolution

## Contexto Geral

Repositório dos fluxos n8n e do painel web **Mike Agentes** — produto SaaS white-label de agendamento via WhatsApp para prestadores de serviço.

- **Empresa:** MK AutoSolution — Gestão de Tráfego Pago e Automações
- **Dono:** Rafael Macario
- **Instagram:** @mkautosolution | **WhatsApp:** 81 983138789
- **Site:** https://www.mkautosolution.cloud
- **GitHub:** https://github.com/rafaelmacario1991/mikeagentes

---

## Infraestrutura (Self-hosted VPS)

| Serviço            | URL / Endereço                                  | Observação                                  |
|--------------------|-------------------------------------------------|---------------------------------------------|
| n8n                | VPS própria                                     | Orquestrador principal dos fluxos           |
| MK PRO (Z-PRO)     | `mkproapi.mkautosolution.cloud`                 | Plataforma de atendimento multi-canal       |
| Evolution API      | `evolution.agentesmkpro.cloud`                  | Envio de alertas via WhatsApp (instâncias)  |
| Redis              | Credencial n8n: `MK Pro - Redis`                | Memória, histórico, timers, dedup           |
| Supabase           | `myofgasezxvbyryenpeq.supabase.co`             | DB dedicado Mike Agentes                    |
| Google Drive       | Armazenamento de arquivos e assets              |                                             |
| Google Sheets      | Logging de leads, registros de atendimento      |                                             |

---

## Stack de Desenvolvimento

### Orquestração
- **n8n** — plataforma principal de desenvolvimento de fluxos (self-hosted)
- Fluxos exportados/importados em `.json`

### Mensageria
- **Baileys (MK PRO)** — WhatsApp via QR code — canal atual do agente de agendamento
- **WABA Cloud API** (Facebook Graph API v18/v21) — WhatsApp Business oficial (Caleb/FD Veículos)
- **Evolution API** — instâncias WhatsApp para alertas internos
- **MK PRO (Z-PRO)** — plataforma de atendimento instalada na VPS; endpoint de envio:
  ```
  POST https://mkproapi.mkautosolution.cloud/v2/api/external/{instance-id}
  ```

### LLMs
| Uso                          | Modelo                          |
|------------------------------|---------------------------------|
| Agente Agendamento (Mike)    | GPT-4o-mini (OpenAI API)        |
| Cérebro do Agente SDR (Caleb)| GPT-4o-mini (OpenAI API)        |
| Análise de imagem            | Gemini 2.5 Flash (ou Flash Lite)|
| Transcrição de áudio         | Gemini 2.5 Flash (ou Flash Lite)|
| Extração de documentos       | Gemini 2.5 Flash                |

### Memória e Estado
- **Redis** — armazenamento de sessão dos agentes
  - Padrão de chave: `{prefixoRedis}:{idChat}_{tipo}`
  - TTL padrão da memória: 172.800s (48h)
  - Context window padrão: 8 mensagens

### Banco de Dados (Mike Agentes)
- **Supabase** — projeto `myofgasezxvbyryenpeq`
- Credenciais ficam apenas em `.env` (nunca no código)

---

## Produto: Mike Agentes

Agente de atendimento e agendamento via WhatsApp para prestadores de serviço (barbearias, clínicas, etc.). White-label: cada cliente (tenant) tem sua configuração isolada.

### Planos e Monetização (futuro)
- Starter: R$97/mês — 300 agendamentos/mês, 1 instância WhatsApp
- Pro: R$197/mês — 1.000 agendamentos/mês + lembretes automáticos
- Agency: R$397/mês — ilimitado + multi-agenda + dashboard avançado

---

## Painel Web (FastAPI)

**Localização:** `mike-agentes/painel/`

### Rodar localmente
```bash
cd mike-agentes/painel
python run.py
# Acessa: http://localhost:8001
```
Matar antes de reiniciar: `taskkill /IM python.exe /F`

### Credenciais admin (desenvolvimento)
- Login: `suporte@mkautosolution.cloud` / `Deusebom12!`
- Tenant de teste: "Barbearia Silva" — `aaaaaaaa-0000-0000-0000-000000000001`

### Stack do Painel
- Backend: FastAPI + Jinja2 (SSR) + Python
- Frontend: HTML/CSS + Alpine.js
- Banco: Supabase Auth + PostgreSQL via supabase-py
- Tema: Dark "Control Room"

### Estrutura
```
mike-agentes/painel/
├── run.py
├── requirements.txt
├── .env                    ← NÃO commitar (gitignore)
└── app/
    ├── main.py             ← FastAPI app, AuthMiddleware, routers
    ├── config.py           ← Settings via pydantic-settings
    ├── dependencies.py     ← get_current_user, get_effective_tenant
    ├── auth/               ← login/logout + JWT decode
    ├── routers/            ← dashboard, agent, professionals, services,
    │                          availability, appointments, admin
    ├── services/           ← supabase_client + service layer para cada entidade
    └── templates/          ← base.html + templates por módulo
```

### Fluxo Admin (impersonation)
1. Admin (`suporte@mkautosolution.cloud`) faz login
2. Redireciona para `/admin/tenants`
3. Clica "Acessar" em um tenant → `/admin/switch/{tenant_id}`
4. Cookie `impersonate_tenant_id` é setado
5. Todos os dados carregam do tenant selecionado

### Rotas disponíveis
- `/` → dashboard (hoje / próximos agendamentos)
- `/appointments?date=YYYY-MM-DD` → agenda por data
- `/professionals` → gestão de profissionais
- `/services` → gestão de serviços (suporta multi-profissional)
- `/availability` → grade de horários por dia da semana
- `/agent` → config do agente (nome, persona, instância WhatsApp)
- `/admin/tenants` → lista de tenants (só admin)

---

## Schema Supabase (Mike Agentes)

Projeto: `myofgasezxvbyryenpeq`

### Convenções críticas (diferem do que o código Python esperava)
| Conceito                | Nome real no DB   |
|-------------------------|-------------------|
| `is_active`             | `ativo`           |
| `day_of_week`           | `weekday`         |
| `duration_minutes`      | `duration_min`    |
| `starts_at`             | `scheduled_at`    |
| `specialty`             | `role`            |

### Tabelas
- **tenants** — id, name, slug, phone, email, plan, ativo, stripe_*
- **agent_configs** — tenant_id (unique), agent_name, agent_persona, slot_duration_min, max_advance_days, whatsapp_instance, mkpro_instance_id, ativo
- **professionals** — tenant_id, name, role, ativo
- **services** — tenant_id, professional_id, name, duration_min, price, ativo
- **availability** — tenant_id, professional_id, weekday (0-6), start_time, end_time, ativo
- **appointments** — tenant_id, client_id, professional_id, service_id, scheduled_at (timestamptz), duration_min, status, notes, cancelled_reason, reminder_sent
  - Status válidos: `scheduled`, `confirmed`, `cancelled`, `rescheduled`, `completed`, `no_show`
- **clients** — tenant_id, name, phone, email, notes
- **blocked_dates** — tenant_id, professional_id, blocked_date, reason
- **rag_documents** — tenant_id, content, embedding (vector), metadata
- **agent_sessions** — tenant_id, client_phone, client_name, redis_key, ativo, expira_em
- **mike_notifications_log** — tenant_id, appointment_id, client_phone, type, status, sent_at

### Dados de teste no DB
- 1 tenant: "Barbearia Silva" (id: `aaaaaaaa-0000-0000-0000-000000000001`)
- 2 profissionais, 6 serviços, slots de disponibilidade configurados

---

## Agente n8n — Mike Agendamentos (Baileys)

**Arquivo atual:** `mike-agentes/02.0 - AGENTE MIKE AGENDAMENTOS BAILEYS - BARBEARIA SILVA - 16_04_2026.json`

### Arquitetura do Workflow
```
Webhook MK PRO (Baileys)
  → Organiza Dados (Set)
  → Mesclar Config (Supabase lookup por tenant)
  → Verifica Status (Redis)
  → [Intervenção Humana?]
  → Tipo de Mensagem (Switch: text/audio/image/document)
  → Limpeza Mensagens (Code JS)
  → Agente de IA (LangChain Agent)
     ├── Cérebro: GPT-4o-mini (temp 0.3)
     ├── Memória: Redis (memoryRedisChat)
     └── 5 Tools (toolCode JS)
  → Fixar Output → Code in JavaScript → Code - Split
  → Loop → Dedup (Redis) → Wait → Send Message (MK PRO API)
```

### 5 Tools do Agente
Todos são nós `@n8n/n8n-nodes-langchain.toolCode`.

| Tool                       | Input (STRING JSON)                                              | O que faz                                   |
|----------------------------|------------------------------------------------------------------|---------------------------------------------|
| `consultar_disponibilidade` | `{tenant_id, data: "YYYY-MM-DD"}`                               | Slots livres no dia (GET availability + appointments) |
| `criar_agendamento`         | `{tenant_id, client_name, client_phone, data, horario: "HH:MM"}` | Cria cliente (se novo) + appointment        |
| `consultar_meu_agendamento` | `{tenant_id, client_phone}`                                      | Lista agendamentos futuros do cliente       |
| `remarcar_agendamento`      | `{appointment_id, nova_data, novo_horario}`                      | Atualiza scheduled_at                       |
| `cancelar_agendamento`      | `{appointment_id, motivo}`                                       | Status → cancelled                          |

### Lições Críticas do Sandbox n8n toolCode (v2.10.4)

**Disponível:**
- `this.helpers.httpRequest` — funciona para GET e POST (body stringificado)
- `query` — variável com o input do LLM (string JSON)
- `require` — carrega módulo mas conexões de rede externas via `require('https')` NÃO funcionam

**NÃO disponível:**
- `$helpers` — só em Code nodes normais
- `fetch` — undefined
- `axios` — undefined
- `Buffer` / WebAPIs — instáveis

**Como fazer POST para Supabase (CORRETO):**
```javascript
// FUNCIONA — body como string JSON com Content-Type
await this.helpers.httpRequest({
  method: 'POST',
  url: SB + '/tabela',
  headers: { apikey: K, Authorization: 'Bearer ' + K, 'Content-Type': 'application/json', 'Prefer': 'return=minimal' },
  body: JSON.stringify({ campo: valor })
});

// NÃO FUNCIONA — require('https') falha silenciosamente na rede
// NÃO FUNCIONA — body como objeto (não stringificado)
```

**Como ler o input do LLM:**
```javascript
const _raw = (typeof query !== 'undefined' && query) ? query : ($input.first()?.json || '');
let _p = {};
if (typeof _raw === 'object') { _p = _raw; }
else { try { _p = JSON.parse(String(_raw)); } catch(e) { _p = {}; } }
```

**Padrão GET-after-POST:** O Supabase REST sem `Prefer: return=representation` retorna corpo vazio (201). Para obter o ID do registro criado, fazer GET logo após o POST.

### IDs dos nós (após último import)
- `consultar_disponibilidade`: `e157d2de-9e22-4cf0-9f86-d25c83db22c5`
- `criar_agendamento`: `70f6637f-572f-4f07-a8a5-3ac5a5d43369`
- `consultar_meu_agendamento`: `bd7cf4bb-cad9-4840-ad8c-3608630e4fee`
- `remarcar_agendamento`: `6508333c-d404-4dd7-b9d5-10402e23c1b8`
- `cancelar_agendamento`: `55d31f20-3f26-47aa-a2ec-3a08f8cac28c`
- `Agente de IA`: `e43445d6-2e65-4c44-aac1-d76366d6fd42`

### Status das Tools
- `consultar_disponibilidade` ✅ — funciona
- `criar_agendamento` ✅ — funciona (v4: httpRequest com body stringificado)
- `consultar_meu_agendamento` ⚠️ — não testado pós-correção
- `remarcar_agendamento` ⚠️ — não testado
- `cancelar_agendamento` ⚠️ — não testado

---

## Arquitetura Padrão dos Agentes SDR (Caleb / FD Veículos)

```
Webhook WABA
  → Organiza Dados (Set)
  → Verifica Status (Redis GET)
  → [Intervenção Humana?]
  → Tipo de Mensagem (Switch)
     ├── Texto   → direto para o agente
     ├── Áudio   → Download Graph → Gemini Transcribe → agente
     ├── Imagem  → Download Graph → Gemini Analyze → agente
     └── PDF     → Download → Extract → agente
  → Adicionar ao Histórico (Redis PUSH)
  → Busca Histórico (Redis GET)
  → Ainda é a última mensagem? (dedup)
  → Agente de IA (LangChain Agent)
     ├── Cérebro LLM (GPT-4o-mini)
     ├── Memória Redis (memoryRedisChat)
     └── RAG Tool (Supabase Vector Store)
  → Limpeza Mensagens (Code JS)
  → Code Split
  → Wait → Send Message (MK PRO API)
  → Eventos do Agente (Switch)
     ├── Alerta SDR Simulação
     └── Alerta SDR Agendamento
  → Google Sheets Append
```

---

## Projetos / Clientes Ativos

### FD Veículos — Agente Caleb
- **Pasta:** `fd-veiculos/`
- **Fluxo:** `02.3 - CALEB WABA - FD VEÍCULOS - 02_03_2026 (1).json`
- **Canal:** WABA
- **Função:** SDR / Consultor de Vendas de Seminovos
- **Instância MK PRO:** `def17a4b-1470-4362-ba38-f63f0637c174`
- **Prefixo Redis:** `fd-wpp2`
- **Status:** Ativo em produção

### Barbearia Silva — Agente Lucas (Mike Agentes)
- **Pasta:** `mike-agentes/`
- **Fluxo:** `02.0 - AGENTE MIKE AGENDAMENTOS BAILEYS - BARBEARIA SILVA - 16_04_2026.json`
- **Canal:** Baileys (MK PRO)
- **Função:** Agendamento via WhatsApp
- **Tenant ID:** `aaaaaaaa-0000-0000-0000-000000000001`
- **Status:** Funcionando — criar/consultar agendamento OK

---

## Padrões de Desenvolvimento

### Ao criar um novo agente de agendamento (Mike Agentes)
1. Criar tenant no Supabase (tenants + agent_configs)
2. Cadastrar profissionais, serviços e disponibilidade via painel
3. Importar o workflow base no n8n
4. Ajustar `Mesclar Config` para buscar config do tenant pelo número da instância
5. Configurar webhook no MK PRO apontando para o n8n

### Ao editar tools do workflow n8n
- Editar o JSON localmente (via Python script) e reimportar no n8n
- Scripts de edição ficam em `mike-agentes/` (ex: `fix_criar_v4.py`)
- Sempre testar com mensagem real via WhatsApp após reimport

### Scripts de manutenção do workflow
- Os arquivos `fix_criar_*.py` ficam no gitignore (são auxiliares de debug)
- Preservar sempre o JSON do workflow como fonte da verdade

### Limpeza de Mensagens
- Nó `Limpeza Mensagens` (Code JS) processa INPUT (mensagem do usuário)
- Nó `Code in JavaScript` processa OUTPUT (resposta do agente) — remove `__MK_EVENT:xxx__`

### Deduplicação
- `_last_msg_id` no Redis garante só a última mensagem é processada
- Evita resposta duplicada em mensagens rápidas

### Alertas para Rafael
- Instância Evolution: `MKAutosolution`
- Endpoint: `evolution.agentesmkpro.cloud/message/sendText/MKAutosolution`

---

## Convenções de Nomenclatura

### Fluxos n8n
```
{versao}.{subversao} - {NOME_AGENTE} {CANAL} - {CLIENTE} - {DD_MM_AAAA}.json
```

### Prefixos Redis
- Formato: `{cliente-sigla}-{canal}{numero}`
- Exemplo: `fd-wpp2`, `bsilva-wpp1`

---

## O que Falta Construir (Roadmap)

### Imediato
- [ ] Testar e corrigir tools: `remarcar_agendamento`, `cancelar_agendamento`, `consultar_meu_agendamento`
- [ ] Agente selecionar serviço correto pelo nome (atualmente pega `LIMIT 1`)
- [ ] Timezone: agendamentos armazenados em UTC — ajustar para horário de Brasília (UTC-3)

### Fase 3 — Automações
- [ ] Lembretes automáticos 24h e 1h antes via WhatsApp
- [ ] Confirmação de presença (cliente responde sim/não)

### Fase 4 — Plataforma Completa
- [ ] Stripe (planos, billing, upgrade/downgrade)
- [ ] Multi-instância WhatsApp por tenant
- [ ] Deploy na VPS
- [ ] Onboarding de novos tenants via painel

---

## Regras para a IA (Claude)

- Sempre responder em português brasileiro
- Nunca inventar credenciais, IDs de instância ou URLs
- Ao editar tools do workflow n8n: editar JSON via Python, nunca manualmente
- Antes de propor mudanças em um fluxo, ler o JSON existente
- Para POST no Supabase via toolCode: usar `this.helpers.httpRequest` com `body: JSON.stringify(...)`
- `require('https')` carrega mas NÃO faz conexões externas no sandbox n8n toolCode
- Ao criar prompts de agente, manter tom humano e nunca revelar que é IA
- Sempre usar `prefixoRedis` único para evitar colisão de chaves no Redis
