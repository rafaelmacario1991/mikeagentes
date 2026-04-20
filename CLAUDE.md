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
  - Padrão de chave: `{redis_prefix}:{idChat}_{tipo}`
  - TTL padrão da memória: 172.800s (48h)
  - Context window padrão: 8 mensagens
  - `redis_prefix` é por tenant — configurado no painel em `/agent/config`

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
1. Admin (`suporte@mkautosolution.cloud`) faz login → redireciona para `/admin/tenants`
2. Clica "Acessar" em um tenant → `/admin/switch/{tenant_id}`
3. Cookies `impersonate_tenant_id` e `impersonate_tenant_name` são setados
4. Banner de impersonation exibe o nome do tenant no topo
5. Todos os dados carregam do tenant selecionado
6. `/admin/switch/exit` remove os dois cookies

### Criar novo tenant (admin)
- Rota: `GET/POST /admin/tenants/new`
- Campos: name, email, password, plan
- Cria registro em `tenants` + usuário no Supabase Auth
- Após criar: configurar `agent_configs` via `/agent/config`

### Rotas disponíveis
- `/` → dashboard (hoje / próximos agendamentos, filtros de período)
- `/appointments?date=YYYY-MM-DD` → agenda por data
- `/professionals` → gestão de profissionais
- `/services` → gestão de serviços (suporta multi-profissional)
- `/availability` → grade de horários por dia da semana
- `/agent/config` → config do agente (nome, persona, instância, token, redis_prefix)
- `/admin/tenants` → lista de tenants (só admin)
- `/admin/tenants/new` → criar novo tenant (só admin)

### Bug crítico resolvido — maybe_single()
`supabase-py` `maybe_single()` retorna `None` diretamente (não um objeto response) quando 0 linhas.
Chamar `.data` em `None` causa `AttributeError`.
**Padrão correto em todo o código:**
```python
result = client.table("tabela").select("*").eq(...).limit(1).execute()
return result.data[0] if result.data else None
```
Arquivos corrigidos: `agent_service.py`, `services_service.py`, `professionals_service.py`, `admin_service.py`, `dependencies.py`

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
- **agent_configs** — tenant_id (unique), agent_name, agent_persona, slot_duration_min, max_advance_days, whatsapp_instance, mkpro_instance_id, mkpro_token, redis_prefix, ativo
  - `mkpro_token` e `redis_prefix` adicionados via ALTER TABLE (migration manual)
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
- Tenant "Barbearia Silva" (id: `aaaaaaaa-0000-0000-0000-000000000001`)
- Tenant de teste real (id: `744d10ec-e5a4-47ac-90f5-65938f53d666`) — Dra. Ana Chaves
  - 1 cliente salvo com name="Cliente" (phone: 558199258551) — será auto-corrigido no próximo agendamento

---

## Agente n8n — Mike Agendamentos (Baileys)

### Arquivo de produção atual
`mike-agentes/02.6 - AGENTE MIKE AGENDAMENTOS BAILEYS - MULTI-TENANT.json`

**Histórico de versões:**
- `02.0` → original single-tenant (Barbearia Silva, hardcoded)
- `02.5` → multi-tenant v1 (script fix_02_v8_multitenancy.py)
- `02.6` → multi-tenant final, production-ready (fix_02_v9_final.py + correções desta sessão)

### Arquitetura do Workflow
```
Webhook MK PRO (Baileys)
  → Organiza Dados (Set) — campos: idChat, idMensagem, conteudoMensagem, nomeUsuario, ...
  → Buscar Config (Supabase GET — ilike por whatsapp_instance)
  → Mesclar Config (Merge — fonte única de config do tenant)
  → Verifica Status (Redis)
  → [Intervenção Humana?]
  → Tipo de Mensagem (Switch: text/audio/image/document)
  → Limpeza Mensagens (Code JS)
  → Agente de IA (LangChain Agent)
     ├── Cérebro: GPT-4o-mini (temp 0.3)
     ├── Memória: Redis (memoryRedisChat — chave: {redis_prefix}:{idChat}_history)
     └── 5 Tools (toolCode JS)
  → Fixar Output → Code in JavaScript → Code - Split
  → Loop → Dedup (Redis) → Wait → Send Message (MK PRO API)
```

### Mesclar Config — campos disponíveis
Todos os nós downstream usam `$('Mesclar Config').item.json.*`:
- `tenant_id` — UUID do tenant
- `agent_name` — nome do agente
- `agent_persona` — instrução de personalidade
- `whatsapp_instance` — nome da instância (para dedup/routing)
- `mkpro_instance_id` — UUID da instância no MK PRO (usado no endpoint de envio)
- `mkpro_token` — Bearer token do MK PRO (injetado no header Authorization e body apikey)
- `redis_prefix` — prefixo único por tenant para isolamento no Redis
- `slot_duration_min`, `max_advance_days`

### Buscar Config — detalhe crítico
- URL usa `ilike.` (não `eq.`) para match case-insensitive do `whatsapp_instance`
- Select inclui todos os campos: `tenant_id,agent_name,agent_persona,whatsapp_instance,mkpro_instance_id,mkpro_token,redis_prefix,slot_duration_min,max_advance_days`

