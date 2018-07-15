"""
StockTwits Trader Mood PsychSignal dataset

This dataset measures the mood of traders posting messages on 
StockTwits

Key metrics:

bull_scored_messages - total count of bullish sentiment messages
                       scored by PsychSignal's algorithm
bear_scored_messages - total count of bearish sentiment messages
                       scored by PsychSignal's algorithm
bullish_intensity - score for each message's language for the stength
                    of the bullishness present in the messages on a 0-4
                    scale. 0 indicates no bullish sentiment measured, 4
                    indicates strongest bullish sentiment measured. 4 is rare
bearish_intensity - score for each message's language for the stength
                    of the bearish present in the messages on a 0-4 scale.
                    0 indicates no bearish sentiment measured, 4 indicates
                    strongest bearish sentiment measured. 4 is rare
total_scanned_messages - number of messages coming through PsychSignal's
                         feeds and attributable to a symbol regardless of
                         whether the PsychSignal sentiment engine can score
                         them for bullish or bearish intensity
"""
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.factors import CustomFactor, AverageDollarVolume
import pandas as pd
import numpy as np

from quantopian.pipeline.data.psychsignal import stocktwits_free as psychsignal


class PsychSignal(CustomFactor):
    # baseline PsychSignal factor
    # based on previous day bullish and bearish intensity levels
    inputs = [psychsignal.bull_minus_bear]
    window_length = 40
    def compute(self, today, assets, out, bull_minus_bear):
        np.mean(bull_minus_bear, axis=0, out=out)

# Assign short and long baskets
def before_trading_start(context, data):
    results = pipeline_output('factors').dropna()
    lower, upper = results['psychsignal_sentiment'].quantile([.1, .9])
    context.shorts = results[results['psychsignal_sentiment'] <= lower] 
    # Short the positions with highest bearish intensity level
    context.longs = results[results['psychsignal_sentiment'] >= upper] 
    # Long the positions with highest bullish intensity level
    update_universe(context.longs.index | context.shorts.index)
    # from 500 stocks, taking top and bottom 10% of those securities and ivesting with them
    
def initialize(context):
    # Create pipeline
    pipe = Pipeline()
    pipe = attach_pipeline(pipe, name='factors')
    pipe.add(PsychSignal(), "psychsignal_sentiment")
	
    #Screen out penny stocks and low liquidity securities
    dollar_volume = AverageDollarVolume(window_length = 20)
    
    # Only look at top 1000 most liquid securities
    liquidity_rank = dollar_volume.rank(ascending=False) < 200
    pipe.set_screen((dollar_volume > 10**7) & (liquidity_rank))
    
    # Set our shorts and longs and define our benchmark
    context.spy = sid(8554)
    context.shorts = None
    context.longs = None
    
    schedule_function(rebalance, date_rules.every_day())
    schedule_function(cancel_open_orders, date_rules.every_day(),
                      time_rules.market_close())
    set_commission(commission.PerShare(cost=0, min_trade_cost=0)) # no cost to trading

    set_slippage(slippage.FixedSlippage(spread=0))

    
# Will be called on every trade event for the securities you specify. 
def handle_data(context, data):
    record(lever=context.account.leverage,
           exposure=context.account.net_leverage,
           num_pos=len(context.portfolio.positions),
           oo=len(get_open_orders()))

    
def cancel_open_orders(context, data):
    # Cancel any open orders at the end of each day 
    for security in get_open_orders():
        for order in get_open_orders(security):
            cancel_order(order)
    
def rebalance(context, data):
    # Order our shorts
    for security in context.shorts.index:
        if get_open_orders(security):
            continue
        if security in data:  
            order_target_percent(security, -1.0/len(context.shorts.index)) #short its percentage of makeup
            
    # Order our longs
    for security in context.longs.index:
        if get_open_orders(security):
            continue
        if security in data:
            order_target_percent(security, 1.0/len(context.longs.index)) # long percentage
            
    # Order securities not in the portfolio
    for security in context.portfolio.positions:
        if get_open_orders(security):
            continue
        if security in data:
            if security not in (context.longs.index):
                order_target_percent(security, 0)
