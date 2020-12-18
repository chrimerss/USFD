
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import geopy
from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="application")

merged= pd.read_csv('USFD_v0.1', index_col='ID')

#====================unify and fill state======================
def fill_country_state(x):
    if (pd.isna(x.COUNTRY)) and (not pd.isna(x.LON)) and (not pd.isna(x.LAT)):
        loc= geolocator.reverse("%f, %f"%(x.LAT, x.LON)).raw
        country= loc['address']['state']
    else:
        country= np.nan
    return country

states= merged.apply(fill_country_state, axis=1)
merged['STATE']= states

#====================unify CAUSE==============================
rains= merged.CAUSE.str.contains('rain',case=False, na=False)
snows= merged.CAUSE.str.contains('snow',case=False, na=False)
dam_break= merged.CAUSE.str.contains('dam|break',case=False, na=False)
dam_release= merged.CAUSE.str.contains('dam|release',case=False, na=False)
storm= merged.CAUSE.str.contains('storm|cyclone',case=False, na=False)
ice= merged.CAUSE.str.contains('ice|jam',case=False, na=False)
merged.loc[:,'CAUSE']= ''
rains_ind= rains[rains].index; snow_ind=snows[snows].index; dam_break_ind= dam_break[dam_break].index;
dam_release_ind= dam_release[dam_release].index; storm_ind= storm[storm].index; ice_ind= ice[ice].index
def append_cause(x):
    global rains_ind, snow_ind, dam_break_ind, dam_release_ind, storm_ind, ice_ind
    ind= x.ID
    cause_labels= ['heavy rain', 'snowmelt', 'dam break', 'dam release', 'Storm', 'ice jam']
    causes= ''
    
    for i, _type in enumerate([rains_ind, snow_ind,
                  dam_break_ind, dam_release_ind,
                  storm_ind, ice_ind]):
        if ind in _type:
            if len(causes)>0:
                causes+= (','+cause_labels[i])
            else:
                causes+= cause_labels[i]
            
    return causes
causes= merged.apply(append_cause, axis=1)
merged.loc[:,'CAUSE']= causes
