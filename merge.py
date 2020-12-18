
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

noaa= pd.read_csv('extracted_events_NOAA.csv')
dfo= pd.read_excel('FloodArchive.xlsx')
cyber= pd.read_excel('global_flood_database_complete.xls', sheet_name= 'GFI_1998_2008')
cyber[(cyber==-9999.) | (cyber==-999)]= np.nan
cyber= cyber[(~pd.isna(cyber.Year)) | (~pd.isna(cyber.Month))]

#MAKE A MERGED ONE
merged= pd.DataFrame(columns=['DATE_BEGIN', 'DATE_END', 'DURATION', 'LON', 'LAT','COUNTRY', 'STATE','LOCATION',
                            'AREA', 'FATALITY', 'DAMAGE', 'SEVERITY','SOURCE','CAUSE',
                              'SOURCE_DB', 'SOURCE_ID', 'DESCRIPTION'],
                    index= range(len(noaa)+len(india)+len(dfo)+len(cyber)))

def map_area(x):
    return (max(x.BEGIN_RANGE, x.END_RANGE)*1.6)**2*np.pi
  
#This is for CyberFlood which records codes instead of names  
country_code= pd.read_csv('country_code.csv', header=None)
cause_codes= pd.read_csv('cause_codes.csv', header=None)

def format_date(x):
    try: 
        return (pd.to_datetime(x['Start Date']).strftime('%Y%m%d'), 
                pd.to_datetime(x['End Date']).strftime('%Y%m%d'))
    except:
        begin= x['Start Date'].str.extract(r'/(\d+)/(\d+)')
        end= x['End Date'].str.extract(r'/(\d+)/(\d+)')
        return (pd.to_datetime('%04d%02d'%(begin[1], begin[0]), format='%Y%m').strftime('%Y%m'),
               pd.to_datetime('%04d%02d'%(end[1], end[0]), format='%Y%m').strftime('%Y%m'))

def checking_lon(x):
    try:
        x=float(x)   
        if -180<=float(x)<=180:
            return x
        else:
            return np.nan
    except ValueError:
        return np.nan

def checking_lat(x):
    try:
        x=float(x)
        if -90<=x<=90:
            return x
        else:
            return np.nan
    except ValueError:
        return np.nan

      
#=======================NWS storm reports================
inoaa= len(noaa)
merged['DATE_BEGIN'].iloc[:inoaa]= list(pd.to_datetime(noaa.datetime_begin).dt.strftime('%Y%m%d%H%M'))
merged['DATE_END'].iloc[:inoaa]= list(pd.to_datetime(noaa.datetime_end).dt.strftime('%Y%m%d%H%M'))
merged['DURATION'].iloc[:inoaa]= (pd.to_datetime(noaa.datetime_end) -\
                                  pd.to_datetime(noaa.datetime_begin)).dt.days
merged['LON'].iloc[:inoaa]= noaa.BEGIN_LON.apply(checking_lon)
merged['LAT'].iloc[:inoaa]= noaa.BEGIN_LAT.apply(checking_lat)
merged['COUNTRY'].iloc[:inoaa]= 'USA'
merged['STATE'].iloc[:inoaa]= noaa.STATE.values
merged['CAUSE'].iloc[:inoaa]= noaa.FLOOD_CAUSE.values
merged['AREA'].iloc[:inoaa]= noaa.apply(map_area, axis=1).values
merged['FATALITY'].iloc[:inoaa]= noaa.fatality.values
merged['DAMAGE'].iloc[:inoaa]= noaa.damages.values
merged['SOURCE_DB'].iloc[:inoaa]= 'NOAA Storm report'
merged['SOURCE_ID'].iloc[:inoaa]= noaa.EVENT_ID.values
merged['DESCRIPTION'].iloc[:inoaa]= noaa.EPISODE_NARRATIVE.tolist()
merged['LOCATION'].iloc[:inoaa]= noaa.CZ_NAME.tolist()
merged['SOURCE'].iloc[:inoaa]= noaa.SOURCE.tolist()

# =====================DFO================================
idfo= len(dfo)
merged['DATE_BEGIN'].iloc[inoaa:inoaa+idfo]= list(dfo.Began.dt.strftime('%Y%m%d'))
merged['DATE_END'].iloc[inoaa:inoaa+idfo]= list(dfo.Ended.dt.strftime('%Y%m%d'))
merged['DURATION'].iloc[inoaa:inoaa+idfo]= ((pd.to_datetime(dfo.Ended) -\
                                            pd.to_datetime(dfo.Began)).dt.days).values