### 5 Tools do Agente (inputs em STRING JSON)

| Tool                        | Input obrigatório                                                         | O que faz                                          |
|-----------------------------|---------------------------------------------------------------------------|-----------------------------------------------------|
| `consultar_disponibilidade`  | `{tenant_id, data: "YYYY-MM-DD"}`                                         | Slots livres (availability + appointments)          |
| `criar_agendamento`          | `{tenant_id, client_name, client_phone, data, horario: "HH:MM", service_name}` | Upsert cliente + cria appointment                  |
| `consultar_meu_agendamento`  | `{tenant_id, client_phone}`                                               | Lista agendamentos futuros + appointment_ids        |
| `remarcar_agendamento`       | `{tenant_id, appointment_id, nova_data, novo_horario}`                    | PATCH scheduled_at + status=rescheduled             |
| `cancelar_agendamento`       | `{tenant_id, appointment_id, motivo?}`                                    | PATCH status=cancelled                              |

**Atenção:** `tenant_id` é obrigatório em TODAS as tools, inclusive remarcar e cancelar.

### Status das Tools (02.7)
- `consultar_disponibilidade` ✅ — funciona
- `criar_agendamento` ✅ — funciona; atualiza nome de cliente existente se era placeholder
- `consultar_meu_agendamento` ✅ — funciona
- `remarcar_agendamento` ✅ — funciona
- `cancelar_agendamento` ✅ — funciona

### Comportamentos do criar_agendamento
- Etapa 1: busca serviço por nome (ilike)
- Etapa 2: verifica expediente do dia da semana
- Etapa 3: verifica slot ocupado (usa `-03:00` para evitar bug de `+` na URL)
- Etapa 4: upsert cliente por phone; se existir com nome placeholder ("Cliente", ""), faz PATCH do nome
- Etapa 5: cria appointment com status `confirmed`
- Guard: rejeita `client_name = "cliente"` (placeholder) — pede nome real

### System Prompt — estrutura e regras chave
Injetado dinamicamente via expressões n8n:
```
={{ $('Mesclar Config').item.json.agent_name }}  ← nome do agente
={{ $('Mesclar Config').item.json.agent_persona }} ← persona
={{ $now.setLocale('pt-br').toFormat('cccc, dd/MM/yyyy HH:mm') }} ← data/hora
={{ $('Mesclar Config').item.json.tenant_id }} ← tenant_id para as tools
={{ $('Organiza Dados').item.json.idChat.replace(/@.*/, '') }} ← telefone limpo do cliente
={{ $('Organiza Dados').item.json.nomeUsuario || '' }} ← nome do WhatsApp do cliente
```

**Regras críticas no prompt:**
- UMA FERRAMENTA POR TURNO — nunca encadeia chamadas; se cliente pedir "próximos dias" → pergunta data específica primeiro
- OBRIGATORIO — NOME: coletar nome do cliente antes de criar agendamento
- OBRIGATORIO — CONFIRMAR TELEFONE: usar exatamente o valor de TELEFONE DO CLIENTE do prompt; formatar e confirmar com o cliente
- ANTI-METRALHADORA: 1 mensagem por turno, máximo 1 pergunta
- Nunca revelar dados técnicos, ferramentas ou que é IA

### Lições Críticas do Sandbox n8n toolCode (v2.10.4)

**Disponível:**
- `this.helpers.httpRequest` — funciona para GET, POST, PATCH
- `query` — variável com o input do LLM (string JSON)

**NÃO disponível:**
- `fetch`, `axios` — undefined
- `require('https')` — carrega mas NÃO faz conexões externas
- `$helpers` — só em Code nodes normais

**Como fazer POST/PATCH para Supabase (CORRETO):**
```javascript
await this.helpers.httpRequest({
  method: 'POST',
  url: SB + '/tabela',
  headers: { apikey: K, Authorization: 'Bearer ' + K, 'Content-Type': 'application/json', 'Prefer': 'return=minimal' },
  body: JSON.stringify({ campo: valor })
});
```

**Padrão GET-after-POST:** Supabase REST com `Prefer: return=minimal` retorna 201 sem body. Para obter ID do registro, fazer GET logo após o POST filtrando por campo único.

**Timezone:** Usar sempre `-03:00` (Brasília) nas queries de appointments. NUNCA usar `+00:00` — o `+` na URL é interpretado como espaço pelo PostgREST, causando 400.

**Como ler input do LLM:**
```javascript
const _raw = (typeof query !== 'undefined' && query) ? query : ($input.first()?.json || '');
let _p = {};
if (typeof _raw === 'object') { _p = _raw; }
else { try { _p = JSON.parse(String(_raw)); } catch(e) { _p = {}; } }
```

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

