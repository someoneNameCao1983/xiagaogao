# encoding: UTF-8

# AUTHOR:Tianyang.Cao
# WeChat/QQ: 54831165

from sqlalchemy import *
from vnpy.trader.vtObject import *
from vnpy.trader.vtGlobal import globalSetting
from sqlalchemy.orm import sessionmaker
from time import time
from datetime import  time as dt
from datetime import datetime, timedelta
import pymongo
import copy
import sys
from sqlalchemy.ext.declarative import *
#
TICK_DB_NAME = 'VnTrader_Tick_Db'
DAILY_DB_NAME = 'VnTrader_Daily_Db'
MINUTE_DB_NAME = 'VnTrader_1Min_Db'

def saveDataFrameToMysql(df, tname, clear=True):

    start = time()
    engine = create_engine(globalSetting['mysqlUrl'])
    if clear:
        df.to_sql(tname, engine, if_exists='replace')
    else:
        df.to_sql(tname, engine, if_exists='append')
    print u'插入完毕，耗时：%s' % (time() - start)

#查询mysql
def loadhistroyDataMysql():

    start = time()
    engine = create_engine(globalSetting['btiUrl'])
    semake = sessionmaker(bind=engine)
    session = semake()
    for instance in session.query(VtBarData).filter(VtBarData.id == 1):
        print instance.low

# 插入mysql
def saveEntityDictToMysql(EntityDict,DbName):
    start = time()
    # simnow模拟
    if DbName == 'Simnow':
        engine = create_engine(globalSetting['simnow'])
    # 行情库
    elif DbName == 'Quote':
        engine = create_engine(globalSetting['quoteUrl'])
    # 回测库
    elif DbName == 'BTI':
        engine = create_engine(globalSetting['btiUrl'])
    else:
        print '没有指定数据'
        engine = create_engine(globalSetting['mysqlUrl'])
    #Base.metadata.create_all(engine)
    semake = sessionmaker(bind=engine)
    session = semake()
    tradeCount = 0
    for trade in EntityDict.values():
        trade = copy.copy(trade)
        tradeCount += 1
        session.add(trade)
        if tradeCount % 1000 == 0:
            session.commit()
    session.commit()
    print u'插入完毕，耗时：%s' % (time() - start)
# 插入mysql
def saveEntityToMysql(Entity,DbName):
    #simnow模拟
    if DbName == 'Simnow':
        engine = create_engine(globalSetting['simnowUrl'])
    # 行情库
    elif DbName == 'Quote':
        engine = create_engine(globalSetting['quoteUrl'])
    #回测库
    elif DbName == 'BTI':
        engine = create_engine(globalSetting['btiUrl'])
    else:
        print '没有指定数据'
        engine = create_engine(globalSetting['mysqlUrl'])
    semake = sessionmaker(bind=engine)
    session = semake()
    session.add(Entity)
    session.commit()
# 插入mysql
def saveEntityListToMysql(EntityList,DbName):
    start = time()
    #simnow模拟
    if DbName == 'Simnow':
        engine = create_engine(globalSetting['simnowUrl'])
    # 行情库
    elif DbName == 'Quote':
        engine = create_engine(globalSetting['quoteUrl'])
    #回测库
    elif DbName == 'BTI':
        engine = create_engine(globalSetting['btiUrl'])
    else:
        print '没有指定数据'
        engine = create_engine(globalSetting['mysqlUrl'])
    semake = sessionmaker(bind=engine)
    session = semake()
    tradeCount = 0
    for trade in EntityList:
        trade = copy.copy(trade)
        tradeCount += 1
        session.add(trade)
        if tradeCount % 1000 == 0:
            session.commit()
    session.commit()
    print u'插入完毕，耗时：%s' % (time() - start)
