# encoding: UTF-8

"""
展示如何执行策略回测。
"""

from __future__ import division

from time import time

from vnpy.trader.app.ctaStrategy.ctaBacktesting import BacktestingEngine, TICK_DB_NAME

if __name__ == '__main__':
    from vnpy.trader.app.ctaStrategy.strategy.strategyCtyDemo import CtyEmaDemoStrategy

    start = time()

    # 创建回测引擎
    engine = BacktestingEngine()
    engine.clearBacktestingResult()
    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.TICK_MODE)

    # 设置回测用的数据起始日期 tick data no need initDay
    engine.setStartDate('2017117', initDays=1)

    # 设置产品相关参数
    engine.setSlippage(0.2)     # 滑点
    engine.setRate(5/10000)   # 万5
    engine.setSize(10)         # 合约大小
    engine.setPriceTick(1)    # 股指最小价格变动
    
    # 设置使用的历史数据库
    engine.setDatabase(TICK_DB_NAME, 'rb1801')
    
    # 在引擎中创建策略对象 artLengt是atr测率的参数,vtSymbol是策略模板的参数，只支持单和约测率
    d = {'vtSymbol': 'rb1801'}
    engine.initStrategy(CtyEmaDemoStrategy, d)

    # 开始跑回测
    engine.runBacktesting()
    # 显示计算收益
    engine.calculateBacktestingResult()
    #engine.calculateDailyResult()
    #保存回测记录
    engine.saveBackTestingData()
    print u'运算完毕，耗时：%s' % (time() - start)
    # 显示回测结果
    #engine.showDailyResult()
    engine.showBacktestingResult()
