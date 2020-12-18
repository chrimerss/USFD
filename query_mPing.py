
import requests
import json

# Set up our request headers indicating we want json returned and include
# our API Key for authorization.
# Make sure to include the word 'Token'. ie 'Token yourreallylongapikeyhere'
reqheaders = {
    'content-type':'application/json',
    'Authorization': 'Token 1271d3d567f3526dbb2ab27ad7c78da0efdab2d5'
    }

reqparams = {
    'category':'Flood'
}

url = 'http://mping.ou.edu/mping/api/v2/reports'
response = requests.get(url, headers=reqheaders, params=reqparams,)

data = response.json()

with open('mPing_1030.txt', 'w') as outfile:
    json.dump(data['results'], outfile)
    
import pandas as pd
df= pd.read_json('mPing_1030.txt')
def convert_lonlat(x):
    geo= x.geom
    x.loc['lon']= geo['coordinates'][0]
    x.loc['lat']= geo['coordinates'][1]
    
    return x
df= df.apply(convert_lonlat, axis=1)
df.drop('geom', axis=1, inplace=True)
df.to_csv('mPing_1030.csv')