merged['LON'].iloc[inoaa:inoaa+idfo]= dfo.long.apply(checking_lon).values
merged['LAT'].iloc[inoaa:inoaa+idfo]= dfo.lat.apply(checking_lat).values
merged['COUNTRY'].iloc[inoaa:inoaa+idfo]= dfo.Country.tolist()
# merged['STATE'].iloc[inoaa:idfo]= dfo.STATE
merged['CAUSE'].iloc[inoaa:inoaa+idfo]= dfo.MainCause.tolist()
merged['AREA'].iloc[inoaa:inoaa+idfo]= dfo.Area.values
merged['FATALITY'].iloc[inoaa:inoaa+idfo]= dfo.Dead.values
merged['SEVERITY'].iloc[inoaa:inoaa+idfo]= dfo.Severity.values
merged['SOURCE_DB'].iloc[inoaa:inoaa+idfo]= 'DFO'
merged['SOURCE_ID'].iloc[inoaa:inoaa+idfo]= dfo.ID.values
merged['SOURCE'].iloc[inoaa:inoaa+idfo]= dfo.Validation.tolist()


# =====================CyberFlood================================

def format_date(x):
    if (not pd.isna(x.Day)) & (not pd.isna(x.Year))& (not pd.isna(x.Month)):
        return pd.to_datetime('%04d%02d%02d'%(x.Year, x.Month, x.Day), format='%Y%m%d').strftime('%Y%m%d')
    elif (pd.isna(x.Day)) & (not pd.isna(x.Year))& (not pd.isna(x.Month)):
        return pd.to_datetime('%04d%02d'%(int(x.Year), int(x.Month)), format='%Y%m').strftime('%Y%m')
    else:
        return np.nan
    
def map_country(x):
    global country_code
    if not pd.isna(x['Country code']):
        code= int(x['Country code'])
        return country_code[country_code.iloc[:,0]==code][1].values[0]
    else:
        return np.nan
def map_causes(x):
    global cause_codes
    code= x['Cause']
    if isinstance(code, int):
        cause= cause_codes[cause_codes.iloc[:,0]==code][1].values[0]
    elif isinstance(code, str):
        codes= code.split(',')
        causes= ''
        for code in codes:
            causes+=(code+',')
        cause=causes
    else:
        cause= np.nan
    return cause

icyber= len(cyber)
merged['DATE_BEGIN'].iloc[idfo+inoaa:icyber+idfo+inoaa]= cyber.apply(format_date, axis=1).tolist()
# merged['DATE_END'].iloc[iind+idfo+inoaa+iind:icyber+iind+idfo+inoaa]= cyber.Ended
merged['DURATION'].iloc[idfo+inoaa:icyber+idfo+inoaa]= cyber['Duration (days)'].tolist()
merged['LON'].iloc[idfo+inoaa:icyber+idfo+inoaa]= cyber.Long.apply(checking_lon).values
merged['LAT'].iloc[idfo+inoaa:icyber+idfo+inoaa]= cyber['Lat '].apply(checking_lon).values
merged['COUNTRY'].iloc[idfo+inoaa:icyber+idfo+inoaa]= cyber.apply(map_country, axis=1).tolist()
# merged['STATE'].iloc[inoaa:idfo]= dfo.STATE
merged['CAUSE'].iloc[idfo+inoaa:icyber+idfo+inoaa]= cyber.apply(map_causes, axis=1).tolist()
# merged['AREA'].iloc[iind+idfo+inoaa+iind:icyber+iind+idfo+inoaa]= cyber.Area
merged['FATALITY'].iloc[idfo+inoaa:icyber+idfo+inoaa]= cyber.fatality.tolist()
merged['SEVERITY'].iloc[idfo+inoaa:icyber+idfo+inoaa]= cyber.Severity.tolist()
merged['SOURCE_DB'].iloc[idfo+inoaa:icyber+idfo+inoaa]= 'CyberFlood'
merged['SOURCE_ID'].iloc[idfo+inoaa:icyber+idfo+inoaa]= cyber.ID.tolist()
merged['SOURCE'].iloc[idfo+inoaa:icyber+idfo+inoaa]= 'WEB CROWDSOURCING'

