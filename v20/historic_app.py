
import streamlit as st
import backtrader as bt
import sys, os
import pandas as pd
import datetime

modules_path = "/home/ubuntu/binance-bot/modules"
local_path = r"C:\Users\mskauen\Documents\Projects\private\github\binance-bot\modules"

sys.path.append(modules_path)
sys.path.append(local_path)

from v20 import *


def run_app():

    st.title('Analyze Candlestick data from Finance Brokers')
    print("Connecting to primary broker")


    ccxt_object = ccxt_class()
    ccxt_object.primary_connect()
    valutas = ccxt_object.get_all_valutas()
    timestamp = datetime.now().isoformat()
    market_list = list(valutas.keys())
    # User input
    valuta = st.selectbox("Valuta",market_list,index=1)
    #valuta = st.text_input("Valuta",'BTC/USDT')
    virtual_cash = st.slider("Virtual Cash",min_value=100,max_value=1000000,value=100000)
    commision = float(st.text_input("Commision",'0.001'))
    timeframe_quantity = st.selectbox("Select a timeframe  number",('1','5','6','12','15','30'))
    timeframe_time = st.selectbox("Select a unit",('m','h','d'))
    timeframe = timeframe_quantity+timeframe_time
    datelist = [str(d.strftime('%Y-%m-%d')) for d in pd.date_range(end=datetime.today(), periods=50).tolist()][::-1]
    timelist = ["0"+str(hour)+":00:00" for hour in range(0,9)] + [str(hour)+":00:00" for hour in range(10,24)]
    since_date = st.selectbox('Since Date',datelist)
    since_time = st.selectbox('Since Time',timelist)
    since = since_date+" "+since_time
    #since = st.text_input("Since",'2021-01-01 00:00:00')
    max_rows = int(st.text_input("Max Rows","250"))
    long_sma = st.slider("MA Long",min_value=20,max_value=500,value=50)
    short_sma = st.slider("MA Short",min_value=5,max_value=50,value=20)
    ssl = st.slider("SSL",min_value=5,max_value=25,value=10)
    macd_fast = int(st.text_input("MACD Fast",'26'))
    macd_slow = int(st.text_input("MACD Slow","12"))
    macd_signal = int(st.text_input("MACD Signal","9"))
    macd_lower = int(st.text_input("MacD Overbought","-400"))
    
    back_test_rows = max_rows - long_sma
    image_name = "-".join([str(i) for i in [valuta,timeframe,max_rows,long_sma,short_sma,macd_fast,macd_slow,macd_signal,macd_lower,ssl]])+'.png'
    print(f"Fetching new bars for {timestamp}")
    raw_data = ccxt_object.get_historical_data(valuta=valuta,timeframe=timeframe,since=since,max_rows=max_rows)
    
    strategy_object = ma_macd_ssl(raw_data)
    df = strategy_object.compute_new(long_sma=long_sma,short_sma=short_sma,macd_lower=macd_lower,ssl=ssl,macd_fast=macd_fast,macd_slow=macd_slow,macd_signal=macd_signal)

    df = df.set_index('timestamp')
    st.header("Raw Data and all Indicators")
    st.dataframe(df)
    data = df[['open','high','low','close','volume','in_uptrend']]
    data = data[-back_test_rows:]
    st.header("Plotted Data:")
    st.dataframe(data)
    data = GormData(dataname=data, timeframe=bt.TimeFrame.Minutes)
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(virtual_cash)

    cerebro.adddata(data)
    cerebro.addstrategy(BackTestUptrend)
    cerebro.broker.setcommission(commission=commision)
    st.header('Backtest with Backtrader')
    st.text('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    cerebro.run()
    st.text('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    st.text(f"Plotting last {long_sma} entries for timeframe {timeframe}")
    
    #figure = cerebro.plot(style ='candlebars')[0][0]
    figure = cerebro.plot(volume=False, width=150,height=100,tight=False)[0][0]
    filepath = os.path.dirname(os.path.realpath(__file__)) + '/backtests/'+image_name.replace('/','')
    filepath_local = os.path.dirname(os.path.realpath(__file__)) + '\\backtests\\'+image_name.replace('/','')
    #try:
    st.text(filepath)
    figure.savefig(filepath)
    #st.image('backetest/'+image_name.replace('/',''))
    st.image(filepath)

    #except:
    #    figure.savefig(filepath_local)
    #    st.image('backtests\\'+image_name.replace('/',''))
            
            
    # Trades
    try:
        db_name = valuta.replace('/','')+'_'+timeframe
        pg_object = postgres()
        pg_object.open_connect()
        data = pg_object.cache_trades(db_name)
        pg_object.close_connect()
        st.write(data)
    except:
        st.write("")
        st.write(f"No trades exists for this strategy({valuta},{timeframe})")

run_app()
