# encoding: UTF-8

"""
展示如何执行策略回测。
"""

from __future__ import division
from time import time
from sqlalchemy import *
from vnpy.trader.vtGlobal import globalSetting
from vnpy.trader.app.ctaStrategy.ctaBacktesting import BacktestingEngine, MINUTE_DB_NAME,TICK_DB_NAME


if __name__ == '__main__':
    from vnpy.trader.app.ctaStrategy.strategy.strategyEmaDemo import EmaDemoStrategy

    start = time()

    # 创建回测引擎
    engine = BacktestingEngine()
    engine.clearBacktestingResult()
    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.TICK_MODE)

    # 设置回测用的数据起始日期 tick data no need initDay
    engine.setStartDate('20171101', initDays=0)
    
    # 设置产品相关参数
    engine.setSlippage(0.2)     # 股指1跳
    engine.setRate(10/10000)   # 万0.3
    engine.setSize(10)         # 股指合约大小
    engine.setPriceTick(0.1)    # 股指最小价格变动
    
    # 设置使用的历史数据库
    engine.setDatabase(TICK_DB_NAME, 'rb1801')
    
    # 在引擎中创建策略对象 artLengt是atr测率的参数,vtSymbol是策略模板的参数，只支持单和约测率
    d = {'vtSymbol': 'rb1801'}
    engine.initStrategy(EmaDemoStrategy, d)

    # 开始跑回测
    engine.runBacktesting()
    # 显示计算收益
    #engine.calculateBacktestingResult()
    engine.calculateDailyResult()
    #保存回测记录
    engine.saveDictData()
    print u'运算完毕，耗时：%s' % (time() - start)
    # 显示回测结果
    engine.showDailyResult()
    #engine.showBacktestingResult()
