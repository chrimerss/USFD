import pandas as pd
import geopandas as gpd
from osgeo import gdal
import ee

ee.Initialize()
df= pd.read_csv('merged_v0.30.csv', index_col='ID')
# read slope data
srtm = ee.Image('CGIAR/SRTM90_V4')
slope = ee.Terrain.slope(srtm)
LULC= ee.Image("COPERNICUS/Landcover/100m/Proba-V-C3/Global/2019").select('discrete_classification')

new_lists=[]
for i in range(len(clean_df)-1):
    if i%5000==0 and i!=0:
        new_lists.append(np.arange(len(clean_df))[i-5000:i])
new_lists.append(np.arange(540000, len(clean_df)))        

def compute_terrain(features, lists):

    slope_collections= {'slope':[],'coords':[]}
    dem_collections= {'dem':[],'coords':[]}
    for i in range(len(lists)):
#         _slice= slice(split_size[i], split_size[i+1])
        _df= features.iloc[lists[i],:]
        points= ee.Geometry.MultiPoint([[_df.iloc[j,3], _df.iloc[j,4]] for j in range(len(_df))])
        return_slopes= slope.sampleRegions(collection=points, scale=90, geometries=True)
        return_dict= return_slopes.getInfo()
        slopes= [feature['properties']['slope'] for feature in return_dict['features']]
        coords= [feature['geometry']['coordinates'] for feature in return_dict['features']]
        slope_collections['slope'].append(slopes)
        slope_collections['coords'].append(coords)
        return_dems= srtm.sampleRegions(collection=points, scale=90, geometries=True)
        return_dict= return_dems.getInfo()
        dems= [feature['properties']['elevation'] for feature in return_dict['features']]
        coords= [feature['geometry']['coordinates'] for feature in return_dict['features']]
        
        dem_collections['dem'].append(dems)
        dem_collections['coords'].append(coords)
        print('%d-%d completed!'%(lists[i][0], lists[i][-1]))
        
    return slope_collections, dem_collections
  
slopes, dems= compute_terrain(clean_df,new_lists)
slope_values= sum(slopes['slope'],[])
slope_coords= sum(slopes['coords'], [])
df['slope']= np.nan
df['dem']= np.nan
for i, [lon, lat] in enumerate(slope_coords):
    inds= df[(abs(df.LON-lon)<1e-3) & (abs(df.LAT-lat)<1e-3)].index
    df.loc[inds,'slope']= slope_values[i]
#     print(df[(abs(df.LON-lon)<1e-3) & (abs(df.LAT-lat)<1e-3)])
dem_values= sum(dems['dem'], [])
dem_coords= sum(dems['coords'],[])
for i, [lon, lat] in enumerate(dem_coords):
    inds= df[(abs(df.LON-lon)<1e-3) & (abs(df.LAT-lat)<1e-3)].index
    df.loc[inds,'dem']= dem_values[i]

#=======================get LULC===========================
def compute_LULC(features, lists):

    LULC_collections= {'LULC':[],'coords':[]}

    for i in range(len(lists)):
#         _slice= slice(split_size[i], split_size[i+1])
        _df= features.iloc[lists[i],:]
        points= ee.Geometry.MultiPoint([[_df.iloc[j,3], _df.iloc[j,4]] for j in range(len(_df))])
        return_lulc= LULC.sampleRegions(collection=points, scale=100, geometries=True)
        return_dict= return_lulc.getInfo()
        lulc= [feature['properties']['discrete_classification'] for feature in return_dict['features']]
        coords= [feature['geometry']['coordinates'] for feature in return_dict['features']]

        
        LULC_collections['LULC'].append(lulc)
        LULC_collections['coords'].append(coords)
        print('%d-%d completed!'%(lists[i][0], lists[i][-1]))
        
    return LULC_collections
new_lists=[]
for i in range(len(clean_df)-1):
    if i%5000==0 and i!=0:
        new_lists.append(np.arange(len(clean_df))[i-5000:i])
new_lists.append(np.arange(180000, len(clean_df)))
lulc= compute_LULC(clean_df,new_lists)
lulc_cat= sum(lulc['LULC'], [])
lulc_coords= sum(lulc['coords'], [])
for i, [lon, lat] in enumerate(lulc_coords):
    inds= df[(abs(df.LON-lon)<1e-3) & (abs(df.LAT-lat)<1e-3)].index
    df.loc[inds,'LULC']= lulc_cat[i]

#================Distance to river and contributing area===================
contributing_area= ee.Image('MERIT/Hydro/v1_0_1').select('upa')
rivers= ee.Image('MERIT/Hydro/v1_0_1').select('wth')
distance = rivers.select('wth').fastDistanceTransform().sqrt().multiply(ee.Image.pixelArea().sqrt()).rename("distance")
def compute_dist(features, lists):

    dist_collections= {'dist':[],'coords':[]}

    for i in range(len(lists)):