#行情转换到mongodb
def convert2Mongo(Conract,DbName):
    start = time()
    # simnow模拟
    if DbName == 'Simnow':
        engine = create_engine(globalSetting['dssUrl'])
    # 行情库
    elif DbName == 'Quote':
        engine = create_engine(globalSetting['quoteUrl'])
    # 回测库
    elif DbName == 'BTI':
        engine = create_engine(globalSetting['btiUrl'])
    else:
        print '没有指定数据'
        engine = create_engine(globalSetting['mysqlUrl'])

    engine.echo = True
    Base.metadata.create_all(engine)
    m = MetaData(bind=engine)
    tick = Table('tick_data', m, autoload=True)
    s = tick.select().offset(1000000).limit(2000000)
    #s = tick.select().offset(0).limit(1000000)
    rs = s.execute()
    # mongodb 连接
    client = pymongo.MongoClient(globalSetting['mongoHost'], globalSetting['mongoPort'])
    collection = client[TICK_DB_NAME][Conract]
    #collection.drop()
    #collection.ensure_index([('_id', pymongo.ASCENDING)])
    count = 0
    recordlist = []
    for row in rs:
        tick = VtTickData()
        tick.id = row['id']
        tick.exchange = row['exchange']
        tick.symbol = row['symbol']
        tick.datetime = row['datetime']
        tick.lastPrice = row['lastPrice']
        tick.highPrice = row['highPrice']
        tick.lowPrice = row['lowPrice']
        tick.openPrice = row['openPrice']
        tick.askPrice1 = row['askPrice1']
        tick.bidPrice1 = row['bidPrice1']
        tick.askVolume1 = row['askVolume1']
        tick.bidVolume1 = row['bidVolume1']
        tick.date = row['date']
        tick.time = row['time']
        tick.datetime = row['datetime']
        tick.exchange = 'SHFE'
        tick.vtSymbol = 'rb1801'
        flt = {'datetime': tick.datetime}
        tick2 = {"_id": tick.id, "symbol": tick.symbol, "vtSymbol": tick.vtSymbol, "lastPrice": tick.lastPrice, "highPrice": tick.highPrice,
                 "lowPrice": tick.lowPrice,
                 "datetime": tick.datetime,
                 "exchange": tick.exchange, "date": tick.date, "time": tick.time,
                 "openPrice": tick.openPrice, "askPrice1": tick.askPrice1, "bidPrice1": tick.bidPrice1,"datetime": tick.datetime,
                 "askVolume1": tick.askVolume1, "bidVolume1": tick.bidVolume1}
        recordlist.append(tick2)
        count += 1
        if count % 20000 == 0:
            collection.insert_many(recordlist)
            del recordlist[:]
            print ("%d record import to mongodb" % count)
    if len(recordlist) > 0:
        collection.insert_many(recordlist)
    print (u'%d 条记录 插入完毕，耗时：%s' % (count,(time() - start )))

#处理一下极大数和极小数
def roundPrice(price):
    if price == sys.float_info.max:
        newPrice = -1
    elif price == sys.float_info.min:
        newPrice = -2
    else:
        newPrice = price
    return newPrice
# ----------------------------------------------------------------------
def validateNI(bar):
    """数据检验"""
    DAY_START1 = dt(9, 00)  # 日盘启动和停止时间
    DAY_END1 = dt(10, 14)
    DAY_START2 = dt(10, 30)  # 日盘启动和停止时间
    DAY_END2 = dt(11, 29)
    DAY_START3 = dt(13, 30)  # 日盘启动和停止时间
    DAY_END3 = dt(14, 59)

    NIGHT_START = dt(21, 00)  # 夜盘启动和停止时间
    NIGHT_END = dt(23, 59)

    NIGHT_START2 = dt(00, 00)  # 夜盘启动和停止时间
    NIGHT_END2 = dt(00, 59)

    quoteH = bar.datetime.strftime('%H')
    quoteMin = bar.datetime.strftime('%M')

    bartime = dt(int(quoteH), int(quoteMin))
    #if self.bar:
    if ((bartime >= DAY_START1 and bartime <= DAY_END1) or
            (bartime >= DAY_START2 and bartime <= DAY_END2) or
            (bartime >= DAY_START3 and bartime <= DAY_END3) or
            (bartime >= NIGHT_START) and(bartime <= NIGHT_END) or
            (bartime >= NIGHT_START2) and (bartime <= NIGHT_END2)
        ):
        return True
    else:
        #print ('非交易时间的数据 %s' % bar.datetime)
        return False

