import json
import uuid

SB_URL    = "https://myofgasezxvbyryenpeq.supabase.co"
SB_KEY    = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im15b2ZnYXNlenh2YnlyeWVucGVxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjI3OTg5NiwiZXhwIjoyMDkxODU1ODk2fQ.fEJNZzZnlnJbasdEapSZa9b1DCApNjbtWDOKoHkE1uc"
TENANT_ID = "aaaaaaaa-0000-0000-0000-000000000001"
MKPRO_URL = "https://mkproapi.mkautosolution.cloud/v2/api/external/0df39b48-c373-4b11-87be-96d873c3ab97"
MKPRO_TKN = "Barear eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0ZW5hbnRJZCI6NywicHJvZmlsZSI6ImFkbWluIiwic2Vzc2lvbklkIjo2NywiaWF0IjoxNzc2MzA4NzIxLCJleHAiOjE4MzkzODA3MjF9.lG628rkPjuveIUSbDKln7a9Foe3rJv9NN8yVTb0099E"

# Node UUIDs
id_trigger  = str(uuid.uuid4())
id_calcular = str(uuid.uuid4())
id_buscar   = str(uuid.uuid4())
id_extrair  = str(uuid.uuid4())
id_split    = str(uuid.uuid4())
id_enviar   = str(uuid.uuid4())
id_marcar   = str(uuid.uuid4())

# ── Código dos nós ──────────────────────────────────────────────────────────

CODE_CALCULAR = (
    "const now = new Date();\n"
    "\n"
    "// Janela 24h: agendamentos entre 23h50 e 24h10 a partir de agora\n"
    "const w24s = new Date(now.getTime() + (23 * 60 + 50) * 60000);\n"
    "const w24e = new Date(now.getTime() + (24 * 60 + 10) * 60000);\n"
    "\n"
    "// Janela 1h: agendamentos entre 50 e 70 min a partir de agora\n"
    "const w1s = new Date(now.getTime() + 50 * 60000);\n"
    "const w1e = new Date(now.getTime() + 70 * 60000);\n"
    "\n"
    "return [\n"
    "  {\n"
    "    json: {\n"
    "      tipo: '24h',\n"
    "      field: 'reminder_24h_sent_at',\n"
    "      null_filter: 'reminder_24h_sent_at=is.null',\n"
    "      window_start: w24s.toISOString(),\n"
    "      window_end:   w24e.toISOString()\n"
    "    }\n"
    "  },\n"
    "  {\n"
    "    json: {\n"
    "      tipo: '1h',\n"
    "      field: 'reminder_1h_sent_at',\n"
    "      null_filter: 'reminder_1h_sent_at=is.null',\n"
    "      window_start: w1s.toISOString(),\n"
    "      window_end:   w1e.toISOString()\n"
    "    }\n"
    "  }\n"
    "];"
)

CODE_EXTRAIR = (
    "const responses = $input.all();\n"
    "const configs   = $('" + "Calcular Janelas" + "').all();\n"
    "\n"
    "const output = [];\n"
    "for (let i = 0; i < responses.length; i++) {\n"
    "  const appointments = responses[i].json;\n"
    "  const config       = configs[i] ? configs[i].json : {};\n"
    "\n"
    "  if (!Array.isArray(appointments)) continue;\n"
    "\n"
    "  for (const apt of appointments) {\n"
    "    const tipo   = config.tipo  || '?';\n"
    "    const field  = config.field || '';\n"
    "    const cName  = (apt.clients && apt.clients.name)  ? apt.clients.name  : 'Cliente';\n"
    "    const cPhone = (apt.clients && apt.clients.phone) ? apt.clients.phone : '';\n"
    "\n"
    "    // Converter UTC -> Brasilia (UTC-3)\n"
    "    const dt      = new Date(apt.scheduled_at);\n"
    "    const dtLocal = new Date(dt.getTime() - 3 * 60 * 60000);\n"
    "    const hh  = String(dtLocal.getUTCHours()).padStart(2, '0');\n"
    "    const mm  = String(dtLocal.getUTCMinutes()).padStart(2, '0');\n"
    "    const dd  = String(dtLocal.getUTCDate()).padStart(2, '0');\n"
    "    const mo  = String(dtLocal.getUTCMonth() + 1).padStart(2, '0');\n"
    "    const timeStr = hh + ':' + mm;\n"
    "    const dateStr = dd + '/' + mo;\n"
    "\n"
    "    let mensagem;\n"
    "    if (tipo === '24h') {\n"
    "      mensagem = 'Ola, ' + cName + '! Lembrando do seu agendamento *amanha, ' + dateStr + ' as ' + timeStr + '*. Caso precise remarcar ou cancelar, e so nos avisar!';\n"
    "    } else {\n"
    "      mensagem = 'Ola, ' + cName + '! Seu agendamento e *hoje as ' + timeStr + '* — daqui a pouco! Te esperamos.';\n"
    "    }\n"
    "\n"
    "    output.push({\n"
    "      json: {\n"
    "        appointment_id:  apt.id,\n"
    "        client_name:     cName,\n"
    "        client_phone:    cPhone,\n"
    "        scheduled_at:    apt.scheduled_at,\n"
    "        tipo:            tipo,\n"
    "        field_to_update: field,\n"
    "        mensagem:        mensagem\n"
    "      }\n"
    "    });\n"
    "  }\n"
    "}\n"
    "\n"
    "return output;"
)

