# encoding: UTF-8

# AUTHOR:Tianyang.Cao
# WeChat/QQ: 54831165
import tushare as ts
from sqlalchemy import create_engine
from vnpy.trader.vtObject import VtTradeData
from vnpy.trader.vtGlobal import globalSetting
from vnpy.cty.tools import saveDataFrameToMysql
from sqlalchemy import FLOAT, Column, Integer, String,DateTime
from sqlalchemy.orm import sessionmaker,relationship
from sqlalchemy.ext.declarative import declarative_base
from vnpy.trader.vtConstant import (EMPTY_STRING, EMPTY_UNICODE,
                                    EMPTY_FLOAT, EMPTY_INT)
Base = declarative_base()


class VtTickData(Base):
    """Tick行情数据类"""
    # ----------------------------------------------------------------------
    __tablename__ = 'monitor_tick_data'
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(32))
    exchange = Column(String(32))  # 交易所代码
    # 成交数据
    lastPrice = Column(FLOAT(10, 4))  # 最新成交价
    lastVolume = Column(Integer)  # 最新成交量
    volume = Column(Integer) #  今天总成交量
    price = Column(FLOAT(10, 4))  # 成交价格
    volume = Column(Integer)  # 成交数量
    openInterest = Column(Integer)  # 持仓量
    time = Column(String(32))     # 时间 11:20:56.5
    date = Column(String(32))   # 日期 20151009
    datetime = Column(DateTime)  # python的datetime时间对象
    # 常规行情
    openPrice = Column(FLOAT(10, 4))  # 今日开盘价
    highPrice = Column(FLOAT(10, 4))  # 今日最高价
    lowPrice = Column(FLOAT(10, 4))  # 今日最低价
    preClosePrice = Column(FLOAT(10, 4))

    upperLimit = Column(FLOAT(10, 4))  # 涨停价
    lowerLimit = Column(FLOAT(10, 4))  # 跌停价
    def __init__(self):
        """Constructor"""
        super(VtTickData, self).__init__()

        # 代码相关
        self.symbol = EMPTY_STRING  # 合约代码
        self.exchange = EMPTY_STRING  # 交易所代码
        self.vtSymbol = EMPTY_STRING  # 合约在vt系统中的唯一代码，通常是 合约代码.交易所代码

        # 成交数据
        self.lastPrice = EMPTY_FLOAT  # 最新成交价
        self.lastVolume = EMPTY_INT  # 最新成交量
        self.volume = EMPTY_INT  # 今天总成交量
        self.openInterest = EMPTY_INT  # 持仓量
        self.time = EMPTY_STRING  # 时间 11:20:56.5
        self.date = EMPTY_STRING  # 日期 20151009
        self.datetime = None  # python的datetime时间对象

        # 常规行情
        self.openPrice = EMPTY_FLOAT  # 今日开盘价
        self.highPrice = EMPTY_FLOAT  # 今日最高价
        self.lowPrice = EMPTY_FLOAT  # 今日最低价
        self.preClosePrice = EMPTY_FLOAT

        self.upperLimit = EMPTY_FLOAT  # 涨停价
        self.lowerLimit = EMPTY_FLOAT  # 跌停价

        # 五档行情
        self.bidPrice1 = EMPTY_FLOAT
        self.bidPrice2 = EMPTY_FLOAT
        self.bidPrice3 = EMPTY_FLOAT
        self.bidPrice4 = EMPTY_FLOAT
        self.bidPrice5 = EMPTY_FLOAT

        self.askPrice1 = EMPTY_FLOAT
        self.askPrice2 = EMPTY_FLOAT
        self.askPrice3 = EMPTY_FLOAT
        self.askPrice4 = EMPTY_FLOAT
        self.askPrice5 = EMPTY_FLOAT

        self.bidVolume1 = EMPTY_INT
        self.bidVolume2 = EMPTY_INT
        self.bidVolume3 = EMPTY_INT
        self.bidVolume4 = EMPTY_INT
        self.bidVolume5 = EMPTY_INT

        self.askVolume1 = EMPTY_INT
        self.askVolume2 = EMPTY_INT
        self.askVolume3 = EMPTY_INT
        self.askVolume4 = EMPTY_INT
        self.askVolume5 = EMPTY_INT

