import os
import json
import gspread
import requests
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, render_template, request, redirect, url_for

# Carica variabili locali se presenti
load_dotenv()

# CONFIGURAZIONE PERCORSI PER VERCEL
# Usiamo ../ perché il file è dentro la cartella /api
app = Flask(__name__, 
            template_folder="../templates", 
            static_folder="../static")

# ATTIVAZIONE ESTENSIONE "DO" PER JINJA2
app.jinja_env.add_extension('jinja2.ext.do')

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
GOOGLE_SHEET_KEY = os.getenv("GOOGLE_SHEET_KEY")

def connect_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_json_string = os.getenv("GOOGLE_CREDENTIALS_JSON")
    
    if creds_json_string:
        creds_info = json.loads(creds_json_string)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        
    client = gspread.authorize(creds)
    return client.open_by_key(GOOGLE_SHEET_KEY)

@app.route('/')
@app.route('/<page_name>')
def index(page_name=None):
    try:
        sheet = connect_sheet()
        worksheets = sheet.worksheets()
        menu = [ws.title for ws in worksheets if ws.title != "ISCRIZIONI"]
        
        if not page_name or page_name.lower() == "home":
            current_ws = worksheets[0]
            page_name = current_ws.title
            raw_data = current_ws.get_all_values()
            data = [[cell.strip() for cell in row] for row in raw_data]
        elif page_name.lower() == "unisciti":
            data = [] 
            page_name = "Unisciti"
        else:
            target_name = page_name.replace('-', ' ').lower().strip()
            current_ws = None
            for ws in worksheets:
                if ws.title.lower().strip() == target_name:
                    current_ws = ws
                    page_name = ws.title  
                    break
            
            if not current_ws:
                return f"Errore: Il foglio '{page_name}' non esiste.", 404
            
            raw_data = current_ws.get_all_values()
            data = [[cell.strip() for cell in row] for row in raw_data]
        
        return render_template('base.html', menu=menu, content=data, current_page=page_name)
    except Exception as e:
        return f"Errore di connessione: {e}", 500

@app.route('/submit', methods=['POST'])
def submit():
    try:
        # 1. Recupero dei campi testuali standard dal modulo HTML
        piattaforma = request.form.get('piattaforma')
        eta = request.form.get('età')
        ruoli = request.form.get('ruoli')
        telefono = request.form.get('telefono')
        club_precedenti = request.form.get('club_precedenti')
        esperienze = request.form.get('esperienze')
        gametarg = request.form.get('gametarg')
        note = request.form.get('note')

        # 2. RISOLUZIONE BUG DISPONIBILITÀ MULTIPLA
        # Recupera l'array di tutti i checkbox spuntati e unisce i giorni con una virgola
        lista_giorni = request.form.getlist('disponibilità')
        if lista_giorni:
            disponibilita = ", ".join(lista_giorni)
        else:
            disponibilita = "Non specificata"

        # 3. Costruzione della notifica Discord EMBED completa di ogni informazione richiesto
        discord_data = {
            "username": "INSIDIOUS RECRUITER",
            "embeds": [{
                "title": "🚨 NUOVA CANDIDATURA RICEVUTA",
                "color": 13938487, 
                "fields": [
                    {"name": "🎮 Piattaforma", "value": piattaforma or "N/A", "inline": True},
                    {"name": "📝 Gamertag / PSN ID", "value": gametarg or "Nessuna", "inline": True},
                    {"name": "🎂 Età", "value": eta or "N/A", "inline": True},
                    {"name": "🏃 Ruoli principali", "value": ruoli or "N/A", "inline": False},
                    {"name": "📞 Telefono / WhatsApp", "value": telefono or "N/A", "inline": True},
                    {"name": "🏟️ Club precedenti", "value": club_precedenti or "Nessuno", "inline": False},
                    {"name": "🏆 Esperienze / Competizioni", "value": esperienze or "Nessuna", "inline": False},
                    {"name": "📅 Disponibilità (Lun - Gio)", "value": disponibilita, "inline": False},
                    {"name": "💬 Note aggiuntive / Discord ID", "value": note or "Nessuna nota", "inline": False}
                ],
                "footer": {"text": "Inviato dal sito ufficiale INSIDIOUS FC"}
            }]
        }
        
        if DISCORD_WEBHOOK_URL:
            requests.post(DISCORD_WEBHOOK_URL, json=discord_data)

        # 4. Connessione e scrittura sul foglio di calcolo Google Sheets
        sheet = connect_sheet()
        try:
            ws_iscrizioni = sheet.worksheet("ISCRIZIONI")
        except:
            # Se il foglio non esiste, lo crea includendo la nona colonna per le "NOTE"
            ws_iscrizioni = sheet.add_worksheet(title="ISCRIZIONI", rows="1000", cols="9")
            ws_iscrizioni.append_row(["PIATTAFORMA", "ETÀ", "RUOLI", "TELEFONO", "CLUB PRECEDENTI", "ESPERIENZE", "DISPONIBILITÀ", "GAMETARG", "NOTE"])

        # Salva la riga completa ordinata nel foglio excel
        ws_iscrizioni.append_row([piattaforma, eta, ruoli, telefono, club_precedenti, esperienze, disponibilita, gametarg, note])
        
        return "<h1>Candidatura inviata!</h1><p>Ti contatteremo presto.</p><a href='/'>Torna alla Home</a>"
    except Exception as e:
        return f"Errore invio: {e}", 500

# Necessario per l'entrypoint di Vercel quando il file è in /api
application = app