# ===========================FEDB====================================
base_dir= 'FEDB'
for repo in os.listdir(base_dir):
    fdir= os.path.join(base_dir,repo,repo+'.shp')
    events= gpd.read_file(fdir)
    _slice= slice(len(merged), len(merged)+len(events),1)
    merged.loc[_slice, 'SOURCE_DB']= 'FEDB'
    merged.loc[_slice, 'SOURCE_ID']= events.STCD.to_list()
    merged.loc[_slice, 'DATE_BEGIN']= pd.to_datetime(events.StartTimeF).strftime('%Y%m%d%H%M%S').to_list()
    merged.loc[_slice, 'DATE_END']= pd.to_datetime(events.EndTimeF).strftime('%Y%m%d%H%M%S').to_list()
    merged.loc[_slice, 'DURATION']= (pd.to_datetime(events.EndTimeF)-pd.to_datetime(events.StartTimeF)).days.to_list()
    merged.loc[_slice, 'LON']= [np.array(events.geometry[i].coords)[0] for i in range(len(events))]
    merged.loc[_slice, 'LAT']= [np.array(events.geometry[i].coords)[1] for i in range(len(events))]
    
# ==========================EM-DAT===================================
embat= pd.read_excel('emdat_public_2020_11_01_query_uid-MSWGVQ.xlsx')
embat= embat[embat['Disaster Type']=='Flood']
def format_date_begin(x):
    try:
        year= int(x['Start Year'])
        month= int(x['Start Month'])
        day= int(x['Start Day'])
        if (not pd.isna(year)) and (not pd.isna(month)) and (not pd.isna(day)):
            return pd.to_datetime('%04d%02d%02d'%(year, month, day)).strftime('%Y%m%d')
        elif (not pd.isna(year)) and (not pd.isna(month)) and ( pd.isna(day)):
            return pd.to_datetime('%04d%02d'%(year, month)).strftime('%Y%m')
    except ValueError:
        return np.nan
    
def format_date_end(x):
    try:
        year= int(x['End Year'])
        month= int(x['End Month'])
        day= int(x['End Day'])
        if (not pd.isna(year)) and (not pd.isna(month)) and (not pd.isna(day)):
            return pd.to_datetime('%04d%02d%02d'%(year, month, day)).strftime('%Y%m%d')
        elif (not pd.isna(year)) and (not pd.isna(month)) and ( pd.isna(day)):
            return pd.to_datetime('%04d%02d'%(year, month)).strftime('%Y%m')
    except ValueError:
        return np.nan    
      
iembat= len(embat)
_slice= slice(iind+idfo+inoaa+icyber, icyber+iind+idfo+inoaa+iembat,1)
merged.loc[_slice,'DATE_BEGIN'] = embat.apply(format_date_begin, axis=1).tolist()
merged.loc[_slice,'DATE_END'] = embat.apply(format_date_end, axis=1).tolist()
merged.loc[_slice,'DURATION']= ((pd.to_datetime(_merged.loc[_slice,'DATE_END']) -\
                                pd.to_datetime(_merged.loc[_slice,'DATE_BEGIN'])).dt.days).values
merged.loc[_slice, 'LON']= embat.Longitude.apply(checking_lon).values
merged.loc[_slice, 'LAT']= embat.Latitude.apply(checking_lat).values
merged.loc[_slice, 'COUNTRY']= embat.Country.tolist()
merged.loc[_slice, 'LOCATION']= embat.Location.tolist()
merged.loc[_slice, 'CAUSE']= embat.Origin.tolist()
merged.loc[_slice, 'FATALITY']= embat['Total Deaths'].tolist()
merged.loc[_slice, 'DAMAGE']= embat.iloc[:,-2].values*1000
merged.loc[_slice, 'SOURCE_DB']= 'EM-DAT'
merged.loc[_slice, 'SOURCE_ID']= embat['Dis No'].tolist()

#==============================mPING================================
mping= pd.read_csv('mPing_1030.csv')
_slice= slice(iind+idfo+inoaa+icyber+iembat, icyber+iind+idfo+inoaa+iembat+imping,1)
merged.loc[_slice,'DATE_BEGIN'] = pd.to_datetime(mping.obtime).dt.strftime('%Y%m%d%H%M%S').tolist()
merged.loc[_slice, 'LON']= mping.lon.apply(checking_lon).values
merged.loc[_slice, 'LAT']= mping.lat.apply(checking_lat).values
merged.loc[_slice, 'COUNTRY']= 'USA'
merged.loc[_slice, 'DESCRIPTION']= mping.description.tolist()
merged.loc[_slice, 'SOURCE_DB']= 'mPing'
merged.loc[_slice, 'SOURCE_ID']= mping.id


#export 
merged.to_csv('USFD_v0.1.csv')
