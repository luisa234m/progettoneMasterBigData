import wbgapi as wb
import pandas as pd



#df = pd.read_csv('data/Olympic_Medal_Tally_History.csv')
#years = df['year'].unique()
#print(years)

#countries = df['country'].unique()
#print(countries)
#
"""
dd = wb.source.list()
for item in dd:
    print(item)


print("WDI SERIES")
wdi_series = wb.series.info(db=2)
print(wdi_series)


#print("Population estimates and projections")
wdi_series = wb.series.list(db=2)
for item in wdi_series:
    print(item)

"""

#print("start")
pd = wb.data.DataFrame(
    series=['SP.POP.80UP.MA.5Y', 'SP.POP.GROW'],
    labels=['Population ages 80 and above, male (% of male population)', 'Population growth (annual %)'],
    economy=['USA', 'CAN', 'MEX', 'ITA'],
    time=range(2020, 2025),
    db=2
)
pd.to_csv('data.csv')

time=range(2020, 2025)
print(type(time))


#
relevant_data = [{
    "dbid" : 2,
    "indicators" : {
        'SP.POP.GROW', 'Population growth (annual %)'
    }
}]

countries = ['USA', 'CAN', 'MEX', 'ITA']
time_range = range(2020, 2025)