# encoding: UTF-8

"""
展示如何执行参数优化。
"""

from __future__ import division
from vnpy.trader.app.ctaStrategy.ctaBacktesting import BacktestingEngine, TICK_DB_NAME, MINUTE_DB_NAME, OptimizationSetting
from time import time


if __name__ == '__main__':
    from vnpy.trader.app.ctaStrategy.strategy.strategyCtyDemo import CtyEmaDemoStrategy
    start = time()

    # 创建回测引擎
    engine = BacktestingEngine()

    # 设置引擎的回测模式
    engine.setBacktestingMode(engine.BAR_MODE)
    engine.setStartDate('20170401', initDays=1)
    # 设置品种相关参数
    engine.setSlippage(1)  # 滑点
    engine.setRate(1 / 10000)  # 万5
    engine.setSize(10)  # 合约大小
    engine.setPriceTick(1)  # 股指最小价格变动
    #engine.setDatabase(TICK_DB_NAME, 'rb18012')
    engine.setDatabase(MINUTE_DB_NAME, 'RB0000')
    '''
    engine.setBacktestingMode(engine.BAR_MODE)
    engine.setStartDate('20100101', initDays=1)
    # 设置品种相关参数
    engine.setSlippage(0.2)  # 滑点
    engine.setRate(0.3 / 10000)  # 万0.3
    engine.setSize(300)  # 合约大小
    engine.setPriceTick(0.2)  # 股指最小价格变动
    engine.setDatabase(MINUTE_DB_NAME, 'IF0000')
    '''
    # 跑优化

    setting = OptimizationSetting()  # 新建一个优化任务设置对象
    setting.setOptimizeTarget('drawdown')  # 设置优化排序的目标是策略净盈利
    setting.addParameter('fastK',6,21,5)  # 增加第一个优化参数atrLength，起始12，结束20，步进2
    setting.addParameter('slowK', 26,61,5)
    setting.addParameter('profitRate', 40)
    setting.addParameter('offsetRate', 2)  # 固定2倍 也就是止损2%
    setting.addParameter('maxHoldPos', 1)  # 固定保证金率
    setting.addParameter('addRate', 2)  # 固定2%
    setting.addParameter('margin', 0.1)    # 固定保证金率


    # 性能测试环境：I7-3770，主频3.4G, 8核心，内存16G，Windows 7 专业版
    # 测试时还跑着一堆其他的程序，性能仅供参考
    # 运行单进程优化函数，自动输出结果，耗时：359秒
    engine.runOptimization(CtyEmaDemoStrategy, setting)

    # 多进程优化，耗时：89秒
    #engine.runParallelOptimization(CtyEmaDemoStrategy, setting)

    print u'运算完毕，耗时：%s' % (time() - start)