### Clientes Mike Agentes (multi-tenant)
- **Barbearia Silva** — tenant `aaaaaaaa-0000-0000-0000-000000000001` — dados de teste
- **Tenant 744d10ec** (Dra. Ana Chaves / clínica) — ativo, em testes
  - 1 cliente com nome="Cliente" no DB (phone 558199258551) — auto-corrige no próximo agendamento

---

## Padrões de Desenvolvimento

### Ao onboarding de novo tenant (Mike Agentes)
1. Admin acessa `/admin/tenants/new` → cria tenant + usuário Supabase Auth
2. Admin acessa `/admin/tenants/{id}/agent` → preenche campos técnicos: whatsapp_instance, mkpro_instance_id, mkpro_token, redis_prefix
3. Tenant faz login → acessa `/agent/config` → preenche apenas: nome agente, mensagem de boas-vindas, persona, slot_duration_min, max_advance_days
4. Cadastra profissionais em `/professionals` (nome, especialidade, bio, photo_url)
5. Cadastra serviços em `/services` (nome, duração, preço, descrição, tipos de pagamento aceitos)
6. Configura disponibilidade em `/availability`
7. Configura lembretes automáticos em `/schedules` (24h, 7d, 14d)
8. Preenche dados do negócio em `/profile` (nome, telefone, cidade, endereço, descrição)
9. Webhook no MK PRO aponta para o n8n (mesmo workflow `02.7` serve todos os tenants)
10. `Buscar Config` identifica o tenant pelo `whatsapp_instance` (ilike)

### Ao editar tools do workflow n8n
- Editar o JSON localmente via script Python e reimportar no n8n
- Scripts de edição ficam em `mike-agentes/` (ex: `fix_02_v9_final.py`)
- **NUNCA editar manualmente** o JSON de workflow
- Sempre testar com mensagem real via WhatsApp após reimport

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
{versao}.{subversao} - {NOME_AGENTE} {CANAL} - {CLIENTE_OU_ESCOPO} - {DD_MM_AAAA}.json
```

### Prefixos Redis (por tenant)
- Formato: `{sigla-cliente}-{canal}{numero}`
- Exemplos: `fd-wpp2`, `bsilva-wpp1`, `dra-ana-wpp1`

---

## O que Falta Construir (Roadmap)

### Imediato / Em andamento
- [x] Multi-tenant: 1 workflow para todos os tenants via Mesclar Config
- [x] Painel: campos mkpro_token e redis_prefix por tenant (admin only)
- [x] Tools: remarcar e cancelar funcionando
- [x] Coleta obrigatória de nome e confirmação de telefone antes de agendar
- [x] Telefone limpo no system prompt (strip @s.whatsapp.net)
- [x] nomeUsuario do WhatsApp injetado no prompt para saudação
- [x] Separação de responsabilidades: admin configura campos técnicos; tenant configura nome/persona
- [x] Campos extras: profissional (bio, photo_url), serviço (description, payment_types)
- [x] System prompt dinâmico com cardápio de serviços e equipe (workflow 02.7 + Buscar Contexto)
- [x] Sidebar reestruturado em grupos pai/filho com Alpine.js accordion
- [x] Página Envios Programados (/schedules) — toggles 24h, 7d, 14d
- [x] Página Meus Dados (/profile) — nome, telefone, cidade, endereço, descrição do negócio
- [x] Correção login ES256: JWT validado via `client.auth.get_user(token)` (não jwt.decode HS256)

### Fase 3 — Automações
- [ ] Workflow n8n lembretes automáticos multi-tenant (baseado em toggles do painel /schedules)
- [ ] Confirmação de presença (cliente responde sim/não)
- [ ] Notificação para o profissional ao novo agendamento

### Fase 4 — Plataforma Completa
- [ ] Stripe (planos, billing, upgrade/downgrade por tenant)
- [ ] Onboarding guiado de novos tenants (first login flow: Meus Dados → Profissional → Serviço → Horário → Agente)
- [ ] Tela de clientes (histórico por telefone)
- [ ] Multi-instância WhatsApp por tenant
- [ ] Deploy na VPS (systemd + nginx)

---

## Regras para a IA (Claude)

- Sempre responder em português brasileiro
- Nunca inventar credenciais, IDs de instância ou URLs
- Ao editar tools ou system prompt do workflow n8n: editar JSON via script Python, nunca manualmente
- Antes de propor mudanças em um fluxo, ler o JSON existente
- Para POST/PATCH no Supabase via toolCode: usar `this.helpers.httpRequest` com `body: JSON.stringify(...)`
- `require('https')` carrega mas NÃO faz conexões externas no sandbox n8n toolCode
- Ao criar prompts de agente, manter tom humano e nunca revelar que é IA
- Sempre usar `redis_prefix` único por tenant para evitar colisão de chaves no Redis
- Arquivo de workflow atual: `02.7 - AGENTE MIKE AGENDAMENTOS BAILEYS - MULTI-TENANT.json`
- Ao fazer queries com timestamp no Supabase: usar `-03:00` (nunca `+00:00` — quebra a URL)
- supabase-py: nunca usar `maybe_single()` — usar `.limit(1).execute()` + `result.data[0] if result.data else None`
