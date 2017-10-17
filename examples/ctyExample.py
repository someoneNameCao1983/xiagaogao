# encoding: UTF-8

# AUTHOR:Tianyang.Cao
# WeChat/QQ: 54831165
import tushare as ts
from sqlalchemy import create_engine
from vnpy.trader.vtObject import VtTradeData
from vnpy.trader.vtGlobal import globalSetting
from vnpy.cty.tools import saveDataFrameToMysql
from sqlalchemy import FLOAT, Column, Integer, String
from sqlalchemy.orm import sessionmaker,relationship
from sqlalchemy.ext.declarative import declarative_base
from vnpy.trader.vtConstant import (EMPTY_STRING, EMPTY_UNICODE,
                                    EMPTY_FLOAT, EMPTY_INT)
Base = declarative_base()
class TradeData(Base):
    """成交数据类"""
    # ----------------------------------------------------------------------
    __tablename__ ='trade_data'
    id = Column(Integer, primary_key=True,autoincrement=True)
    symbol = Column(String(32))
    exchange = Column(String(32))  # 交易所代码
    vtSymbol = Column(String(32))  # 合约在vt系统中的唯一代码，通常是 合约代码.交易所代码

    tradeID = Column(String(32))  # 成交编号
    vtTradeID = Column(String(32))  # 成交在vt系统中的唯一编号，通常是 Gateway名.成交编号

    orderID = Column(String(32))  # 订单编号
    vtOrderID = Column(String(32))  # 订单在vt系统中的唯一编号，通常是 Gateway名.订单编号

    #jiaoyi相关
    direction = Column(String(32))  # 成交方向
    offset = Column(String(32))  # 成交开平仓
    price = Column(FLOAT(10, 4))  # 成交价格
    volume = Column(String(32))  # 成交数量
    tradeTime = Column(String(32))  # 成交时间


    def __init__(self):
        """Constructor"""
        #super(VtTradeData, self).__init__()

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

#df = ts.get_tick_data('600848', date='2017-09-26')
#saveDataFrameToMysql(df, 'tick_data')
engine = create_engine(globalSetting['mysqlUrl'])
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)
s = Session()
trade1 = VtTradeData()
trade1.symbol = 'IF1803'
s.add(trade1)
s.commit()
