# -*- coding: utf-8 -*-
"""
Created on Tue Mar 23 10:34:53 2021

@author: lizca
"""
import ee
import pandas as pd
import xlsxwriter
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.getcwd()),'bin'))
import datetime
from functions import CloudScore6S,landMaskFunction,div
import geemap
from IPython.display import display, Image

ee.Initialize()
print('EE API version: ',ee.__version__)


## Some settings and metadata:

#imageID = 'LT05_016041_19890205'
imageID = '20190208T160421_20190208T161051_T17RLL'
#boaFolder = 'FL_90'
exportFolder = 'FL_seasonality'
dataFolder = 'Ground-points-19'
#dataFolder = 'Ground-points-00'
#dataFolder = 'Ground-points-90'
smoothStr = '_raw_' #Smooth or not? '_smooth_' or '_raw_'


## Image Collection
#collection = ee.ImageCollection("users/lizcanosandoval/BOA/Sentinel/"+boaFolder)
#collection = ee.ImageCollection("users/lizcanosandoval/BOA/Landsat/"+boaFolder)

## Filter collection by image ID:
# imageTarget = collection.filter(ee.Filter.eq('file_id',imageID)).first()
imageTarget = ee.Image('COPERNICUS/S2_SR/'+imageID)
imageTarget = imageTarget.divide(10000).set(imageTarget.toDictionary(imageTarget.propertyNames()))
imageSat = imageTarget.get('SPACECRAFT_NAME').getInfo()
imageTile = imageTarget.get('MGRS_TILE').getInfo()
ee_date = imageTarget.get('GENERATION_TIME').getInfo()
imageDate = str(datetime.datetime.utcfromtimestamp(ee_date/1000.0))

## more settings and metadata
imageGeometry = imageTarget.geometry() #Tile geometry.
# imageSat = imageTarget.get('satellite').getInfo() #Image satellite
# imageTile = imageTarget.get('tile_id').getInfo() #Image tile id
# imageDate = imageTarget.get('date').getInfo() #Image date
if 'Sentinel' in imageSat:
    imageScale = 10 # Sentinel resolution
else:
    imageScale = 30 # Landsat resolution

print('Satellite: ',imageSat)
print('Tile: ',imageTile)
print('Date: ',imageDate)
print(imageDate[0:4])



# Sandy areas
sand_areas = ee.FeatureCollection("users/lizcanosandoval/ground-points/Sand")

# Ground-Points
#groundPoints = ee.FeatureCollection("users/lizcanosandoval/ground-points/Turkey_2020")
groundPoints = ee.FeatureCollection("users/lizcanosandoval/ground-points/"+dataFolder)
#groundPoints = ee.FeatureCollection("users/lizcanosandoval/ground-points/Ground-points-00")
#groundPoints = ee.FeatureCollection("users/lizcanosandoval/ground-points/Ground-points-90")

gadm_FL = ee.FeatureCollection("users/lizcanosandoval/Florida_10m")##Created from NDWI using Sentinel-2 imagery


## Recommended Threshold values for
## *Sentinel: 2
## *Landsat: 5
if 'Sentinel' in imageSat:
    threshold = 5
else:
    threshold = 5

## Apply cloud mask
cloudMask = CloudScore6S(imageSat, imageTarget, threshold)


## Apply land mask
landMask = landMaskFunction(cloudMask, gadm_FL)

## Apply bathymetry mask
bathyMask = landMask##.clip(bathyVector) ##Using the NOAA dataset: bathyVector



## Turbidity masking is based on the red band reflectances. Based on own observations, values higher than 0.02-0.03 indicates
## turbid waters, but sometimes may indicate shallow seagrass banks. So the below algorithm try to separate shallow seagrass
## from turbidity.

## Set parameter values
if 'Sentinel' in imageSat:
    red_band = 'B4' #Red seems work better in this case than B5.
    red_thr_inf = 0.025
    red_thr_sup = 0.2
    green_band = 'B3'
    green_thr = 0.15
    blue_band = 'B2'
    blue_thr = 0.11
elif 'Landsat8' in imageSat:
    red_band = 'B4'
    red_thr_inf = 0.025
    red_thr_sup = 0.2
    green_band = 'B3'
    green_thr = 0.15
    blue_band = 'B2'
    blue_thr = 0.11
