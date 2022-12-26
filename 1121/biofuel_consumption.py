#!/usr/bin/env python
"""
Author: Jonathan Mann
Question: What percentage of the U.S.’s renewable energy consumption will come from biofuels in 2023?
Link: https://www.infer-pub.com/questions/1121
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from datetime import timedelta
import random

DATA_URL = 'https://www.eia.gov/totalenergy/data/browser/csv.php?tbl=T10.01'
BIOFUEL_DATA_START = 1981
RELEVANT_START = 1981 # Maybe this should be 2007?
ANNUALIZED_MONTH = 13
DAYS_IN_MONTH = 30.5
EXPIRATION = '2024-01'
TRIALS = 100000

sample = lambda data: random.sample(data,1)[0] # Pull a random sample from a set

def get_shifts(df, col):
    df[col + "_prev"] = df[col].shift()
    df.dropna(inplace=True)
    shifts = set((df[col]/df[col + "_prev"]).apply(lambda x: x - 1)) # Make a set of historical price shifts
    return shifts

def random_flip(move,cx=1):
    chance_array = [-1] + [1]*cx
    if move == 0 or 1 == chance_array[random.randrange(cx + 1)]: # 1 / (cx + 1) chance of flipping the sign
        return move
    return (1 / (1 + move) - 1)

def correlated_flip(move,market_move,prob):
    if random.random() < prob:
        if move * market_move > 0:
            return move
        return (1 / (1 + move) - 1)
    if move * market_move > 0:
        return (1 / (1 + move) - 1)
    return move

# Get datetime from EXPRIATION
expiration = datetime.strptime(EXPIRATION, '%Y-%m')

history = pd.read_csv(DATA_URL)
history = history[["YYYYMM", "Value","Description"]]
history["YYYY"] = history["YYYYMM"].apply(lambda x: str(x)[:-2]) #.apply(int)
history["MM"] = history["YYYYMM"].apply(lambda x: str(x)[-2:])#.apply(int)
history["YYYYMM"] = history.YYYY + '-' + history["MM"]
history["YYYY"] = history["YYYY"].apply(int)
history["MM"] = history["MM"].apply(int)
history = history[history["MM"] != ANNUALIZED_MONTH] # remove annual data
history = history[history["YYYY"] >= BIOFUEL_DATA_START] # remove years before biofuel tracking
history = history[history["YYYY"] >= RELEVANT_START] # remove years before forecaster-determined relevant start
history["YYYYMM"] = pd.to_datetime(history["YYYYMM"])
latest_month = history['YYYYMM'].max()
remaining_months = int((expiration - latest_month).days // DAYS_IN_MONTH)

# removes all rows that where the value field is "Not Available"
history = history[history["Value"] != "Not Available"]

# removes all rows that are not relevant to the question
history = history[history["Description"].isin(["Biofuels Consumption", "Total Renewable Energy Consumption"])]

# converts the value field to a float
history["Value"] = history["Value"].apply(float)

# separate out the biofuel and total renewable energy consumption data frames
biofuels = history[history["Description"] == "Biofuels Consumption"]
total_renewable = history[history["Description"] == "Total Renewable Energy Consumption"]

# renames the value column to Biofuels Consumption
biofuels = biofuels.rename(columns={"Value": "Biofuels Consumption"})
del biofuels["Description"]
del biofuels["YYYY"]
del biofuels["MM"]

# renames the value column to Total Renewable Energy Consumption
total_renewable = total_renewable.rename(columns={"Value": "Total Renewable Energy Consumption"})
del total_renewable["Description"]

# joins biofuel and total renewable consumption on YYYYMM
history = biofuels.merge(total_renewable, on='YYYYMM')


# calculates the non-biofuels consumption
history["Non-Biofuels Consumption"] = history["Total Renewable Energy Consumption"] - history["Biofuels Consumption"]

# aggregates the data by year
history = history.groupby("YYYY").sum()

# YYYY back to column
history = history.reset_index()

# calculates the percentage of biofuel consumption relative to total renewable energy consumption
history["Biofuels Consumption Percent"] = history["Biofuels Consumption"] / history["Total Renewable Energy Consumption"]

# gets the shifts in biofuel consumption
biofuel_percentage_shifts = get_shifts(history, "Biofuels Consumption Percent")

outcomes = []
for i in range(TRIALS):
    biofuel_percentage = history["Biofuels Consumption Percent"].iloc[-1]
    biofuel_percentage *= (1 + sample(biofuel_percentage_shifts))
    outcomes.append(biofuel_percentage)

outcomes = pd.DataFrame(outcomes, columns=[ "Biofuels Consumption Percent"])
biofuel_quantile = lambda x: outcomes["Biofuels Consumption Percent"].quantile(x)
biofuel_percentage = history["Biofuels Consumption Percent"].iloc[-1]

print('5th: ',biofuel_quantile(.05))
print('10th: ',biofuel_quantile(.1))
print('25th: ',biofuel_quantile(.25))
print('40th: ',biofuel_quantile(.4))
print('50th: ',biofuel_quantile(.5))
print('60th: ',biofuel_quantile(.6))
print('75th: ',biofuel_quantile(.75))
print('90th: ',biofuel_quantile(.9))
print('95th: ',biofuel_quantile(.95))

# create area chart of biofuel consumption relative to total renewable energy consumption
sns.set_theme()
plt.stackplot(history["YYYY"], history["Biofuels Consumption Percent"], labels=["% Biofuels"])
plt.show()
