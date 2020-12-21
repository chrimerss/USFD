
import geopandas as gpd
import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt

import sys
#preload plot configuration
# sys.path.append('/Users/allen/Documents/Python/PlotGallary')

# from matplotlibconfig import basic

# basic()

df= pd.read_csv('USFD_v1.0.csv', index_col='ID')
states= gpd.read_file('US_floods_states')
gdf = gpd.GeoDataFrame(
    df, geometry=gpd.points_from_xy(df.LON, df.LAT))
def fillStates(state):
    masks= unique_geometry.within(state.geometry)
    print('done %s'%state[0])
    
    return masks, state[0]

# fill state names
results= states.apply(fillStates, axis=1)
for i in range(len(results)):
    (masks, state_name)= results.values[i]
    for j,geometry in enumerate(unique_geometry[masks]):
        print('[%d/%d] [%d/%d]'%(i,len(results),j,len(unique_geometry[masks])))
        if len(geometry.coords)>=1:
            lon,lat=list(geometry.coords)[0]
#             ids= gdf[(gdf.geometry==geometry)].index.values
#             print(ids)
            df.loc[(abs(gdf.LON-lon)<1e-5) & (abs(gdf.LAT-lat)<1e-5),'STATE']= state_name
  
df.STATE= df.STATE.str.upper()
def countOccr(state):
    return len(df[df.STATE==state[0].upper()])

def countbyDB(state):
    print(state.name)
#     print(df[df.STATE==state[0].upper()]['SOURCE_DB'].unique())
    return df[df.STATE==state[0].upper()]['SOURCE_DB'].value_counts()

results= states.apply(countbyDB, axis=1)

from matplotlib import cm
from matplotlib.colors import ListedColormap
from mpl_toolkits.axes_grid1 import make_axes_locatable
colors = ("#8E063B","#B9534C","#DA8459","#EEAB65","#F6C971","#F1DE81","#E2E6BD")[::-1]
events_cmap= ListedColormap(colors)

#==================Figure 1=================
fig=plt.figure(figsize=(12,6))

ax=fig.add_subplot(111)
divider = make_axes_locatable(ax)
cax = divider.append_axes("bottom", size="5%", pad=0.5)
states.iloc[3:].plot(column='events',ax=ax,cmap=events_cmap,legend=True,edgecolor='k',cax=cax,
                               legend_kwds={'label': "number of events",
                                'orientation': "horizontal",
#                                "ticks": np.linspace(0,42448,8),
                                "ticks":[0,6800,12800,18700,24600,30500,36500,42448],
                               "extend": 'both'})
# cax.set_xticks(np.linspace(1,5,7))
# cax.set_xticklabels(['$10^%d$'%i for i in np.linspace(1,6,7)]);
ax.set_xlim([-130,-65])
ax.set_ylim([23,52])
ax.set_title('(a)', loc='left',weight='bold')
ax.axis('off');
# fig.savefig('src/Figure1a.png',dpi=300)
states= states.iloc[5:,:]
states= states.drop(['HAWAII','ALASKA'],axis=0)
fig=plt.figure(figsize=(12,8))
ax=fig.add_subplot(111)
pd.DataFrame(states).sort_values(by='events').loc[:,results.columns].plot(kind='barh',stacked=True,ax=ax,edgecolor='k')
ax.set_yticklabels(states.sort_values(by='events').code, fontsize=13, weight='bold')
ax.set_ylabel('')
ax.set_title('(b)', weight='bold',loc='left');
# fig.savefig('src/Figure1b.png',dpi=300)

#==================Figure 2===================
import ee
from shapely.geometry import shape, MultiPoint, Point
ee.Initialize()
watersheds= ee.FeatureCollection('USGS/WBD/2017/HUC04').getInfo()['features']
geom = [shape(watershed['geometry']) for watershed in watersheds]
geo_watersheds= gpd.GeoDataFrame({'geometry':geom})

# assign geopandas attributes
for i,watershed in enumerate(watersheds):
#     print(shape(watershed['geometry']))
#     geo_watersheds.loc[i, 'geometry']=shape(watershed['geometry'])
    geo_watersheds.loc[i, 'ID']= watershed['properties']['huc2']
    geo_watersheds.loc[i, 'name']= watershed['properties']['name']
    geo_watersheds.loc[i, 'area']= watershed['properties']['areasqkm']
    geo_watersheds.loc[i, 'km_area']= watershed['properties']['shape_area']
    geo_watersheds.loc[i, 'length']= watershed['properties']['shape_leng']

def groupBySeason(watershed):
    try:
        masks= gdf.geometry.within(watershed.geometry)
#     gdf.loc[masks, 'Basin']= watershed.HYBAS_ID
    
        return gdf.loc[masks].index, watershed.ID
    except ValueError:
        return np.nan, np.nan
results= geo_watersheds.apply(groupBySeason,axis=1)
df['WATERSHED_ID']= np.nan
for ids, watershed_id in results:
    df.loc[ids, 'WATERSHED_ID']= watershed_id
