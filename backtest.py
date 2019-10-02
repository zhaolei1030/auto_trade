# -*- coding: utf-8 -*-
import pandas as pd
import math
                                     #设定开盘价，收盘价的时间
close_ = pd.to_datetime("15:00:00")
all_close,all_high,all_low = {},{}, {}, 
data_file_content = pd.read_csv('D:/5min-tick-2016-01-06-rb0001.csv')          
data_file_content['Date'] = pd.to_datetime(data_file_content['Date'])
data_file_content['Time'] = pd.to_datetime(data_file_content['Time'])
date = data_file_content['Date'].drop_duplicates()                             #提取所有天数
date = date.tolist()                       
for i in date:                                                                 #提取指标所需要的计算数值
    all_high[i] = data_file_content.loc[data_file_content['Date'] == i]['High'].max()
    all_low[i] = data_file_content.loc[data_file_content['Date'] == i]['Low'].min()
    all_close[i] = data_file_content.loc[(data_file_content['Date'] == i) & (data_file_content['Time'] == close_)]['Close'].max()
close = pd.Series(all_close)                                                   # 将相应的指标提取并且转化为dataframe格式
low = pd.Series(all_low)
high = pd.Series(all_high)
day_data= pd.concat([close,low,high],axis = 1)
day_data.columns = ['close','low','high']
day_data = day_data.fillna(day_data.mean())                                  #将空值填充为列的均值   
         
