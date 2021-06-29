
#!/usr/bin/env python3
import time, json, sys
import psycopg2
from configparser import ConfigParser
import pandas as pd
import numpy as np

static_path = "/home/ubuntu/binance-bot/static"
local_path = r"C:\Users\mskauen\Documents\Projects\private\github\binance-bot\static"
sys.path.append(static_path)
sys.path.append(local_path)
import config, postgres_commands

import ta
import slack
import schedule
import ccxt
import backtrader as bt

pd.set_option('display.max_rows',None)

import warnings
warnings.filterwarnings('ignore')
from datetime import datetime


class postgres():
    def postgres_config(self, filename=config.postgres_filename, section=config.postgres_section):
        # create a parser
        parser = ConfigParser()
        # read config file
        parser.read(filename)

        # get section, default to postgresql
        db = {}
        if parser.has_section(section):
            params = parser.items(section)
            for param in params:
                db[param[0]] = param[1]
        else:
            raise Exception('Section {0} not found in the {1} file'.format(section, filename))

        return db

    def open_connect(self):
        """ Connect to the PostgreSQL database server """
        self.conn = None
        try:
            # read connection parameters
            self.params = self.postgres_config()

            # connect to the PostgreSQL server
            print('Connecting to the PostgreSQL database...')
            self.conn = psycopg2.connect(**self.params)
               
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

    def close_connect(self):
        if self.conn is not None:
            self.conn.close()
            print('Database connection closed.')
        else:
            print('Database connection is not Open')

    def insert_prices(self, sql_string, op, cl, hi, lo, timestamp):
        price_id = None
        try:
            cur = self.conn.cursor()
            cur.execute(sql_string, (timestamp,op,cl,hi,lo))
            #price_id = cur.fetchone()[0]
            self.conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        return timestamp

    def insert_super_trend(self,df):
        #clean = df.drop('index', 1)
        
        clean_list = list(zip(*map(clean.get, clean)))
        for row in clean_list:
            print(row)
            print(postgres_commands.ccxt_sql_string)
            input()
            try:
                cur = self.conn.cursor()
                #cur.execute(ccxt_sql_string, (timestamp,op,cl,hi,lo))
                cur.execute(postgres_commands.ccxt_sql_string, row)
                self.conn.commit()
                cur.close() 
            except (Exception, psycopg2.DatabaseError) as error:
                print(error)
            return timestamp

    def insert_trade(self,order_type,quantity,timestamp,name,close):
        entry = (order_type,quantity,timestamp,close)
        command = postgres_commands.trade_sql_string.replace('TABLE_NAME', name)
        #print(command)
        #print(entry)
        #input()
        #try:
        cur = self.conn.cursor()
        #cur.execute(ccxt_sql_string, (timestamp,op,cl,hi,lo))
        #hits =  pd.read_sql('SELECT * FROM ethusd_1m',self.conn)
        #print(hits)
        #input()
        cur.execute(command, entry)
        self.conn.commit()
        cur.close() 
        #except (Exception, psycopg2.DatabaseError) as error:
        #    print(error)
    def create_bot_table(self,name):
        command = postgres_commands.postgres_bot_table.replace('TABLE_NAME', name)
        try:
            cur = self.conn.cursor()
            cur.execute(command)
            cur.close()
            self.conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print("table create error")
            print(error)
    def create_tables(self, ccxt=False):
        commands = postgres_commands.postgres_table_commands
        if ccxt == True:
            commands = postgres_commands.ccxt_postgres_table_commands
        try:
            cur = self.conn.cursor()
            for command in commands:
                #try:
                cur.execute(command)
                #except:
                #   print("failed")
            cur.close()
            self.conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print("here")
            print(error)

    def delete_prices(self, ccxt=False):
        commands = postgres_commands.postgres_delete_command
        if ccxt == True:
            commands = postgres_commands.ccxt_postgres_delete_command        
        try:
            cur = self.conn.cursor()
            cur.execute(commands)
            cur.close()
            self.conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

    def cache_prices(self):
        df = pd.read_sql(postgres_commands.postgres_cache_command, self.conn)
        df.head()
        return df
        # https://stackoverflow.com/questions/57949871/how-to-set-get-pandas-dataframes-into-redis-using-pyarrow/57986261#57986261

    def cache_trades(self,name):
        command = postgres_commands.postgres_cache_trades.replace('TABLE_NAME',name)
        df = pd.read_sql(command, self.conn)
        df.head()
        return df

