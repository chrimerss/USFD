
import numpy as np
import pandas as pd
from glob import glob
import os

fnames= glob('noaa storm/*.csv')
details_fn= sorted([fn for fn in fnames if 'details' in fn])

timezone_mapper= {
    'CST'   : 'US/Central',
    'CST-6' : 'US/Central',
    'EST'   : 'US/Eastern',
    'EST-5' : 'US/Eastern',
    'PST'   : 'US/Pacific',
    'PST-8' : 'US/Pacific',
    'MST'   : 'US/Mountain',
    'MST-7' : 'US/Mountain',
    'AST'   : 'Etc/GMT-4',
    'AST-4' : 'Etc/GMT-4',
    'HST'   : 'US/Hawaii',
    'HST-10': 'US/Hawaii',
    'GST10' : 'Etc/GMT-4',
    'SST'   : 'US/Samoa',
    'SST-11': 'US/Samoa',
    'AKST-9': 'US/Alaska'
}
def retrieve_floods(fn):
    ''''''
    df= pd.read_csv(fn)
    df= df[df['EVENT_TYPE'].str.contains(pat='Lakeshore Flood|Flood|Flash Flood|Coastal Flood')]
    return df

# convert begin time and end time to UTC
def convert_datetime_begin(x):
    if x.CZ_TIMEZONE in timezone_mapper.keys():
        timezone= timezone_mapper[x.CZ_TIMEZONE]
    else:
        timezone= x.CZ_TIMEZONE
    datetime= '%06d'%(x.BEGIN_YEARMONTH)+'%02d'%(x.BEGIN_DAY)+'%04d'%(x.BEGIN_TIME)
    datetime= pd.to_datetime(datetime, format='%Y%m%d%H%M').tz_localize('%s'%timezone, ambiguous='NaT', nonexistent='NaT').tz_convert('UTC').tz_localize(None)
#     except:
# #         print(str(x.BEGIN_YEARMONTH)+str(x.BEGIN_DAY)+'%04d'%(x.BEGIN_TIME))
#         datetime= pd.to_datetime(datetime, format='%Y%m%d%H%M')
        
    return datetime

def convert_datetime_end(x):
    if x.CZ_TIMEZONE in timezone_mapper.keys():
        timezone= timezone_mapper[x.CZ_TIMEZONE]
    else:
        timezone= x.CZ_TIMEZONE

    datetime= '%06d'%(x.END_YEARMONTH)+'%02d'%(x.END_DAY)+'%04d'%(x.END_TIME)
    datetime= pd.to_datetime(datetime, format='%Y%m%d%H%M').tz_localize('%s'%timezone, ambiguous='NaT', nonexistent='NaT').tz_convert('UTC').tz_localize(None)


        
    return datetime
    
    
floods= pd.DataFrame(columns= df.columns)
for i in range(len(details_fn)):
    _df= retrieve_floods(details_fn[i])
    floods= pd.concat([floods, _df])
begin_time= floods.apply(convert_datetime_begin,axis=1)
end_time= floods.apply(convert_datetime_end,axis=1)
floods['datetime_begin']= begin_time
floods['datetime_end']= end_time

def update_fatality(df, df_fatality):
    df['fatality']= 0

    for ID in df_fatality.EVENT_ID:
        if ID in list(df.EVENT_ID):
            df.loc[df.EVENT_ID==ID, 'fatality']+=1

            
    return df
fatalities_fn= sorted([fn for fn in fnames if 'fatalities' in fn])
df= pd.read_csv(fatalities_fn[0])
fatalities= pd.DataFrame(columns= df.columns)
for i in range(len(fatalities_fn)):
    _df= pd.read_csv(fatalities_fn[i])
    fatalities= pd.concat([fatalities, _df])
    
floods= update_fatality(floods, fatalities)
def justify(x):

    if isinstance(x, str):
        if x[-1]=='K': 
            if x[0]=='K':
                y=1
            else:
                y= float(x[:-1])*1000
        elif x[-1]=='M':
            if x[0]=='M':
                y= 1000000
            else:
                y= float(x[:-1])*1000000
        elif x[-1]=='B': 
            if x[0]=='B':
                y=1e9
            else:
                y= float(x[:-1])*10**9
        elif x[-1]=='0': y= 0
    else: y= 0

    return y

floods['damages']= floods.DAMAGE_PROPERTY.apply(justify) + floods.DAMAGE_CROPS.apply(justify)

# geocode NWS report to fill nan geophysical coordinates with natural language processing
import spacy
from spacy import displacy
from collections import Counter
import en_core_web_sm
nlp = en_core_web_sm.load()

from geopy import Nominatim
locator = Nominatim(user_agent= "myGeocoder")
def insert_location(x):
    try:
    
        if (pd.isna(x.LON) or pd.isna(x.LAT)) and not pd.isna(x.DESCRIPTION):
            text= x.DESCRIPTION
            if isinstance(text, str):
                doc= nlp(text)
                for X in doc.ents:
#                     print(X.label)
                    if X.label_ == 'GPE' or X.label_ == 'ORG':
                        loc= "%s, %s"%(X.text, x.STATE)
                        location= locator.geocode(loc)
                        print(loc)
                        if location:
                            x.loc['LON']= location.longitude
                            x.loc['LAT']= location.latitude
                            print(location.longitude, location.latitude)
    except:
        pass

    
    return x
  
merge= merge.apply(insert_location, axis=1)