# ── URL de busca (expressão n8n) ────────────────────────────────────────────
URL_BUSCAR = (
    "={{ '"
    + SB_URL
    + "/rest/v1/appointments?select=*,clients(name,phone)&tenant_id=eq."
    + TENANT_ID
    + "&scheduled_at=gte.' + $json.window_start + '&scheduled_at=lte.' + $json.window_end + '&' + $json.null_filter + '&status=in.(scheduled,confirmed)&order=scheduled_at' }}"
)

URL_PATCH = (
    "={{ '"
    + SB_URL
    + "/rest/v1/appointments?id=eq.' + $json.appointment_id + '&tenant_id=eq."
    + TENANT_ID
    + "' }}"
)

BODY_ENVIAR = (
    '={{ JSON.stringify({ number: $json.client_phone, text: $json.mensagem }) }}'
)

BODY_PATCH = (
    "={{ JSON.stringify({ [$json.field_to_update]: new Date().toISOString() }) }}"
)

# ── Nós ─────────────────────────────────────────────────────────────────────

nodes = [
    # 1. Schedule Trigger — a cada 10 minutos
    {
        "parameters": {
            "rule": {
                "interval": [{"field": "minutes", "minutesInterval": 10}]
            }
        },
        "id": id_trigger,
        "name": "Schedule Trigger",
        "type": "n8n-nodes-base.scheduleTrigger",
        "typeVersion": 1.2,
        "position": [0, 0]
    },

    # 2. Code: Calcular Janelas
    {
        "parameters": {
            "jsCode": CODE_CALCULAR
        },
        "id": id_calcular,
        "name": "Calcular Janelas",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [240, 0]
    },

    # 3. HTTP GET: Buscar Lembretes
    {
        "parameters": {
            "method": "GET",
            "url": URL_BUSCAR,
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {"name": "apikey",        "value": SB_KEY},
                    {"name": "Authorization", "value": "Bearer " + SB_KEY}
                ]
            },
            "options": {}
        },
        "id": id_buscar,
        "name": "Buscar Lembretes",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [480, 0]
    },

    # 4. Code: Extrair e Formatar itens
    {
        "parameters": {
            "jsCode": CODE_EXTRAIR
        },
        "id": id_extrair,
        "name": "Extrair Itens",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [720, 0]
    },

    # 5. Split in Batches — 1 por vez
    {
        "parameters": {
            "batchSize": 1,
            "options": {}
        },
        "id": id_split,
        "name": "Split in Batches",
        "type": "n8n-nodes-base.splitInBatches",
        "typeVersion": 3,
        "position": [960, 0]
    },

    # 6. HTTP POST: Enviar WhatsApp via MK PRO
    {
        "parameters": {
            "method": "POST",
            "url": MKPRO_URL,
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {"name": "Authorization", "value": MKPRO_TKN},
                    {"name": "Content-Type",  "value": "application/json"}
                ]
            },
            "sendBody": True,
            "specifyBody": "string",
            "body": BODY_ENVIAR,
            "options": {}
        },
        "id": id_enviar,
        "name": "Enviar WhatsApp",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [1200, 0]
    },

    # 7. HTTP PATCH: Marcar lembrete como enviado
    {
        "parameters": {
            "method": "PATCH",
            "url": URL_PATCH,
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {"name": "apikey",        "value": SB_KEY},
                    {"name": "Authorization", "value": "Bearer " + SB_KEY},
                    {"name": "Content-Type",  "value": "application/json"},
                    {"name": "Prefer",        "value": "return=minimal"}
                ]
            },
            "sendBody": True,
            "specifyBody": "string",
            "body": BODY_PATCH,
            "options": {}
        },
        "id": id_marcar,
        "name": "Marcar Enviado",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [1440, 0]
    },
]

# ── Conexões ─────────────────────────────────────────────────────────────────
connections = {
    "Schedule Trigger": {
        "main": [[{"node": "Calcular Janelas",  "type": "main", "index": 0}]]
    },
    "Calcular Janelas": {
        "main": [[{"node": "Buscar Lembretes",  "type": "main", "index": 0}]]
    },
    "Buscar Lembretes": {
        "main": [[{"node": "Extrair Itens",     "type": "main", "index": 0}]]
    },
    "Extrair Itens": {
        "main": [[{"node": "Split in Batches",  "type": "main", "index": 0}]]
    },
    # Split in Batches: output 0 = tem itens, output 1 = terminou
    "Split in Batches": {
        "main": [
            [{"node": "Enviar WhatsApp", "type": "main", "index": 0}],
            []  # output 1: todos processados — fluxo encerra
        ]
    },
    "Enviar WhatsApp": {
        "main": [[{"node": "Marcar Enviado",    "type": "main", "index": 0}]]
    },
    # Loop: Marcar Enviado → Split in Batches
    "Marcar Enviado": {
        "main": [[{"node": "Split in Batches",  "type": "main", "index": 0}]]
    },
}

workflow = {
    "name": "03.0 - LEMBRETES AUTOMATICOS - BARBEARIA SILVA",
    "nodes": nodes,
    "connections": connections,
    "active": False,
    "settings": {
        "executionOrder": "v1"
    },
    "id": str(uuid.uuid4()),
    "meta": {
        "instanceId": "mike-agentes"
    }
}

output_path = "03.0 - LEMBRETES AUTOMATICOS - BARBEARIA SILVA.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(workflow, f, ensure_ascii=False, indent=2)

print(f"Workflow gerado: {output_path}")
print(f"Nodes: {[n['name'] for n in nodes]}")
