@app.route('/')
@app.route('/<page_name>')
def index(page_name=None):
    try:
        sheet = connect_sheet()
        worksheets = sheet.worksheets()
        
        # Genera il menu escludendo le pagine gestite in modo fisso o speciale
        menu = [ws.title.strip() for ws in worksheets if ws.title.lower().strip() not in ["iscrizioni", "sponsor"]]
        
        # Se non viene specificata una pagina o è 'home', cerca il foglio 'Home' o usa il primo foglio visibile nel menu
        if not page_name or page_name.lower().strip() == "home":
            current_ws = None
            # Cerca un foglio chiamato "Home"
            for ws in worksheets:
                if ws.title.lower().strip() == "home":
                    current_ws = ws
                    page_name = "Home"
                    break
            
            # Se non esiste un foglio "Home", prendi il primo foglio valido presente nel menu
            if not current_ws and menu:
                target_title = menu[0]
                for ws in worksheets:
                    if ws.title.strip() == target_title:
                        current_ws = ws
                        page_name = ws.title.strip()
                        break
            
            if not current_ws:
                return "Errore: Nessun foglio valido trovato per la Home Page su Google Sheets.", 404

            raw_data = current_ws.get_all_values()
            data = [[cell.strip() for cell in row] for row in raw_data]

        elif page_name.lower().strip() == "unisciti":
            data = [] 
            page_name = "Unisciti"

        elif page_name.lower().strip() == "sponsor":
            current_ws = None
            for ws in worksheets:
                if ws.title.lower().strip() == "sponsor":
                    current_ws = ws
                    page_name = "Sponsor"
                    break
            
            if not current_ws:
                return "Errore: Il foglio 'Sponsor' non esiste su Google Sheets.", 404
                
            raw_data = current_ws.get_all_values()
            data = [[cell.strip() for cell in row] for row in raw_data]

        else:
            target_name = page_name.replace('-', ' ').lower().strip()
            current_ws = None
            
            for ws in worksheets:
                if ws.title.lower().strip() == target_name:
                    current_ws = ws
                    page_name = ws.title.strip()
                    break
            
            if not current_ws:
                return f"Errore: Il foglio '{page_name}' non esiste.", 404
            
            raw_data = current_ws.get_all_values()
            data = [[cell.strip() for cell in row] for row in raw_data]
        
        return render_template('base.html', menu=menu, content=data, current_page=page_name, page_id=page_name.lower().strip())
        
    except Exception as e:
        return f"Errore di connessione: {e}", 500
