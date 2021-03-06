# encoding: UTF-8

"""
展示如何执行策略回测。
"""

from __future__ import division

from time import time

from vnpy.trader.app.ctaStrategy.ctaBacktesting import BacktestingEngine, TICK_DB_NAME, MINUTE_DB_NAME, OptimizationSetting

if __name__ == '__main__':
    from vnpy.trader.app.ctaStrategy.strategy.strategyCtyDemo import CtyEmaDemoStrategy

    start = time()

    # 创建回测引擎
    engine = BacktestingEngine()
    engine.clearBacktestingResult()

    # 设置引擎的回测模式为K线
    #engine.setBacktestingMode(engine.TICK_MODE)
    engine.setBacktestingMode(engine.BAR_MODE)
    # 设置回测用的数据起始日期 tick data no need initDay
    engine.setStartDate('20170901', initDays=1)
    # 设置产品相关参数
    engine.setSlippage(1)     # 滑点
    engine.setRate(1/10000)   # 万3
    engine.setSize(10)         # 合约大小
    engine.setPriceTick(1)    # 股指最小价格变动
    
    # 设置使用的历史数据库
    #engine.setDatabase(TICK_DB_NAME, 'rb18012')
    engine.setDatabase(MINUTE_DB_NAME, 'RB0000')
    '''
    engine.setBacktestingMode(engine.BAR_MODE)
    engine.setStartDate('20100101', initDays=1)
    #设置产品相关参数
    engine.setSlippage(0.2)  # 滑点
    engine.setRate(0.3 / 10000)  # 万5
    engine.setSize(300)  # 合约大小
    engine.setPriceTick(0.2)  # 股指最小价格变动
    engine.setDatabase(MINUTE_DB_NAME, 'IF0000')
    '''
    # 在引擎中创建策略对象 artLengt是atr测率的参数,vtSymbol是策略模板的参数，只支持单和约测率
    #d = {'vtSymbol': 'IF0000', 'fastK': 7, 'profitRate': 34, 'slowKRate': 6, 'margin': 0.22, 'offsetRate': 1}
    d = {'vtSymbol': 'RB0000', 'fastK': 6, 'profitRate': 40, 'slowK': 31, 'maxHoldPos': 1, 'margin': 0.1, 'offsetRate': 2, 'addRate':2}
    engine.initStrategy(CtyEmaDemoStrategy, d)

    # 开始跑回测
    engine.runBacktesting()
    # 显示计算收益
    engine.calculateBacktestingResult()
    #engine.calculateDailyResult()
    #保存回测记录
    engine.saveBackTestingData()
    #print u'运算完毕，耗时：%s' % (time() - start)
    # 显示回测结果
    #engine.showDailyResult()
    engine.showBacktestingResult()

    print u'运算完毕，耗时：%s' % (time() - start)
