
'''
File name: Optimizer.py
Authors: Chris Osufsen, Gabriel Mennesson
Date created: 4/27/2018
'''

import pandas as pd
import numpy as np
import matplotlib as plt
import math
from datetime import date
from dateutil.relativedelta import relativedelta


# read our file
xls = pd.ExcelFile('FA Systematic Strategies.xlsx')

Sectors = ['Telecom','ConsumerDiscretionary','ConsumerStaples','Energy','Financials','Healthcare','Industrials','InfoTech','Materials','Utilities']]

# create an array of thresholds to try
Thresholds = []
for i in np.arange(-3.1, 3.1, .5):
    Thresholds.append(np.asscalar(i))
    print(i)

# global variables to update
best = 0 # sharpe
bestI = 0 # ROE
bestJ = 0 # P/B
bestX = 0 #P/E

df = pd.read_excel(xls)

# only focus on columns relating to our fundamentals and returns
df.drop(df.columns[[1,2,3,4,5,6,7,8,9,10,11,12,13,14]], axis=1, inplace=True)
df = df.drop(df.index[[0,1,2,3,4,5,6,7,8,9,10,11,12]])

# set index to datetime to only run the algorithm on data before 2013
# this is so we can use thresholds on our testing data from 2013-2018 without bias
df['Period ending'] = pd.to_datetime(df['Period ending'])
df = df[(df['Period ending'].dt.year < 2013)]

# for each sector
for sector in Sectors:
    # show sector calculating for
    print(sector)
    # visit the corresponding sector sheet and drop non-essential columns
    df = pd.read_excel(xls, sector)
    df.drop(df.columns[[1,2,3,4,5,6,7,8,9,10,11,12,13,14]], axis=1, inplace=True)
    df = df.drop(df.index[[0,1,2,3,4,5,6,7,8,9,10,11,12]])
    # set index to datetime again and our year to before 2013 for each sheet
    df['Period ending'] = pd.to_datetime(df['Period ending'])
    df = df[(df['Period ending'].dt.year < 2013)]

    # combinations of all 3 threshold together
    for i in Thresholds:
        for k in Thresholds:
            for x in Thresholds:
                # list of returns
                ret = []
                # temporary variable to change and ensure that the return for the next month was added,
                # not the current month
                use = False

                for index, row in df.iterrows():
                    if use == True:
                        # take return for next day from the return column
                        ret.append(row['Unnamed: 23'])
                        use = False
                    # these were the names of the columns for each sheet to access the original thresholds of each fundamental
                    # note: some of these column names have been changed since running the optimizer
                    if row['Normalize'] < x and row['Unnamed: 17'] < k and row['Unnamed: 18'] > i:
                        use = True
                # calculating sharpe: add a zero into the list of returns for every month we are not in so we
                # can accurately calulate the volatility needed to generate the Sharpe Ratio
                # 259 is amount of months from our starting month in 1990 to the end of 2012
                stdevList = [0] *(259-len(ret)) + ret
                # use to find standard deviation
                sd = np.std(stdevList)
                # sharpe calculation
                Sharpe = (math.sqrt(12))*((sum(ret)/259)/sd)
                if Sharpe > best and (len(ret)/259 > .2): #make sure its in for 20% of the time at least
                    print(len(ret)) # display amount of times we are in for
                    best = Sharpe
                    bestROE = i
                    bestPB = k
                    bestPE = x
    # display the best sharpe ratio and thresholds that provided it
    print(best)
    print("PE:",bestPE,"PB:",bestPB,"ROE:",bestROE)
    best = 0