class VtOrderData(Base):
    """订单数据类"""
    # ----------------------------------------------------------------------
    __tablename__ = 'monitor_order_data'
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 代码编号相关
    symbol = Column(String(32))  # 合约代码
    exchange = Column(String(32))  # 交易所代码
    vtSymbol = Column(String(32))  # 合约在vt系统中的唯一代码，通常是 合约代码.交易所代码

    orderID = Column(String(32))  # 订单编号
    vtOrderID = Column(String(32))  # 订单在vt系统中的唯一编号，通常是 Gateway名.订单编号

    # 报单相关
    direction = Column(String(32))  # 报单方向
    offset = Column(String(32))  # 报单开平仓
    price = Column(FLOAT(8,4))  # 报单价格
    totalVolume = Column(Integer)  # 报单总数量
    tradedVolume = Column(Integer)  # 报单成交数量
    status = Column(String(32))  # 报单状态

    orderTime = Column(String(32))  # 发单时间
    cancelTime = Column(String(32))  # 撤单时间

    # CTP/LTS相关
    frontID = Column(String(32))  # 前置机编号
    sessionID = Column(String(32))  # 连接编号

    def __init__(self):
        """Constructor"""
        super(VtOrderData, self).__init__()

        # 代码编号相关
        self.symbol = EMPTY_STRING  # 合约代码
        self.exchange = EMPTY_STRING  # 交易所代码
        self.vtSymbol = EMPTY_STRING  # 合约在vt系统中的唯一代码，通常是 合约代码.交易所代码

        self.orderID = EMPTY_STRING  # 订单编号
        self.vtOrderID = EMPTY_STRING  # 订单在vt系统中的唯一编号，通常是 Gateway名.订单编号

        # 报单相关
        self.direction = EMPTY_UNICODE  # 报单方向
        self.offset = EMPTY_UNICODE  # 报单开平仓
        self.price = EMPTY_FLOAT  # 报单价格
        self.totalVolume = EMPTY_INT  # 报单总数量
        self.tradedVolume = EMPTY_INT  # 报单成交数量
        self.status = EMPTY_UNICODE  # 报单状态

        self.orderTime = EMPTY_STRING  # 发单时间
        self.cancelTime = EMPTY_STRING  # 撤单时间

        # CTP/LTS相关
        self.frontID = EMPTY_INT  # 前置机编号
        self.sessionID = EMPTY_INT  # 连接编号

class VtTradeData(Base):
    """成交数据类"""
    __tablename__ = 'monitor_trade_data'
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(32))
    exchange = Column(String(32))  # 交易所代码
    vtSymbol = Column(String(32))  # 合约在vt系统中的唯一代码，通常是 合约代码.交易所代码

    tradeID = Column(String(32))  # 成交编号
    vtTradeID = Column(String(32))  # 成交在vt系统中的唯一编号，通常是 Gateway名.成交编号

    orderID = Column(String(32))  # 订单编号
    vtOrderID = Column(String(32))  # 订单在vt系统中的唯一编号，通常是 Gateway名.订单编号

    # jiaoyi相关
    direction = Column(String(32))  # 成交方向
    offset = Column(String(32))  # 成交开平仓
    price = Column(FLOAT(10, 4))  # 成交价格
    volume = Column(Integer)  # 成交数量
    tradeTime = Column(String(32))  # 成交时间
    dt = Column(DateTime)  # 成交时间

    # ----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        super(VtTradeData, self).__init__()

        # 代码编号相关
        self.symbol = EMPTY_STRING  # 合约代码
        self.exchange = EMPTY_STRING  # 交易所代码
        self.vtSymbol = EMPTY_STRING  # 合约在vt系统中的唯一代码，通常是 合约代码.交易所代码

        self.tradeID = EMPTY_STRING  # 成交编号
        self.vtTradeID = EMPTY_STRING  # 成交在vt系统中的唯一编号，通常是 Gateway名.成交编号

        self.orderID = EMPTY_STRING  # 订单编号
        self.vtOrderID = EMPTY_STRING  # 订单在vt系统中的唯一编号，通常是 Gateway名.订单编号

        # 成交相关
        self.direction = EMPTY_UNICODE  # 成交方向
        self.offset = EMPTY_UNICODE  # 成交开平仓
        self.price = EMPTY_FLOAT  # 成交价格
        self.volume = EMPTY_INT  # 成交数量
        self.tradeTime = EMPTY_STRING  # 成交时间
        self.dt = None  # 成交时间

class StopOrder(Base):
    """本地停止单"""
    # ----------------------------------------------------------------------
    __tablename__ = 'monitor_stop_order'
    id = Column(Integer, primary_key=True, autoincrement=True)
    vtSymbol = Column(String(32))
    orderType = Column(String(32))
    direction = Column(String(32))
    offset = Column(String(32))
    price = Column(FLOAT(10, 4))
    volume = Column(Integer)

    strategy =  Column(String(32))  # 下停止单的策略对象
    stopOrderID = Column(String(32))  # 停止单的本地编号
    status = Column(String(32))  # 停止单状态
    def __init__(self):
        """Constructor"""
        self.vtSymbol = EMPTY_STRING
        self.orderType = EMPTY_UNICODE
        self.direction = EMPTY_UNICODE
        self.offset = EMPTY_UNICODE
        self.price = EMPTY_FLOAT
        self.volume = EMPTY_INT

        self.strategy = None  # 下停止单的策略对象
        self.stopOrderID = EMPTY_STRING  # 停止单的本地编号
        self.status = EMPTY_STRING  # 停止单状态
    #df = ts.get_tick_data('600848', date='2017-09-26')
#saveDataFrameToMysql(df, 'tick_data')
engine = create_engine(globalSetting['mysqlUrl'])
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)
s = Session()
trade1 = VtOrderData()
trade1.symbol = 'IF1803'
trade2 = VtTickData()
trade2.symbol = 'IF1803'
trade3 = VtTradeData()
trade3.symbol = 'IF1803'
trade4 = StopOrder()
trade4.vtSymbol = 'IF1803'
s.add(trade1)
s.add(trade2)
s.add(trade3)
s.add(trade4)
s.commit()
