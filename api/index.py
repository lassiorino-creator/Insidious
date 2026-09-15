@app.route('/')
@app.route('/<page_name>')
def index(page_name=None):
    try:
        sheet = connect_sheet()
        worksheets = sheet.worksheets()
        
        # Mappa dei fogli per ricerca rapida (in minuscolo e pulita)
        ws_map = {ws.title.lower().strip(): ws for ws in worksheets}
        
        # Genera il menu escludendo le pagine speciali o gestite separatamente
        menu = [ws.title.strip() for ws in worksheets if ws.title.lower().strip() not in ["iscrizioni", "sponsor"]]
        
        # 1. Caso HOME (Nessun parametro o pagina = 'home')
        if not page_name or page_name.lower().strip() == "home":
            current_ws = ws_map.get("home")
            page_name = "Home"
            
            # Se non esiste un foglio "Home", prende il primo foglio valido presente nel menu
            if not current_ws and menu:
                target_title = menu[0]
                current_ws = ws_map.get(target_title.lower().strip())
                page_name = target_title

            if not current_ws:
                return "Errore: Nessun foglio valido trovato per la Home Page su Google Sheets.", 404

            data = [[cell.strip() for cell in row] for row in current_ws.get_all_values()]

        # 2. Caso UNISCITI (Pagina statica/form)
        elif page_name.lower().strip() == "unisciti":
            data = [] 
            page_name = "Unisciti"

        # 3. Caso SPONSOR
        elif page_name.lower().strip() == "sponsor":
            current_ws = ws_map.get("sponsor")
            if not current_ws:
                return "Errore: Il foglio 'Sponsor' non esiste su Google Sheets.", 404
                
            page_name = "Sponsor"
            data = [[cell.strip() for cell in row] for row in current_ws.get_all_values()]

        # 4. Tutte le altre pagine dinamiche
        else:
            target_key = page_name.replace('-', ' ').lower().strip()
            current_ws = ws_map.get(target_key)
            
            if not current_ws:
                return f"Errore: Il foglio '{page_name}' non esiste.", 404
            
            page_name = current_ws.title.strip()
            data = [[cell.strip() for cell in row] for row in current_ws.get_all_values()]
        
        return render_template(
            'base.html', 
            menu=menu, 
            content=data, 
            current_page=page_name, 
            page_id=page_name.lower().strip()
        )
        
    except Exception as e:
        return f"Errore di connessione: {e}", 500
