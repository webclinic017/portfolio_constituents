import pandas as pd
import yfinance
from datetime import date
from datetime import timedelta
import yaml
import dash_bootstrap_components as dbc
from sqlalchemy import create_engine
from sqlalchemy import text
import re
from typing import Tuple, Union, Optional, Dict, List
from dash import html
import dash_bootstrap_components as dbc
import dash_daq as daq

pd.options.display.float_format = '{:6.2f}'.format

def active_tickers(dynamic_delete_inputs: Dict[str, int]) -> List[str]:
    distinct_tickers = []
    pattern = re.compile(r'[A-Z]+')
    for i in dynamic_delete_inputs.keys():
        if dynamic_delete_inputs[i] == 0:
            ticker = pattern.findall(str(i))
            distinct_tickers.append(ticker[0])
    if len(distinct_tickers) == 0:
        return(['VGT'])
    else:
        return (distinct_tickers)
    
def drawNumericInput(min, value, max, ticker):
    return dbc.Row(children = [
        dbc.Col(html.H4(ticker, style={'textAlign': 'center'}), width=4),
        dbc.Col(daq.NumericInput(min=min, 
                                max=max, 
                                value=value, 
                                size='fit',
                                id = {'type':'portfolio-modification','index':ticker})
                , align = 'center', width=6),
        dbc.Col(dbc.Button(className="bi bi-x-square-fill", 
                            color="white", 
                            style={'border-width': 0, 'font-size':30},
                            n_clicks=0,  
                            id = {'type':'portfolio-deletion','index':ticker})
                , align='right', width=1)
    ], style={"width": "100%"}, align='center')

def draw_portfolio_inputs(portfolio: Dict[str, int]) -> List[dbc.Row]:
    buttons = []
    for ticker in portfolio.keys():
        buttons.append(drawNumericInput(0,portfolio[ticker],1000,ticker))
    return(buttons)

def increment_portfolio(props_dictionary: Dict[str, str]) -> Dict[str, int]:
    portfolio_dictionary = {}
    for i in props_dictionary:
        ticker = i['id']['index']
        value = i['value']
        portfolio_dictionary[ticker] = value
    return portfolio_dictionary

def add_ticker(portfolio_buffer: Optional[Dict[str, int]] = None, new_ticker: Optional[str] = None) -> Tuple[Dict[str, int], bool, bool]:
    if portfolio_buffer is None:
        portfolio_buffer = {'VGT':15,'EDV':15,'GME':15}
    portfolio = portfolio_buffer.copy()
    if new_ticker is not None and new_ticker.upper() not in portfolio.keys():
        new_ticker = new_ticker.upper()
        validation = validate_stock(new_ticker)
        if validation:
            portfolio[new_ticker] = 5
        return(portfolio, validation, not validation)
    else:
        return(portfolio, False, False)

def get_range(tickers: List[str], selection: str, last_day: pd.Timestamp) -> Tuple[List[date], int]:
    dict = {'test':3,'all':0,'one year':365,'three months':92,'one month':31,'ytd':(last_day-date(last_day.year, 1, 1)).days}
    selection = dict[selection]
    local_engine = create_engine('sqlite+pysqlite:///assets/financial_website.db')
    with local_engine.connect() as con:
        tickers = "'" + "', '".join(tickers) + "'" 
        earliest_date = con.execute(text(f'SELECT date FROM fact_ticker_data WHERE name IN ({tickers}) ORDER BY date ASC LIMIT 1;')).fetchone()
    start = last_day - timedelta(days = selection)
    return([max(start, earliest_date), last_day], selection)    

def validate_stock(ticker: str) -> bool:
    info = yfinance.Ticker(ticker).history(
        period='7d',
        interval='1d')
    return len(info) > 0

def collect_yaml(file_name: str) -> Dict[str, int]:
    with open(file_name, 'r') as file:
        config = yaml.safe_load(file)
        portfolio = config["portfolio"]
    return(portfolio)