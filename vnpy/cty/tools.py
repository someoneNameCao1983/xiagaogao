# encoding: UTF-8

# AUTHOR:Tianyang.Cao
# WeChat/QQ: 54831165

from sqlalchemy import create_engine
from vnpy.trader.vtGlobal import globalSetting
from sqlalchemy.orm import sessionmaker
from time import time
import copy
#
def saveDataFrameToMysql(df, tname, clear=True):

    start = time()
    engine = create_engine(globalSetting['mysqlUrl'])
    if clear:
        df.to_sql(tname, engine, if_exists='replace')
    else:
        df.to_sql(tname, engine, if_exists='append')
    print u'插入完毕，耗时：%s' % (time() - start)
    
# 插入mysql
def saveEntityListToMysql(EntityDict):
    start = time()
    engine = create_engine(globalSetting['mysqlUrl'])
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

def saveEntityToMysql(Entity):
    engine = create_engine(globalSetting['mysqlUrl'])
    semake = sessionmaker(bind=engine)
    session = semake()
    session.add(Entity)
    session.commit()
