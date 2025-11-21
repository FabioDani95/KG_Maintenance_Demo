# Knowledge Graph Maintenance - Sistema Dinamico

Sistema completo per la visualizzazione interattiva di ontologie con **backend dinamico** che legge e parsifica automaticamente file JSON di ontologie.

## 🎯 Caratteristiche

✅ **Backend dinamico** con Flask
✅ **Parsing automatico** dell'ontologia da JSON
✅ **Non hardcoded** - si adatta a qualsiasi struttura ontologia
✅ **API REST** per comunicazione frontend-backend
✅ **Visualizzazione interattiva** con Cytoscape.js
✅ **Filtri e ricerca** sui nodi

## 🏗️ Architettura

```
KG_Maintenance_Demo/
├── backend/
│   ├── app.py                    # Server Flask principale
│   ├── ontology_parser.py        # Parser dinamico per ontologie
│   └── requirements.txt          # Dipendenze Python
├── frontend/
│   └── index.html               # Interfaccia web
└── README.md
```

## 🚀 Installazione e Avvio

### 1. Installare le dipendenze

```bash
cd backend
pip install -r requirements.txt
```

### 2. Avviare il backend

```bash
python app.py
```

Il server sarà disponibile su **http://localhost:8000**

### 3. Aprire l'applicazione

Aprire il browser e navigare su:
```
http://localhost:8000
```

## 📖 Come Usare

### 1. Carica l'Ontologia JSON

- Clicca sul pulsante **"Scegli file"** nell'header
- Seleziona il tuo file JSON di ontologia (usa `defaultOntology.json` o `example_ontology.json` per testare)
- Il sistema caricherà il file sul backend e mostrerà statistiche (numero di nodi e archi)

### 2. Analizza l'Ontologia

- Clicca sul pulsante **"Analizza Ontologia"** che appare dopo il caricamento
- Il sistema parsificherà la struttura e visualizzerà il grafo interattivo

### 3. Esplora il Grafo

- **Click su un nodo**: visualizza i dettagli nel pannello laterale
- **Zoom**: usa i pulsanti + / - o la rotellina del mouse
- **Pan**: trascina il grafo con il mouse
- **Fit**: adatta il grafo alla finestra

### 4. Filtra e Cerca

- **Filtri per categoria**: usa le checkbox nella sidebar
- **Ricerca**: digita nel campo di ricerca per trovare nodi specifici

## 📝 Formato JSON Ontologia

Il sistema accetta qualsiasi struttura JSON di ontologia. Esempio:

```json
{
  "nome_ontologia": {
    "version": "1.0",
    "domain": "Maintenance",
    "description": "Ontologia di manutenzione",
    "classes": {
      "machine_components": {
        "hydraulic_unit": {
          "description": "Unità idraulica"
        },
        "injection_unit": {
          "description": "Unità di iniezione"
        }
      },
      "maintenance_activities": {
        "preventive_maintenance": {},
        "corrective_maintenance": {}
      },
      "relationships": {
        "causal_relationships": [
          {
            "source": "hydraulic_unit",
            "target": "injection_unit",
            "type": "affects"
          }
        ]
      }
    }
  }
}
```

## 🔧 API Endpoints

Il backend espone le seguenti API REST:

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/api/upload` | POST | Carica e parsifica ontologia JSON |
| `/api/graph` | GET | Ottieni nodi ed archi del grafo |
| `/api/categories` | GET | Lista delle categorie disponibili |
| `/api/node/<id>` | GET | Dettagli di un nodo specifico |
| `/api/search?q=...` | GET | Cerca nodi per nome |
| `/api/filter` | POST | Filtra nodi per categoria |
| `/api/stats` | GET | Statistiche sull'ontologia |
| `/api/health` | GET | Health check del server |

## 🎨 Categorie Automatiche

Il parser riconosce automaticamente le seguenti categorie:

- **Machine Components** (blu)
- **Maintenance Activities** (verde)
- **Process Parameters** (arancione)
- **Failures & Anomalies** (rosso)
- **Relationships** (viola)
- **Metrics & KPI** (rosa)
- **Documentation** (indaco)
- **Safety & Compliance** (arancione scuro)
- **Operating Environment** (teal)
- **Spare Parts** (viola chiaro)
- **Integration & Systems** (ciano)
- **Human Factors** (lime)

## 🛠️ Personalizzazione

### Aggiungere nuove categorie

Modifica il file `backend/ontology_parser.py`:

```python
CATEGORY_KEYWORDS = {
    'nuova_categoria': ['keyword1', 'keyword2'],
    # ...
}

CATEGORY_COLORS = {
    'nuova_categoria': '#colore_hex',
    # ...
}
```

### Modificare il layout del grafo

Modifica il file `frontend/index.html` nella funzione `renderGraph()`:

```javascript
cy.layout({
    name: 'cose',  // o 'breadthfirst', 'circle', 'grid', etc.
    // altre opzioni...
}).run();
```

## 📊 Tecnologie Utilizzate

- **Backend**: Python, Flask, Flask-CORS
- **Frontend**: HTML5, JavaScript, Cytoscape.js
- **Parsing**: JSON dinamico con supporto per strutture complesse

## 🐛 Troubleshooting

### Il backend non si avvia
```bash
# Verifica le dipendenze
pip install -r backend/requirements.txt
```

### Errore CORS
Il backend ha già Flask-CORS configurato. Se persiste l'errore, verifica che il backend sia in esecuzione su localhost:8000

### Il grafo non si visualizza
1. Verifica che il file JSON sia valido
2. Controlla la console del browser per errori (F12)
3. Verifica che il backend sia raggiungibile su http://localhost:8000

## 📄 Licenza

MIT License

## 👥 Contributi

Contributi, issues e feature requests sono benvenuti!