class slack_class():
    def connect(self):
        self.slackclient = slack.WebClient(token=config.SLACK_TOKEN)
    
    def write_trade(self,order_type):
        text = f"""SuperTrend reporting! 
    Suggested action: {order_type} 
    Backtest this strategy: """+config.APP_URL
        self.slackclient.chat_postMessage(channel='#CHANNELNAME', text=text)

class ccxt_class():
    def primary_connect(self):
        self.exchange = ccxt.binanceus()
        #exchange = ccxt.binanceus({
        #    "apiKey": config.BINANCE_API_KEY,
        #    "secret": config.BINANCE_SECRET_KEY
        #})
    def get_all_valutas(self):
        return self.exchange.load_markets()

    def get_data(self,valuta='BTC/USDT',timeframe='1m',max_rows=250):
        bars = self.exchange.fetch_ohlcv(valuta, timeframe=timeframe, limit=max_rows)
        #bars = self.exchange.fetch_ohlcv()
        df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df

    def get_historical_data(self,valuta='BTC/USDT',timeframe='1m',max_rows=250,since='2021-01-01 00:00:00'):
        since= self.exchange.parse8601(since)
        bars = self.exchange.fetch_ohlcv(valuta, timeframe=timeframe, since=since, limit=max_rows)
        #bars = self.exchange.fetch_ohlcv()
        df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df

    def sell_order(self,valuta='ETH/USD',quantity=0.05):
        order = self.exchange.create_market_sell_order(valuta, quantity)
        return order
    
    def buy_order(self,valuta='ETH/USD',quantity=0.05):
        order = self.exchange.create_market_buy_order(valuta, quantity)
        return order

class supertrend():
    def __init__(self, df):         
        self.df = df

    # basic upper band = ((high + low) / 2) + (multiplier * atr)
    # basic lower band = ((high + low) / 2) - (multiplier * atr)
    def tr(self):
        self.df['previous_close'] = self.df['close'].shift(1)
        self.df['highminuslow'] = self.df['high'] - self.df['low']
        self.df['highminuspc'] = abs(self.df['high'] - self.df['previous_close'])
        self.df['lowminuspc'] = abs(self.df['low'] - self.df['previous_close'])
        self.df['tr'] = self.df[['highminuslow','highminuspc','lowminuspc']].max(axis=1)

    def atr(self, period=14):
        self.tr()
        print("avg true range")
        
        self.df['atr'] = self.df['tr'].rolling(period).mean()


    def compute(self, period=14, multiplier=3):

        self.atr(period=period)
        self.df['upperband'] = ((self.df['high'] + self.df['low']) / 2) + (multiplier * self.df['atr'])
        self.df['lowerband'] = ((self.df['high'] + self.df['low']) / 2) - (multiplier * self.df['atr'])

        self.df['in_uptrend'] = True
        for current in range(1, len(self.df.index)):
            previous = current - 1
            
            if self.df['close'][current] > self.df['upperband'][previous]:
                self.df['in_uptrend'][current] = True
            elif self.df['close'][current] < self.df['lowerband'][previous]:
                self.df['in_uptrend'][current] = False
            else:
                self.df['in_uptrend'][current] = self.df['in_uptrend'][previous]

                if self.df['in_uptrend'][current] and self.df['lowerband'][current] < self.df['lowerband'][previous]:
                    self.df['lowerband'][current] = self.df['lowerband'][previous]
                
                if not self.df['in_uptrend'][current] and self.df['upperband'][current] > self.df['upperband'][previous]:
                    self.df['upperband'][current] = self.df['upperband'][previous]
            
        return self.df

from ta.trend import MACD
from ta.trend import SMAIndicator
from ta.volatility import BollingerBands