# df.to_csv('USFD_v1.0_HUC4.csv')
#format database date
def format_date(x):
    if not pd.isna(x.DATE_BEGIN):
        if isinstance(x.DATE_BEGIN, int):
            date= str(x.DATE_BEGIN)
        elif isinstance(x.DATE_BEGIN, float):
            date= str(int(x.DATE_BEGIN))
        else:
            date= x.DATE_BEGIN
        if len(date)==4:
            return pd.to_datetime(date, format='%Y')
        elif len(date)==6:
            return pd.to_datetime(date, format='%Y%m')
        elif len(date)==8:
            return pd.to_datetime(date, format='%Y%m%d')
        elif len(date)==10:
            return pd.to_datetime(date, format='%Y%m%d%H')
        elif len(date)==12:
            return pd.to_datetime(date, format='%Y%m%d%H%M')
        elif len(date)==14:
            return pd.to_datetime(date, format='%Y%m%d%H%M%S')
        else:
            return np.nan
    else:
        return np.nan
    
dates= df.apply(format_date, axis=1)

for mon in range(1,13):
#     geo_watersheds_4['%02d'%mon]= 0
    for i in range(len(geo_watersheds_4)):
        geo_watersheds_4.loc[i,'%02d'%mon]= len(df[(df.WATERSHED_ID.astype(str)==geo_watersheds_4.loc[i,'ID'])&\
                                                 (dates.dt.month==mon)])
      
def mapMostMonths(x):
  '''Get month with most events'''
    cases= np.array([x['%02d'%m] for m in range(1,13)])
    if (cases==0).all():
        return np.nan
    else:
        return np.argmax(cases)+1
        

geo_watersheds_4['most_cases_by_month']= geo_watersheds_4.apply(mapMostMonths,axis=1)
#("#002F70","#517AC9","#B4C2EB","#F6F6F6","#EDB4B5","#C05D5D","#5F1415")
colors= ["#517AC9","#B4C2EB","#ABDFAC","#42A644","#005600","#EDB4B5","#C05D5D","#A2223C",
        "#F2EBAC","#DED471","#BAAE00","#002F70"]
seasons_cmap= ListedColormap(colors)
fig= plt.figure(figsize=(12,8))
ax= fig.add_subplot(111)
# divider = make_axes_locatable(ax)
# cax = divider.append_axes("bottom", size="5%", pad=0.5)

geo_watersheds_4.plot(column='most_cases_by_month', cmap=seasons_cmap,ax=ax, legend=False,edgecolor='black',
           legend_kwds={'label': "Month",
                        'orientation': "horizontal",
                       "ticks": [1.2,2.3,3.3,4.2,5.1,6,7,7.9,8.8,9.8,10.6,11.8],
                       "extend": 'both'})
geo_watersheds.plot(color='none',edgecolor='white', ax=ax, linewidth=2)
# geo_watersheds.apply(lambda x: ax.annotate(s=x[2].replace('Region', ''),
#                     xy=x.geometry.centroid.coords[0], ha='center', color='white', fontsize=8),axis=1);
# geo_watersheds.plot(alpha=0,edgecolor='k', ax=ax)
# cax.set_xticks([1,2.2,3.2,4.1,5.1,6,7,7.9,8.8,9.8,10.6,12])
# cax.set_xticklabels(['%02d'%i for i in range(1,13)]);
ax.set_xlim([-130,-65])
ax.set_ylim([23,52])
ax.axis('off')
ax.set_title('(a)', weight='bold', loc='left')
legend_ax= fig.add_axes([0.1,0.06,0.2,0.2])
legend_ax.pie([0.083333333]*12, colors=colors, labels=np.arange(1,13),startangle=110,counterclock=False, radius=0.6,
      wedgeprops=dict(width=0.3, edgecolor='w'));
legend_ax.pie([0.25]*4, radius=1,wedgeprops=dict(width=0.4, edgecolor='w'),startangle=140,counterclock=False,
      colors=["#517AC9","#42A644","#C05D5D","#DED471"], labels=['Winter','Spring','Summer','Autumn']);                 

fig.savefig('src/Figure2a.png',dpi=300)

geo_watersheds['events']= geo_watersheds.iloc[:,6:18].sum(axis=1)
fig= plt.figure(figsize=(12,6))
ax=fig.add_subplot(111)
pd.DataFrame(geo_watersheds).sort_values(by='events', ascending=False).iloc[:20,[17,6,7,8,9,10,11,12,13,14,
                                                                                15,16]].plot(kind='barh',
                                                                            stacked=True,color=np.array(colors)[[-1,
                                                                                        0,1,2,
                                                                                    3,4,5,6,7,8,9,10]],
                                                                                           legend=False,
                                                                                          edgecolor='k',
                                                                                          ax=ax)
