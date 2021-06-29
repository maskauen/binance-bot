
import config 

# ccxt

ccxt_postgres_table_commands = (
    """
    CREATE TABLE ccxt_"""+config.CURRENCY+""" (
        timestamp TIMESTAMP PRIMARY KEY,
        open VARCHAR(255),
        high VARCHAR(255),
        low VARCHAR(255),
        close VARCHAR(255),
        volume VARCHAR(255),
        previous_close VARCHAR(255),
        highminuslow VARCHAR(255),
        highminuspc VARCHAR(255),
        lowminuspc VARCHAR(255),
        tr VARCHAR(255),
        atr VARCHAR(255),
        basic_upperband VARCHAR(255),
        basic_lowerband VARCHAR(255),
        )
    """,
    """
    CREATE TABLE trades (
    timestamp TIMESTAMP PRIMARY KEY,
    order_type VARCHAR(255) NOT NULL,
    quantity VARCHAR(255) NOT NULL
    )
    """)



ccxt_postgres_delete_command = """DELETE FROM ccxt_"""+config.CURRENCY+""" WHERE timestamp < now() - interval '"""+str(config.DB_PERIOD)+""" minutes';"""

ccxt_sql_string = """INSERT INTO ccxt_"""+config.CURRENCY+""" (timestamp,open,high,low,close,volume,previous_close,highminuslow,highminuspc,lowminuspc,tr,atr,basic_upperband,basic_lowerband) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
trade_sql_string = """INSERT INTO TABLE_NAME (order_type,quantity,timestamp,close) VALUES(%s,%s,%s,%s);"""            


postgres_table_commands = (
    """
    CREATE TABLE """+config.CURRENCY+""" (
        price_id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP,
        opening VARCHAR(255),
        closing VARCHAR(255),
        high VARCHAR(255),
        low VARCHAR(255)
        )
    """,
    """
    CREATE TABLE rand (
    transaction_id SERIAL PRIMARY KEY,
    timestamp VARCHAR(255) NOT NULL,
    trade VARCHAR(255) NOT NULL
    )
    """)


postgres_bot_table = """
    CREATE TABLE TABLE_NAME (
    timestamp TIMESTAMP PRIMARY KEY,
    order_type VARCHAR(255) NOT NULL,
    quantity VARCHAR(255) NOT NULL,
    close VARCHAR(255)
    )
    """

postgres_delete_command = """DELETE FROM """+config.CURRENCY+""" WHERE timestamp < now() - interval '"""+str(config.DB_PERIOD)+""" minutes';"""

# DELETE FROM ethusdt WHERE timestamp < now() - interval '1 week';

postgres_cache_command = """SELECT * FROM """+config.CURRENCY+""";"""
postgres_cache_trades = """SELECT * FROM TABLE_NAME;"""
