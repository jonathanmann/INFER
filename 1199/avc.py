#!/usr/bin/env python

# Collects data from this web page: https://www.dmv.ca.gov/portal/vehicle-industry-services/autonomous-vehicles/autonomous-vehicle-collision-reports/
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import requests
from bs4 import BeautifulSoup
import csv
import random

URL = 'https://www.dmv.ca.gov/portal/vehicle-industry-services/autonomous-vehicles/autonomous-vehicle-collision-reports/'
TRIALS = 1000

# Get the page
page = requests.get(URL)
soup = BeautifulSoup(page.content, 'html.parser')

# Get the table
divs = soup.find_all('div', attrs={'class':'accordion-block__content'})

# Get the rows
records = []
for div in divs:
    rows = div.find_all('li')
    for r in rows:
        records.append(r.text)

months = ['January','February','March','April','May','June','July','August','September','October','November','December']
month_nums = ['01','02','03','04','05','06','07','08','09','10','11','12']

mdict = dict(zip(months, month_nums))

# make a list of the strings of years from 2014 to 2023
years = [str(i) for i in range(2014,2024)]

data = [['Month','Year','Literal']]

for r in records:
    try:
        t_month = ''
        t_year = ''
        for m in months:
            if m in r:
                t_month = m
                break
                
        for y in years:
            if y in r:
                t_year = y
                break
        data.append([t_month,t_year,r])
    except:
        print("ERROR: ", r)

df = pd.DataFrame(data[1:], columns=data[0])

# Get rid of accidental duplicates
df.drop_duplicates(inplace=True)

df['Month'] = df['Month'].apply(lambda x: mdict[x])
#df.to_csv('avc.csv', index=False)
# remove all years from the summary data frame that are not 2019 - 2023
df = df[df['Year'].isin(years[-5:])]

# get a count by year and month from the data frame
summary = df.groupby(['Year','Month']).count()
#summary.to_csv('avc_summary.csv')

# rename literal to count
summary.rename(columns={'Literal':'Count'}, inplace=True)


# grab a sample count value from the summary
def sample_historical_count():
    # get the number of rows in the summary
    n = summary.shape[0]
    # get a random row
    return summary.iloc[random.randint(0,n-1)]['Count']

collection = []
for i in range(TRIALS):
    c = 3 + sample_historical_count() + sample_historical_count()
    collection.append(c)

# convert collection to a data frame
df = pd.DataFrame(collection, columns=['Count'])

print(df.quantile([0.1,.25,.5,.75,0.9,0.95,0.99]))

summary.reset_index(inplace=True)

#summary['YYYY-MM'] = summary['Year'].apply(lambda x:x[-2:]) + '-' + summary['Month']
summary['YYYY-MM'] = summary['Year'] + '-' + summary['Month']

sns.set_theme()
plt.stackplot(summary["YYYY-MM"], summary["Count"], labels=["Monthly Collisions"])
# adjust plt to show ticks only every 5 months
plt.xticks(summary["YYYY-MM"][::5], rotation=45)
plt.show()



