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
app = Flask(__name__, 
            template_folder="../templates", 
            static_folder="../static")

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
GOOGLE_SHEET_KEY = os.getenv("GOOGLE_SHEET_KEY")

def connect_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_json_string = os.getenv("GOOGLE_CREDENTIALS_JSON")
    
    if creds_json_string:
        # Online su Vercel
        creds_info = json.loads(creds_json_string)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    else:
        # Locale
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
            # Recupera e pulisce i dati dagli spazi bianchi
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
            
            # Recupera e pulisce i dati dagli spazi bianchi (IMPORTANTE PER I LINK)
            raw_data = current_ws.get_all_values()
            data = [[cell.strip() for cell in row] for row in raw_data]
        
        return render_template('base.html', menu=menu, content=data, current_page=page_name)
    except Exception as e:
        return f"Errore di connessione: {e}", 500

@app.route('/submit', methods=['POST'])
def submit():
    try:
        piattaforma = request.form.get('piattaforma')
        ruoli = request.form.get('ruoli')
        club_precedenti = request.form.get('club_precedenti')
        competizioni = request.form.get('competizioni')
        giorni = ", ".join(request.form.getlist('giorni'))
        telefono = request.form.get('telefono')
        note = request.form.get('note')

        discord_data = {
            "username": "INSIDIOUS RECRUITER",
            "embeds": [{
                "title": "🚨 NUOVA CANDIDATURA RICEVUTA",
                "color": 13938487, 
                "fields": [
                    {"name": "🎮 Piattaforma", "value": piattaforma, "inline": True},
                    {"name": "👦 Età", "value": piattaforma, "inline": True},
                    {"name": "🏃 Ruoli", "value": ruoli, "inline": True},
                    {"name": "📞 Telefono", "value": telefono, "inline": True},
                    {"name": "🏟️ Club precedenti", "value": club_precedenti or "Nessuno"},
                    {"name": "🏆 Esperienze", "value": competizioni or "Nessuna"},
                    {"name": "📅 Disponibilità", "value": giorni or "Non specificata"},
                    {"name": "📝 Gametarg", "value": note or "Nessuna"}
                ],
                "footer": {"text": "Inviato dal sito ufficiale INSIDIOUS FC"}
            }]
        }
        
        if DISCORD_WEBHOOK_URL:
            requests.post(DISCORD_WEBHOOK_URL, json=discord_data)

        sheet = connect_sheet()
        try:
            ws_iscrizioni = sheet.worksheet("ISCRIZIONI")
        except:
            ws_iscrizioni = sheet.add_worksheet(title="ISCRIZIONI", rows="1000", cols="7")
            ws_iscrizioni.append_row(["TELEFONO", "PIATTAFORMA", "RUOLI", "CLUB PRECEDENTI", "COMPETIZIONI", "DISPONIBILITA", "NOTE/DISCORD"])

        ws_iscrizioni.append_row([telefono, piattaforma, ruoli, club_precedenti, competizioni, giorni, note])
        return "<h1>Candidatura inviata!</h1><p>Ti contatteremo presto.</p><a href='/'>Torna alla Home</a>"
    except Exception as e:
        return f"Errore invio: {e}", 500