else:
    red_band = 'B3'
    red_thr_inf = 0.03 #Landsat5/7 are less sensitive
    red_thr_sup = 0.2
    green_band = 'B2'
    green_thr = 0.15
    blue_band = 'B1'
    blue_thr = 0.11

## Select the red band
selectRedBand = bathyMask.select('B4')

## Identify turbid areas first (pixel values higher than the threshold)
turbidMask = selectRedBand.gt(red_thr_inf)

## Apply thresholds on red, green and blue bands
maskRed = selectRedBand.gt(red_thr_inf).And(selectRedBand.lt(red_thr_sup))
imageMaskRed = bathyMask.mask(maskRed)
maskGreen = imageMaskRed.select(green_band).lt(green_thr)
imageMaskGreen = imageMaskRed.mask(maskGreen)
maskBlue = imageMaskGreen.select(blue_band).lt(blue_thr) ##Shallow seagrass

## Final mask (excluding seagrass/including turbid water)
turbidImage = bathyMask.mask(turbidMask) ## Turbidity
seagrassImage = bathyMask.mask(maskBlue).mask().Not() ## Shallow seagrass (inverse mask)
excludeSeagrass = turbidImage.updateMask(seagrassImage) ## Turbidity minus shallow seagrass
finalMaskImage = bathyMask.mask(excludeSeagrass)
finalMask = finalMaskImage.mask().Not()

## Final Image
finalImage = bathyMask.updateMask(finalMask)



## Filter sand polygons by tile/area:
sand = ee.FeatureCollection(sand_areas).filterBounds(imageGeometry)
print('Number of sand polygons: ',sand.size().getInfo())

## Run the Depth-Invariant Index Function
imageDIV = div(finalImage, imageScale, sand)
#print(imageDIV.getInfo())


## Filter ground points by tile geometry and display classes
filterPoints = ee.FeatureCollection(groundPoints).filterBounds(imageGeometry)
print('Classes: ', filterPoints.aggregate_array('class').distinct().getInfo())
print('Ground Points per Class:', filterPoints.aggregate_histogram('class').getInfo())

totalPoints = filterPoints.size()
print('Total points:', totalPoints.getInfo())



## Select bands to sample. The B/G band is B2B3 in Sentinel-2 and Landsat-8, and B1B2 for Landsat-7/5
if 'Sentinel' in imageSat or 'Landsat8' in imageSat:
    bandsClass = ['B1','B2', 'B3', 'B4','B2B3']
    bg = ['B2B3']
else:
    bandsClass = ['B1','B2', 'B3', 'B1B2']
    bg = ['B1B2']
    
## Add bands of interest to sample training points:
imageClassify = finalImage.addBands(imageDIV.select(bg)).select(bandsClass)
print('Bands to sample:',imageClassify.bandNames().getInfo())


seagrass_buffer = ee.FeatureCollection("users/lizcanosandoval/Seagrass_Habitat_Florida_buff5k")
#shallowMask = ee.ImageCollection("users/lizcanosandoval/Shallow_Mask_FL")
#specificTurbidMask = ee.ImageCollection("users/lizcanosandoval/TurbidityMask")
#listShallowMask = shallowMask.aggregate_array('system:index').getInfo()
#listTurbidMask = specificTurbidMask.aggregate_array('system:index').getInfo()

imageClassify = imageClassify.clip(seagrass_buffer) #For polygons



## Define a boxcar or low-pass kernel (Used if want to smooth the image)
smooth = ee.Kernel.euclidean(**{
    'radius': 1, 
    'units': 'pixels', 
    'normalize': True
})

## Apply smoother if set:
if 'smooth' in smoothStr:
    imageClassify = imageClassify.convolve(smooth)
    
    
## Sample multi-spectral data using all ground points.
samplingData = imageClassify.sampleRegions(**{
    'collection': filterPoints,
    'properties': ['class'],
    'scale': imageScale})

## Add random numbers to each feature (from 0 to 1).
randomData = samplingData.randomColumn("random",0)

## Split ground data in training (~70%) and validation (~30%) points
trainingData = randomData.filter(ee.Filter.lt("random",0.7))
validationData = randomData.filter(ee.Filter.gte("random", 0.7))

print('Training Points per Class:', trainingData.aggregate_histogram('class').getInfo())
print('Validation Points per Class:', validationData.aggregate_histogram('class').getInfo())
print('Training Samples (70%):',trainingData.size().getInfo())
print('Validation Samples (30%):',validationData.size().getInfo())