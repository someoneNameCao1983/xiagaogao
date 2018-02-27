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
    DAY_START1 = dt(8, 59)  # 日盘启动和停止时间
    DAY_END1 = dt(10, 15)
    DAY_START2 = dt(10, 29)  # 日盘启动和停止时间
    DAY_END2 = dt(11, 30)
    DAY_START3 = dt(13, 29)  # 日盘启动和停止时间
    DAY_END3 = dt(15, 00)

    NIGHT_START = dt(20, 50)  # 夜盘启动和停止时间
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
    DAY_START1 = dt(8, 59)  # 日盘启动和停止时间
    DAY_END1 = dt(10, 15)
    DAY_START2 = dt(10, 29)  # 日盘启动和停止时间
    DAY_END2 = dt(11, 30)
    DAY_START3 = dt(13, 29)  # 日盘启动和停止时间
    DAY_END3 = dt(14, 59)

    NIGHT_START = dt(20, 59)  # 夜盘启动和停止时间
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
    DAY_START1 = dt(8, 59)  # 日盘启动和停止时间
    DAY_END1 = dt(10, 15)
    DAY_START2 = dt(10, 29)  # 日盘启动和停止时间
    DAY_END2 = dt(11, 30)
    DAY_START3 = dt(13, 29)  # 日盘启动和停止时间
    DAY_END3 = dt(15, 00)

    NIGHT_START = dt(20, 59)  # 夜盘启动和停止时间
    NIGHT_END = dt(23, 30)

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
    DAY_START1 = dt(8, 59)  # 日盘启动和停止时间
    DAY_END1 = dt(10, 15)
    DAY_START2 = dt(10, 29)  # 日盘启动和停止时间
    DAY_END2 = dt(11, 30)
    DAY_START3 = dt(13, 29)  # 日盘启动和停止时间
    DAY_END3 = dt(15, 00)

    NIGHT_START = dt(21, 00)  # 夜盘启动和停止时间
    NIGHT_END = dt(23, 30)

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
    DAY_START1 = dt(9, 14)  # 日盘启动和停止时间
    DAY_END1 = dt(11, 30)
    DAY_START2 = dt(12, 59)  # 日盘启动和停止时间
    DAY_END2 = dt(15, 00)
    quoteH = bar.datetime.strftime('%H')
    quoteMin = bar.datetime.strftime('%M')

    bartime = dt(int(quoteH), int(quoteMin))
    #if self.bar:
    if DAY_END1 >= bartime >= DAY_START1 or DAY_END2 >= bartime >= DAY_START2:
        return True
    else:
        #print ('非交易时间的数据 %s' % bar.datetime)
        return False
def rbOpenTime(bar):
    rbStopTime = ['2245', '2246', '2247', '2248', '2249', '2250', '2251', '2252', '2253', '2254', '2255', '2256', '2257', '2258', '2259',
          '1445', '1446', '1447', '1448', '1449', '1450', '1451', '1452', '1453', '1454', '1455', '1456', '1457', '1458', '1459',
          '1121','1122','1123', '1124','1125', '1126', '1127', '1128', '1129',
          '1009', '1010', '1011', '1012', '1013', '1014', '1015'
          '0859', '0900', '0901', '0902', '0903', '0904', '0905', '0906',
          '2059', '2100', '2101', '2102', '2103', '2104', '2105', '2106']
    rbContractDay = ['2016/8/16', '2016/11/25', '2017/3/21', '2017/8/4']
    if bar.symbol == 'RB':
        mint = bar.datetime.strftime('%H%M')
        xq = bar.datetime.weekday()
        if bar.date in rbContractDay or mint in rbStopTime:
            isOpen = True
        elif xq == 4 and (bar.datetime.strftime('%H') == '21' or bar.datetime.strftime('%H') == '22'):
            isOpen = True
            # self.output('周五：' + bar.datetime.strftime('%Y%m%d-%H%M'))
        else:
            isOpen = False
    return isOpen