class ma_macd_ssl():
    def __init__(self, df):         
        self.df = df

    def get_sma(self,param1=50):
        init_sma = SMAIndicator(self.df['close'], window= int(param1))
        self.df["sma"+"_"+str(param1)] = init_sma.sma_indicator()
    
    def get_ssl(self,param1=14):
        init_high = SMAIndicator(self.df['high'], window= int(param1))
        init_low = SMAIndicator(self.df['low'], window= int(param1))
        self.df["ssl_high"] = init_high.sma_indicator()
        self.df["ssl_low"] = init_low.sma_indicator()
    
    def get_macd(self,macd_slow,macd_fast,macd_signal):
        init_macd = MACD(self.df['close'], window_slow = macd_slow, window_fast = macd_fast, window_sign = macd_signal, fillna = False)
        self.df['macd'] = init_macd.macd()
        self.df['macd_diff'] = init_macd.macd_diff()
        self.df['macd_signal'] = init_macd.macd_signal()
    
    def get_boillinger(self):
        # Initialize Bollinger Bands Indicator
        indicator_bb = BollingerBands(close=self.df["close"], window=20, window_dev=2)

        # Add Bollinger Bands features
        self.df['bb_bbm'] = indicator_bb.bollinger_mavg()
        self.df['bb_bbh'] = indicator_bb.bollinger_hband()
        self.df['bb_bbl'] = indicator_bb.bollinger_lband()

        # Add Bollinger Band high indicator
        self.df['bb_bbhi'] = indicator_bb.bollinger_hband_indicator()

        # Add Bollinger Band low indicator
        self.df['bb_bbli'] = indicator_bb.bollinger_lband_indicator()

        # Add Width Size Bollinger Bands
        self.df['bb_bbw'] = indicator_bb.bollinger_wband()

        # Add Percentage Bollinger Bands
        self.df['bb_bbp'] = indicator_bb.bollinger_pband()

    def in_uptrend(self,long_trend,short_trend,macd_lower):
        self.df['ssl_in_uptrend'] = False
        self.df['ma_long_in_uptrend'] = False
        self.df['ma_short_in_uptrend'] = False
        self.df['macd_in_uptrend'] = False
        self.df['in_uptrend'] = False

        last_macd = False
        last_ssl = False
        last_trend = False
        for current in range(1, len(self.df.index)):
            previous = current - 1
            
            #ma trend
            if self.df['close'][current] > self.df['sma'+'_'+str(long_trend)][current]:
                self.df['ma_long_in_uptrend'][current] = True
            if self.df['close'][current] > self.df['sma'+'_'+str(short_trend)][current]:
                self.df['ma_short_in_uptrend'][current] = True
            
            #macd trend
            if last_macd:
                if self.df['macd'][current] > self.df['macd_signal'][current]:
                    self.df['macd_in_uptrend'][current] = True   
                else:
                    last_macd = False
            else:      
                if self.df['macd'][current] > self.df['macd_signal'][current]:
                    if self.df['macd'][current] < macd_lower:
                        self.df['macd_in_uptrend'][current] = True
                        last_macd = True

            #ssl trend
            if self.df['close'][current] > self.df['ssl_high'][current]:
                self.df['ssl_in_uptrend'][current] = True
                last_ssl = True
            elif self.df['close'][current] < self.df['ssl_low'][current]:
                self.df['ssl_in_uptrend'][current] = False
                last_ssl = False
            else:
                self.df['ssl_in_uptrend'][current] = last_ssl

            #overall 
            if last_trend:
                if self.df['ma_short_in_uptrend'][current]:
                    self.df['in_uptrend'][current] = True
                else:
                    last_trend = False
            else:
                #if self.df['ma_short_in_uptrend'][current] and self.df['ma_long_in_uptrend'][current] and self.df['ssl_in_uptrend'][current] and self.df['macd_in_uptrend'][current]:
                if self.df['ma_short_in_uptrend'][current] and self.df['ma_long_in_uptrend'][current] and self.df['ssl_in_uptrend'][current]:
                    self.df['in_uptrend'][current] = True
                    last_trend = True

    def in_ssl_malong_out_ma_short(self,long_trend,short_trend,macd_lower):
        self.df['ssl_in_uptrend'] = False
        self.df['ma_long_in_uptrend'] = False
        self.df['ma_short_sell'] = False
        self.df['macd_in_uptrend'] = False
        self.df['in_uptrend'] = False

        last_macd = False
        last_ssl = False
        last_trend = False
        for current in range(1, len(self.df.index)):
            previous = current - 1
            
            #ma trend
            if self.df['close'][current] > self.df['sma'+'_'+str(long_trend)][current]:
                self.df['ma_long_in_uptrend'][current] = True
                
            if self.df['close'][current] < self.df['sma'+'_'+str(short_trend)][current]:
                if self.df['close'][previous] > self.df['sma'+'_'+str(short_trend)][previous]:
                    self.df['ma_short_sell'][current] = True
            
            #macd trend
            if last_macd:
                if self.df['macd'][current] > self.df['macd_signal'][current]:
                    self.df['macd_in_uptrend'][current] = True   
                else:
                    last_macd = False
            else:      
                if self.df['macd'][current] > self.df['macd_signal'][current]:
                    if self.df['macd'][current] < macd_lower:
                        self.df['macd_in_uptrend'][current] = True
                        last_macd = True

            #ssl trend
            if self.df['close'][current] > self.df['ssl_high'][current]:
                self.df['ssl_in_uptrend'][current] = True
                last_ssl = True
            elif self.df['close'][current] < self.df['ssl_low'][current]:
                self.df['ssl_in_uptrend'][current] = False
                last_ssl = False
            else:
                self.df['ssl_in_uptrend'][current] = last_ssl

            #overall 
            if last_trend:
                if not self.df['ma_short_sell'][current]:
                    self.df['in_uptrend'][current] = True
                else:
                    last_trend = False
            else:
                #if self.df['ma_short_in_uptrend'][current] and self.df['ma_long_in_uptrend'][current] and self.df['ssl_in_uptrend'][current] and self.df['macd_in_uptrend'][current]:
                if self.df['ma_long_in_uptrend'][current] and self.df['ssl_in_uptrend'][current]:
                    self.df['in_uptrend'][current] = True
                    last_trend = True
     
    def compute_gorm(self,long_sma=200,short_sma=50,macd_lower=-150,ssl=14,macd_fast=26,macd_slow=12,macd_signal=9):
        
        self.get_macd(macd_slow=macd_slow,macd_fast=macd_fast,macd_signal=macd_signal)
        self.get_sma(param1=short_sma)
        self.get_sma(param1=long_sma)
        self.get_ssl(param1=ssl)
        #self.get_boillinger()
        #print(self.df)
        #input()
        self.in_uptrend(long_sma,short_sma,macd_lower)
        #print(self.df)
        #input()
        return self.df

    def compute_new(self,long_sma=200,short_sma=50,macd_lower=-150,ssl=14,macd_fast=26,macd_slow=12,macd_signal=9):
        
        self.get_macd(macd_slow=macd_slow,macd_fast=macd_fast,macd_signal=macd_signal)
        self.get_sma(param1=short_sma)
        self.get_sma(param1=long_sma)
        self.get_ssl(param1=ssl)
        #self.get_boillinger()
        #print(self.df)
        #input()
        self.in_ssl_malong_out_ma_short(long_sma,short_sma,macd_lower)
        #print(self.df)
        #input()
        return self.df

