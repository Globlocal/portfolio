import os
import requests
import pandas as pd
import json
import plotly.graph_objs as go

#in questo codice vi è una sommaria gestione dell'armonizzazione tra prodotti di specie diversa (forex, azioni, commodity, crypto, index); 
#in relazione alla chiusura e non, dei mercati.
#Nessun problema noto tra prodotti con stessi orari.

#riferimento temporale
#orari= ['15min','30min','1h','4h','1day'] variante con ciclo for
orario= '1day'

periodo=180

# Indica le coppie di trading desiderate come portafoglio
portfolio = [
    #forex
    {'symbol': 'eur/usd', 'quantity': 1, 'type': 'long'},
    {'symbol': '', 'quantity': 1, 'type': 'long'},
    #commodity
    {'symbol': '', 'quantity': 1, 'type': 'long'},
    #crypto
    {'symbol': 'BTC/USD', 'quantity': 1, 'type': 'long'},
    #index
    {'symbol': '', 'quantity': 1, 'type': 'short'},
    #azioni
    #{'symbol': '/usd', 'quantity': 1, 'type': 'long'},
    #{'symbol': '/usd', 'quantity': 1, 'type': 'long'},
]

#consultazione mercati internazionali
def buy_sell_folio(periodo, portfolio, orario):
    """
      Calcola i valori del portafoglio e le date basandosi sui dati storici dei prezzi.
      
      Args:
      periodo (int): Il numero di punti dati storici da recuperare.
      portfolio (list): Una lista di dizionari che rappresentano il portafoglio.
      Ogni dizionario dovrebbe contenere le seguenti chiavi:
      - 'symbol': Il simbolo dello strumento.
      - 'quantity': La quantità dello strumento.
      - 'type': Il tipo dello strumento ('long' o 'short').
      orario (str): L'intervallo di tempo per il recupero dei dati storici.
      
      Returns:
      tuple: Una tupla contenente due liste:
      - portfolio_values: Una lista di valori del portafoglio nel tempo.
      - portfolio_dates: Una lista di date corrispondenti.
    """
    #export sec_key=la_tua_chive o altro metodo per caricare la variabile d'ambiente
    # carica variabile per apikey
    sec_key = os.getenv('sec_key')

    #url twelvedata
    API_BASE_URL = 'https://api.twelvedata.com/time_series'
    # Dati storici dei prezzi per il portafoglio
    portfolio_data = {}
    portfolio_values = []  # Valori del portafoglio nel tempo
    portfolio_dates = []  # Date corrispondenti ai timestamp

    for instrument in portfolio:
        symbol = instrument['symbol']
        instrument_url = f'{API_BASE_URL}?apikey={sec_key}&interval={orario}&symbol={symbol}&outputsize={periodo}&timezone=Europe/Rome'

        # Chiama l'API per ottenere i dati
        response = requests.get(instrument_url)
        data = json.loads(response.text)
        portfolio_data[symbol] = data  # Salva i dati storici completi nel dizionario portfolio_data

    # Trova tutti i timestamp disponibili nel dizionario portfolio_data
    all_timestamps = set()
    for data in portfolio_data.values():
        timestamps = [value['datetime'] for value in data['values']]
        all_timestamps.update(timestamps)

    # Dizionario per tenere traccia dell'ultimo prezzo conosciuto per ciascun simbolo
    last_known_prices = {instrument['symbol']: None for instrument in portfolio}

    # Itera su tutti i timestamp
    for timestamp in all_timestamps:
        value = 0
        is_forex_open = True  # Indica se il mercato forex è aperto per questa data

        for instrument in portfolio:
            symbol = instrument['symbol']
            quantity = instrument['quantity']
            type_ = instrument['type']
            data = portfolio_data[symbol]['values']

            # Inizializza la variabile data_datetime
            data_datetime = None

            # Trova il prezzo di chiusura corrispondente al timestamp
            last_price = None

            for value_data in data:
                if value_data['datetime'] == timestamp:
                    last_price = float(value_data['close'])
                    data_datetime = value_data['datetime']
                    break

            # Controlla se il prezzo manca o è negativo
            if last_price is None or last_price <= 0:
                # Utilizza l'ultimo prezzo noto per questo simbolo
                last_price = last_known_prices[symbol]
            else:
                # Aggiorna l'ultimo prezzo noto per questo simbolo solo se il prezzo è valido
                last_known_prices[symbol] = last_price

            # Se il prezzo manca per il simbolo o è negativo, salta il calcolo per questa data
            if last_price is None or last_price <= 0:
                is_forex_open = False
                break

            # Converti la data corretta in un oggetto datetime
            date_object = pd.to_datetime(data_datetime)
            #gestisci posizioni lunghe e corte
            if type_ == 'long':
                instrument_value = last_price * quantity
            elif type_ == 'short':
                instrument_value = -last_price * quantity

            value += instrument_value
        if is_forex_open:
            #aggiungi valori portfolio
            portfolio_values.append(value)
            #portfolio_dates.append(pd.to_datetime(timestamp).strftime('%Y-%m-%d'))  # Conversione del timestamp in data
            portfolio_dates.append(date_object)

    return portfolio_values, portfolio_dates

def grafico_semplice_portfolio (portfolio_values, portfolio_dates):
    #crezion dataframe per manipolare i dati
    data_df = pd.DataFrame({'date': portfolio_dates, 'close': portfolio_values})
    # Ordina il DataFrame in base alle date in modo ascendente
    data_df = data_df.sort_values('date')
    # Plot del valore del portafoglio nel tempo
    fig = go.Figure(data=go.Scatter(x=data_df['date'], y=data_df['close']))
    fig.update_layout(
        title="Andamento del portafoglio nel tempo",
        xaxis_title="Tempo",
        yaxis_title="Valore del portafoglio"
    )
    fig.update_traces(
        hovertemplate='<b>Data:</b> %{x}<br><b>Valore del portafoglio:</b> $%{y:.2f}'
    )

    fig.show()


#run
portfolio_values, portfolio_dates=buy_sell_folio(periodo, portfolio, orario)
grafico_semplice_portfolio(portfolio_values, portfolio_dates)