def validateRB(bar):
    """数据检验"""
    DAY_START1 = dt(9, 00)  # 日盘启动和停止时间
    DAY_END1 = dt(10, 14)
    DAY_START2 = dt(10, 30)  # 日盘启动和停止时间
    DAY_END2 = dt(11, 29)
    DAY_START3 = dt(13, 30)  # 日盘启动和停止时间
    DAY_END3 = dt(14, 59)

    NIGHT_START = dt(21, 00)  # 夜盘启动和停止时间
    NIGHT_END = dt(22, 59)

    quoteH = bar.datetime.strftime('%H')
    quoteMin = bar.datetime.strftime('%M')

    bartime = dt(int(quoteH), int(quoteMin))

    if ((bartime >= DAY_START1 and bartime <= DAY_END1) or
            (bartime >= DAY_START2 and bartime <= DAY_END2) or
            (bartime >= DAY_START3 and bartime <= DAY_END3) or
            (bartime >= NIGHT_START) and(bartime <= NIGHT_END)
        ):
        return True
    else:
        #print ('非交易时间的数据 %s' % bar.datetime)
        return False

def validateJ(bar):
    """数据检验"""
    DAY_START1 = dt(9, 00)  # 日盘启动和停止时间
    DAY_END1 = dt(10, 14)
    DAY_START2 = dt(10, 30)  # 日盘启动和停止时间
    DAY_END2 = dt(11, 29)
    DAY_START3 = dt(13, 30)  # 日盘启动和停止时间
    DAY_END3 = dt(14, 59)

    NIGHT_START = dt(21, 00)  # 夜盘启动和停止时间
    NIGHT_END = dt(23, 29)

    quoteH = bar.datetime.strftime('%H')
    quoteMin = bar.datetime.strftime('%M')

    bartime = dt(int(quoteH), int(quoteMin))
    #if self.bar:
    if ((bartime >= DAY_START1 and bartime <= DAY_END1) or
            (bartime >= DAY_START2 and bartime <= DAY_END2) or
            (bartime >= DAY_START3 and bartime <= DAY_END3) or
            (bartime >= NIGHT_START) and(bartime <= NIGHT_END)
        ):
        return True
    else:
        #print ('非交易时间的数据 %s' % bar.datetime)
        return False

def validateMA(bar):
    """数据检验"""
    DAY_START1 = dt(9, 00)  # 日盘启动和停止时间
    DAY_END1 = dt(10, 14)
    DAY_START2 = dt(10, 30)  # 日盘启动和停止时间
    DAY_END2 = dt(11, 29)
    DAY_START3 = dt(13, 30)  # 日盘启动和停止时间
    DAY_END3 = dt(14, 59)

    NIGHT_START = dt(21, 00)  # 夜盘启动和停止时间
    NIGHT_END = dt(23, 29)

    quoteH = bar.datetime.strftime('%H')
    quoteMin = bar.datetime.strftime('%M')

    bartime = dt(int(quoteH), int(quoteMin))
    #if self.bar:
    if ((bartime >= DAY_START1 and bartime <= DAY_END1) or
            (bartime >= DAY_START2 and bartime <= DAY_END2) or
            (bartime >= DAY_START3 and bartime <= DAY_END3) or
            (bartime >= NIGHT_START) and(bartime <= NIGHT_END)
        ):
        return True
    else:
        #print ('非交易时间的数据 %s' % bar.datetime)
        return False
def validateIF(bar):
    """数据检验"""
    DAY_START1 = dt(9, 30)  # 日盘启动和停止时间
    DAY_END1 = dt(11, 29)

    quoteH = bar.datetime.strftime('%H')
    quoteMin = bar.datetime.strftime('%M')

    bartime = dt(int(quoteH), int(quoteMin))
    #if self.bar:
    if (bartime >= DAY_START1 and bartime <= DAY_END1):
        return True
    else:
        #print ('非交易时间的数据 %s' % bar.datetime)
        return False