class PD(bt.feeds.PandasData):
    #linesoverride = True
    lines = ('previous_close','highminuslow','highminuspc','lowminuspc','tr','atr','upperband','lowerband','in_uptrend',)
    params = (
        ('datetime', None),
        ('open','open'),
        ('high','high'),
        ('low','low'),
        ('close','close'),
        ('volume','volume'),
        ('previous_close','previous_close'),
        ('highminuslow','highminuslow'),
        ('highminuspc','highminuspc'),
        ('lowminuspc','lowminuspc'),
        ('tr','tr'),
        ('atr','atr'),
        ('upperband','upperband'),
        ('lowerband','lowerband'),
        ('in_uptrend', 'in_uptrend')          
    )


class GormData(bt.feeds.PandasData):
    #linesoverride = True
    lines = ('in_uptrend',)
    #lines = ('macd','macd_diff','macd_signal','sma','ssl_high','ssl_low','bb_bbm','bb_bbh','bb_bbl','bb_bbhi','bb_bbli','bb_bbw','bb_bbp','ma_in_uptrend','macd_in_uptrend','ssl_in_uptrend','in_uptrend',)
    params = (
        ('datetime', None),
        ('open','open'),
        ('high','high'),
        ('low','low'),
        ('close','close'),
        ('volume','volume'),
        ('in_uptrend', 'in_uptrend')          
    )


class BackTestSuperTrend(bt.Strategy):

    def __init__(self):
        self.tr = self.data.tr
        self.atr = self.data.atr
        self.close = self.data.close
        self.in_uptrend = self.data.in_uptrend
        self.in_position = False

    def next(self):
        #print(self.in_position)
        size = int(self.broker.getcash() / self.close[0])
        #print(self.in_uptrend[0])
        if self.in_uptrend[0] == True and self.in_position == False:
            self.buy(size=size)
            self.in_position = True
            #print("Buy!")
        elif self.in_uptrend[0] == False and self.in_position == True:
            self.sell(size=self.position.size)
            self.in_position = False
            #print("Sell!")
        #input()

class BackTestUptrend(bt.Strategy):

    def __init__(self):
        self.close = self.data.close
        self.in_uptrend = self.data.in_uptrend
        self.in_position = False

    def next(self):
        #print(self.in_position)
        size = int(self.broker.getcash() / self.close[0])
        #print(self.in_uptrend[0])
        if self.in_uptrend[0] == True and self.in_position == False:
            self.buy(size=size)
            self.in_position = True
            #print("Buy!")
        elif self.in_uptrend[0] == False and self.in_position == True:
            self.sell(size=self.position.size)
            self.in_position = False
            #print("Sell!")
        #input()