# ax=plt.gca()
# yticks= ax.get_yticks()
ax.set_yticklabels(geo_watersheds.sort_values(by='events', ascending=False)[:20].ID.astype(str), rotation=20)
ax.set_title('(b)', loc='left',weight='bold')
ax.invert_yaxis();
# ax.set_xscale('log')
fig.savefig('src/Figure2b.png',dpi=300)

#======================Figure 3====================
gdp= pd.read_csv('GDP_deflactor.csv')
gdp.DATE=pd.to_datetime(gdp.DATE)
gdp.set_index('DATE',inplace=True)
gdp['year']= gdp.index.year
gdp= gdp.groupby('year').mean()
def adjust_damage(feature):
  '''Deflact damage'''
    if not pd.isna(feature.DAMAGE) and not np.isnan(feature.DAMAGE) and not np.isnan(feature.year):
        year=int(feature.year)
        if year<1947:
#             print('country name or year not satisfying')
            return np.nan

        else:
            factor= gdp.loc[year,'GDP']/gdp.loc[2020,'GDP']
            if factor==0:
#                 print('factor 0!!!')
                return np.nan
            else:
#                 print(feature.DAMAGE, factor)
                return feature.DAMAGE/(factor)
    else:
#         print('not satisfying')
        return np.nan

df['adjusted_damage']= df.apply(adjust_damage, axis=1)
fig= plt.figure(figsize=(10,8))
ax= fig.add_subplot(211)
ax.set_yscale('log')
fatalities= df[(~pd.isna(df.FATALITY)) & (~pd.isna(df.year))].groupby('year')['FATALITY'].mean()
ax.bar(fatalities.index, fatalities.values, alpha=0.5, edgecolor='k', label='mean fatalities',color='k')
df_fat= pd.DataFrame(index=dates)
df_fat['fatalities']= df.FATALITY.values
average= df_fat.resample('10Y').mean()
ax.plot(average.index.year, average.values, linestyle='dashed', linewidth=2, label='10-yr average',color='k')
ax.legend()
ax.set_title('(a)', loc='left', pad=1,weight='bold')
ax.set_ylabel('Fatality (person)')
marked_years= [2011,2012,2016,2017]
ax.bar(marked_years, fatalities[marked_years], color='r')


ax= fig.add_subplot(212)
ax.set_yscale('log')
fatalities= df[(~pd.isna(df.adjusted_damage)) & (~pd.isna(df.year)) & (df.adjusted_damage>0)].groupby('year').mean()['adjusted_damage']
ax.bar(fatalities.index, fatalities.values, alpha=0.5, edgecolor='k', label='mean damages',color='k')
df_fat= pd.DataFrame(index=dates)
df_fat['loss']= df.adjusted_damage.values
average= df_fat.resample('10Y').mean()
ax.plot(average.index.year, average.values, linestyle='dashed', linewidth=2, label='10-yr average',color='k')
ax.legend()
ax.set_title('(b)', loc='left', pad=1,weight='bold')
ax.set_ylabel('Economic damage (US dollors)')
ax.set_xlim([1947, None])
ax.bar(marked_years, fatalities[marked_years], color='r');
# ax.set_xticks(np.arange(0,121,5))
# ax.set_xticks(np.arange(0,121,5))
# ax.set_xticklabels(np.arange(1900,2021,5).astype(int));
fig.savefig('src/Figure3.png',dpi=300)


#======================Figure 4=================
#("#002F70","#517AC9","#B4C2EB","#F6F6F6","#EDB4B5","#C05D5D","#5F1415")
colors= ("#001889","#72008D","#AB1488","#D24E71","#E8853A","#ECC000","#DAFF47")[::-1]
cmap= ListedColormap(colors)
fig= plt.figure(figsize=(12,12))
ax= fig.add_subplot(211)
divider = make_axes_locatable(ax)
cax = divider.append_axes("bottom", size="5%", pad=0.5)
view= states.plot(column='losses',ax=ax, cmap=cmap, legend=True, cax=cax, edgecolor='black',
           legend_kwds={'label': "Economic losses per event (million US dollors)",
                        'orientation': "horizontal",
                       "ticks": [0,1.6,3.2,4.75,6.35,7.95,9.5,11],
                       "extend": 'both'},
                        )

# cax.set_xticks(np.arange(1,8))
ax.set_xlim([-130,-65])
ax.set_ylim([23,52])
ax.axis('off');     

ax= fig.add_subplot(212)
pd.DataFrame(states).sort_values(by='losses',ascending=False)['losses'].iloc[:20].plot(kind='barh',
    color=cmap((states.losses/states.losses.max()).sort_values(ascending=False)),
                                            edgecolor='k',ax=ax)
ax.set_ylabel('')
ax.set_yticklabels(states.sort_values(by='losses',ascending=False)['code'].iloc[:20])
for i in range(20):
    ax.text(states.sort_values(by='losses',ascending=False).iloc[:20].losses[i]+0.1, i-0.15,
            states.sort_values(by='losses',ascending=False)['counts'].iloc[:20][i]);
# fig.savefig('src/Figure4.png',dpi=300)