def rbreaker(x,y,z):
    """
    复现r-breaker策略
    :param x:
    :param y:
    :param z:
    :return:
    """
    break_buy,observe_sell,reverse_sell,reverse_buy,observe_buy,break_sell = {}, {}, {}, {}, {}, {},   #构造六项突破指标
    
    for i in date:    
        break_buy[i] = (5/3*day_data.loc[i,'high']+2/3*day_data.loc[i,'close']-4/3*day_data.loc[i,'low'])
        observe_sell[i]=(4/3*day_data.loc[i,'high']-2/3*day_data.loc[i,'low']+1/3*day_data.loc[i,'close'])
        reverse_sell[i]=(2/3*day_data.loc[i,'high']+2/3*day_data.loc[i,'close']-1/3*day_data.loc[i,'low'])
        reverse_buy[i]=(-1/3*day_data.loc[i,'high']+2/3*day_data.loc[i,'close']+2/3*day_data.loc[i,'low'])
        observe_buy[i]=-2/3*day_data.loc[i,'high']+4/3*day_data.loc[i,'low']+1/3*day_data.loc[i,'close']
        break_sell[i]=(-4/3*day_data.loc[i,'high']+2/3*day_data.loc[i,'close']+5/3*day_data.loc[i,'low'])                                             #将每日的六项指标转化为dataframe格式，便于之后调用
    break_buy = pd.Series(break_buy)
    observe_sell = pd.Series(observe_sell)
    reverse_sell = pd.Series(reverse_sell)
    reverse_buy = pd.Series(reverse_buy)
    observe_buy =pd.Series(observe_buy)
    break_sell = pd.Series(break_sell)
    index_data= pd.concat([break_buy,observe_sell,reverse_sell,reverse_buy,observe_buy,break_sell],axis = 1)
    index_data.columns = ['break_buy','observe_sell','reverse_sell','reverse_buy','observe_buy','break_sell']
    index_data = index_data.fillna(index_data.mean())                              #六项指标构造完成
    base_price = 1e+7 
    withdraw_rate = x
    sell_rate = y
    buy_rate = z
    money = 1e+6
    stock_number = 0
    for j in  range(len(date)-1):                                                  #数据回测函数，假定交易成本为万分之三
        time_line_trade = data_file_content.loc[data_file_content['Date'] == date[j+1]]['Close']    #按天提取每日的开盘价收盘价构成时间序列  
        time_line_trade = time_line_trade.as_matrix() 
        time_line_trade = time_line_trade.ravel()
        observe = 'Wait'                                                    #初始观察状态为wait
        for i in range(len(time_line_trade)):
            if time_line_trade[i] >= index_data.iloc[j].loc['break_buy']:             #突破时买入,同时观察状态变为wait
                observe = 'Wait'
                stock_number += math.ceil(money*buy_rate/index_data.iloc[j].loc['break_buy']/(1+0.001))
                money -= math.ceil(money*buy_rate/(index_data.iloc[j].loc['break_buy']/(1+0.001)))*(index_data.iloc[j].loc['break_buy']*(1+0.001))
                if base_price == 1e+7 :
                    base_price = index_data.iloc[j].loc['break_buy']
                break 
            elif time_line_trade[i] <= index_data.iloc[j].loc['break_sell']:           #突破时卖出，同时观察状态变为wait
                observe = 'Wait' 
                money += sell_rate*stock_number*(index_data.iloc[j].loc['break_sell']*(1-0.001))
                stock_number -= sell_rate*stock_number
                if index_data.iloc[j].loc['break_sell'] <= base_price*(1-withdraw_rate) :
                    money += stock_number*(index_data.iloc[j].loc['break_sell']*(1-0.001))
                    stock_number = 0
                break
            elif observe == 'Buy':                                                 #在观察区间的时候，如果是买入观察期，那么超过翻转买入就买，如果同时突破了观察卖出指标，观察状态改为sell
                if time_line_trade[i] >= index_data.iloc[j].loc['reverse_buy']:
                    if time_line_trade[i] >= index_data.iloc[j].loc['observe_sell']:
                        observe = 'Sell'
                        stock_number +=  math.ceil(money*buy_rate/(index_data.iloc[j].loc['reverse_buy']/(1+0.001)))
                        money -= math.ceil(money*buy_rate/(index_data.iloc[j].loc['reverse_buy']/(1+0.001)))*(index_data.iloc[j].loc['reverse_buy']*(1+0.001))
                        if base_price == 1e+7 :
                             base_price = index_data.iloc[j].loc['reverse_buy']
                        break
                    else:
                        observe = 'Wait'
                        stock_number +=  math.ceil(money*buy_rate/(index_data.iloc[j].loc['reverse_buy']/(1+0.001)))
                        money -= math.ceil(money*buy_rate/(index_data.iloc[j].loc['reverse_buy']/(1+0.001)))*(index_data.iloc[j].loc['reverse_buy']*(1+0.001))
                        if base_price == 1e+7 :
                             base_price = index_data.iloc[j].loc['reverse_buy']
                        break
                else:
                    continue  
            elif observe == 'Sell':                                                #在观察区间的时候，如果是卖出观察期，那么超过翻转卖出就卖，如果同时突破了观察买入指标，观察状态改为buy
                if time_line_trade[i] <= index_data.iloc[j].loc['reverse_sell']:
                    if time_line_trade[i] <= index_data.iloc[j].loc['observe_buy']:
                        observe = 'Buy'
                        money += sell_rate*stock_number*(index_data.iloc[j].loc['reverse_sell']/(1+0.001))
                        stock_number -= stock_number*sell_rate
                        if index_data.iloc[j].loc['reverse_sell'] <= base_price*(1-withdraw_rate) :
                            money += stock_number*(index_data.iloc[j].loc['reverse_sell']*(1-0.001))
                            stock_number = 0
                        break
                    else:
                        observe = 'Wait'
                        money += sell_rate*stock_number*(index_data.iloc[j].loc['reverse_sell']/(1+0.001))
                        stock_number -= stock_number*sell_rate       
                        if index_data.iloc[j].loc['reverse_sell'] <= base_price*(1-withdraw_rate) :
                            money += stock_number*(index_data.iloc[j].loc['reverse_sell']*(1-0.001))
                            stock_number = 0
                        break
                else:
                    continue 
            elif observe == 'Wait':                                                #没直接买入卖出而又不处于观察期的时候，判断是否能够进入观察期
                if time_line_trade[i] <= index_data.iloc[j].loc['observe_buy']:
                    observe = 'Buy'
                elif time_line_trade[i] >= index_data.iloc[j].loc['observe_sell']:
                    observe = 'Sell'
                else:
                    continue
            else:
                continue    
    
    #profit = money + stock_number*data_file_content.loc[(data_file_content['Date'] == date[j]) & (data_file_content['Time'] == close_)]['Close'].max()
    #daily_proift[date[j]] = profit              #每天的交易如果立刻结算后的价格
    money += stock_number*2259/(1+0.001)
    return money                  #打印总资产
if __name__ == '__main__':
    choice = [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1]
    choice1 = []
    #for i in choice[:6]:
    #    for j in choice:
    #        for k in choice:
     #           profit = rbreaker(i,j,k)
    #            choice1.append(profit)
    #print([choice1,max(choice1),choice1.index(max(choice1))])
    print(rbreaker(0.3,1,1))