#         _slice= slice(split_size[i], split_size[i+1])
        _df= features.iloc[lists[i],:]
        points= ee.Geometry.MultiPoint([[_df.iloc[j,3], _df.iloc[j,4]] for j in range(len(_df))])
        return_dist= distance.sampleRegions(collection=points, scale=100, geometries=True)
        return_dict= return_dist.getInfo()
        dist= [float(feature['properties']['distance']/1000.) for feature in return_dict['features']]
        coords= [feature['geometry']['coordinates'] for feature in return_dict['features']]

        
        dist_collections['dist'].append(dist)
        dist_collections['coords'].append(coords)
        print('%d-%d completed!'%(lists[i][0], lists[i][-1]))
        
    return dist_collections
  
dist= compute_dist(clean_df, new_lists)
dist_values= sum(dist['dist'], [])
dist_coords= sum(dist['coords'], [])

for i, [lon, lat] in enumerate(dist_coords):
    inds= df[(abs(df.LON-lon)<1e-3) & (abs(df.LAT-lat)<1e-3)].index
    df.loc[inds,'DISTANT_RIVER']= dist_values[i]

def buffer(f):
    distance= ee.Number(f.get('distance'))
    f=ee.Algorithms.If(distance, f.buffer(distance.add(30),1),f)
    f= ee.Feature(f)
    return f.set(contributing_area.reduceRegion(ee.Reducer.mean().unweighted(), f.geometry(), 1000))
def compute_fac(features, lists):
    fac_collections= {'FAC':[],'coords':[]}

    for i in range(len(lists)):
#         _slice= slice(split_size[i], split_size[i+1])
        _df= features.iloc[lists[i],:]
        points= ee.Geometry.MultiPoint([[_df.iloc[j,3], _df.iloc[j,4]] for j in range(len(_df))])
        return_dict= distance.reduceRegions(points, ee.Reducer.first().setOutputs(["distance"])).map(buffer)
        return_fac= return_dict.getInfo()
        dist= [float(feature['properties']['distance']/1000.) for feature in return_dict['features']]
        fac= [float(feature['properties']['upa']) for feature in return_dict['features']]
        coords= [feature['geometry']['coordinates'][0][0] for feature in return_dict['features']]
        
        fac_collections['FAR'].append(fac)
        fac_collections['coords'].append(coords)
        print('%d-%d completed!'%(lists[i][0], lists[i][-1]))
        
    return dist_collections
def single_fac(loc):
    try:
        lon,lat= loc
        point= ee.Geometry.Point([lon, lat])
        return_dict=distance.reduceRegions(point, ee.Reducer.first().setOutputs(["distance"])).map(buffer)
        return_fac= return_dict.getInfo()
        fac= return_fac['features'][0]['properties']['upa']

        return fac, lon,lat
    except:
        return np.nan, lon, lat
lons=[]
lats=[]
for lon in clean_df.LON.unique():
    for lat in clean_df[clean_df.LON==lon].LAT.unique():
        lons.append(lon)
        lats.append(lat)
res= []
for i,(lon, lat) in enumerate(zip(lons, lats)):
    print('%d/%d'%(i,len(lons)))
    res.append(single_fac((lon, lat)))
for i, [fac, lon, lat] in enumerate(res):
    inds= df[(abs(df.LON-lon)<1e-4) & (abs(df.LAT-lat)<1e-4)].index
    df.loc[inds,'CONT_AREA']= fac

#================500-yr flood risk===================
risk= ee.Image('users/chrimerss/floodMap_500yr')
def compute_depth(features, lists):
    global risk
    collections= {'depth':[],'coords':[]}

    for i in range(len(lists)):
#         _slice= slice(split_size[i], split_size[i+1])
        _df= features.iloc[lists[i],:]
        points= ee.Geometry.MultiPoint([[_df.iloc[j,3], _df.iloc[j,4]] for j in range(len(_df))])
        return_fea= risk.sampleRegions(collection=points, scale=90, geometries=True)
        return_dict= return_fea.getInfo()
#         print(return_dict)
        fea= [feature['properties']['b1'] for feature in return_dict['features']]
        coords= [feature['geometry']['coordinates'] for feature in return_dict['features']]

        
        collections['depth'].append(fea)
        collections['coords'].append(coords)
        print('%d-%d completed!'%(lists[i][0], lists[i][-1]))
        
    return collections
depth= compute_depth(clean_df, new_lists)
dist_values= sum(depth['depth'], [])
dist_coords= sum(depth['coords'], [])

for i, [lon, lat] in enumerate(dist_coords):
    inds= df[(abs(df.LON-lon)<1e-3) & (abs(df.LAT-lat)<1e-3)].index
    df.loc[inds,'DEPTH']= dist_values[i]

