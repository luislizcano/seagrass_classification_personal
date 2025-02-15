# -*- coding: utf-8 -*-
"""
Created on Sat Oct 17 18:42:48 2020

@author: Luis Lizcano-Sandoval
University of South Florida
luislizcanos@usf.edu

"""

import ee
ee.Initialize()

# =============================================================================
# Function to mask clouds using band thresholds.

# Buildings, Sand and Glinted pixels are too bright so they are also masked.
# It works very well for oceanographic purposes. It needs to be tweked to work
# with inland areas.

## Usage:
# img = image to apply cloud mask
# cloudThresh = integer used as threshold to mask clouds (see more info below)
# =============================================================================
## Composite parameters
## cloudThresh: If using the cloudScoreTDOMShift method-Threshold for cloud 
##     masking (lower number masks more clouds.  Between 10 and 30 generally 
##     works best).
## 20 is the best value for Sentinel-2 according to Zhu et al. (2015) & 
## Qiu et al. 2019 (https://doi.org/10.1016/j.rse.2019.05.024)
#cloudThresh = 12 # 12 works best for me. At 2 it cleans all cirrus, but land as well.

## A helper to apply an expression and linearly rescale the output.
## Used in the landsatCloudScore function.
def rescale(img, exp, thresholds):
    return (img.expression(exp, {'img': img})
      .subtract(thresholds[0]).divide(thresholds[1] - thresholds[0]))
 
def rescaleThr(img, exp, thresholds):
    return img.expression(exp, {'img': img})\
         .add(thresholds[0]).divide(thresholds[1] + thresholds[0])

## For BOA Sentinel-2 images, processed with the Py6S model 
## Adapted according to Chastain et al. 2019 (https://doi.org/10.1016/j.rse.2018.11.012).
## Compute a cloud score:
def CloudScore6S(sat, img, cloudThresh):
        
    cloudThresh = int(cloudThresh)
 
    if 'Sentinel' in sat:
        ## Compute several indicators of cloudyness and take the minimum of them.
        ## Bands required: [B1,B2,B3,B4,B8,B11,B12]
        score = ee.Image(1.0)

        ## Clouds are reasonably bright in the blue band.
        ## (BLUE−0.1) / (0.5−0.1)
        score = score.min(rescale(img, 'img.B2', [0.01, 0.3])) #[0.01,0.5]-for ocean

        ## Aerosols.
        ## (AEROSOL−0.1) / (0.3−0.1)
        score = score.min(rescale(img, 'img.B1', [0.01, 0.3])) #[0.01,0.5]-for ocean

        ## Clouds are reasonably bright in all visible bands.
        ## (BLUE+GREEN+RED−0.2) / (0.8−0.2)
        score = score.min(rescale(img, 'img.B4 + img.B3 + img.B2', [0.01, 0.8]))

        ## (((NIR−SWIR1)/(NIR+SWIR1))+0.1) / (0.1+0.1)
        score =  score.min(rescale(img, 'img.B8 + img.B11 + img.B12', [0.01, 0.8])) #.multiply(100).byte();

        ## However, clouds are not snow.
        ## (((GREEN−SWIR1)/(GREEN+SWIR1))−0.8) / (0.6−0.8)
        ndsi = img.normalizedDifference(['B3', 'B11'])
        score =  score.min(rescale(ndsi, 'img', [0.8, 0.6])).multiply(100).byte();
        ##Map.addLayer(score,{'min':0,'max':100});
        
        ## Apply threshold
        score = score.lt(cloudThresh).rename('cloudMask')
        img = img.updateMask(img.mask().And(score))
        return ee.Image(img).addBands(score)
    
    elif 'Landsat8' in sat:
        ## Compute several indicators of cloudyness and take the minimum of them.
        ## Bands required: [B1,B2,B3,B4,B5,B6,B7,B10]
        score = ee.Image(1.0)

        ## Clouds are reasonably bright in the blue band.
        ## (BLUE−0.1) / (0.5−0.1)
        score = score.min(rescale(img, 'img.SR_B2', [0.01, 0.3])) #[0.01,0.5]-for ocean

        ## Aerosols.
        ## (AEROSOL−0.1) / (0.3−0.1)
        score = score.min(rescale(img, 'img.SR_B1', [0.01, 0.3])) #[0.01,0.5]-for ocean

        ## Clouds are reasonably bright in all visible bands.
        ## (BLUE+GREEN+RED−0.2) / (0.8−0.2)
        score = score.min(rescale(img, 'img.SR_B4 + img.SR_B3 + img.SR_B2', [0.2, 0.8])) ## if [0.01, 0.8] - very sensitive to glint

        ## (((NIR−SWIR1)/(NIR+SWIR1))+0.1) / (0.1+0.1)
        score =  score.min(rescale(img, 'img.SR_B5 + img.SR_B6 + img.SR_B7', [0.1, 0.8])) #.multiply(100).byte();

        ## Clouds are reasonably cool in temperature.
        score = score.min(rescale(img,'img.ST_B10', [296, 280]));
        
        ## However, clouds are not snow.
        ## (((GREEN−SWIR1)/(GREEN+SWIR1))−0.8) / (0.6−0.8)
        ndsi = img.normalizedDifference(['SR_B3', 'SR_B6'])
        score =  score.min(rescale(ndsi, 'img', [0.8, 0.6])).multiply(100).byte();
        ##Map.addLayer(score,{'min':0,'max':100});
        
        ## Apply threshold
        score = score.lt(cloudThresh).rename('cloudMask')
        img = img.updateMask(img.mask().And(score))
        return ee.Image(img).addBands(score)
        
    elif 'Landsat7' in sat:
        ## Compute several indicators of cloudyness and take the minimum of them.
        ## Bands required: [B1,B2,B3,B4,B5,B6,B7]
        score = ee.Image(1.0)

        ## Clouds are reasonably bright in the blue band.
        ## (BLUE−0.1) / (0.5−0.1)
        score = score.min(rescale(img, 'img.SR_B1', [0.01, 0.3])) #[0.01,0.5]-for ocean

        ## Clouds are reasonably bright in all visible bands.
        ## (BLUE+GREEN+RED−0.2) / (0.8−0.2)
        score = score.min(rescale(img, 'img.SR_B3 + img.SR_B2 + img.SR_B1', [0.2, 0.8]))

        ## (((NIR−SWIR1)/(NIR+SWIR1))+0.1) / (0.1+0.1)
        score =  score.min(rescale(img, 'img.SR_B4 + img.SR_B5 + img.SR_B7', [0.1, 0.8])) #.multiply(100).byte();

        ## Clouds are reasonably cool in temperature.
        score = score.min(rescale(img,'img.ST_B6', [296, 280]));
        
        ## However, clouds are not snow.
        ## (((GREEN−SWIR1)/(GREEN+SWIR1))−0.8) / (0.6−0.8)
        ndsi = img.normalizedDifference(['SR_B3', 'SR_B5'])
        score =  score.min(rescale(ndsi, 'img', [0.8, 0.6])).multiply(100).byte();
        ##Map.addLayer(score,{'min':0,'max':100});
        
        ## Apply threshold
        score = score.lt(cloudThresh).rename('cloudMask')
        img = img.updateMask(img.mask().And(score))
        return ee.Image(img).addBands(score)
    
    elif 'Landsat5' in sat:
        ## Compute several indicators of cloudyness and take the minimum of them.
        ## Bands required: [B1,B2,B3,B4,B5,B6,B7]
        score = ee.Image(1.0)

        ## Clouds are reasonably bright in the blue band.
        ## (BLUE−0.1) / (0.5−0.1)
        score = score.min(rescale(img, 'img.SR_B1', [0.01, 0.3])) #[0.01,0.5]-for ocean

        ## Clouds are reasonably bright in all visible bands.
        ## (BLUE+GREEN+RED−0.2) / (0.8−0.2)
        score = score.min(rescale(img, 'img.SR_B3 + img.SR_B2 + img.SR_B1', [0.2, 0.8]))

        ## (((NIR−SWIR1)/(NIR+SWIR1))+0.1) / (0.1+0.1)
        score =  score.min(rescale(img, 'img.SR_B4 + img.SR_B5 + img.SR_B7', [0.1, 0.8])) #.multiply(100).byte();

        ## Clouds are reasonably cool in temperature.
        score = score.min(rescale(img,'img.ST_B6', [296, 280]));
        
        ## However, clouds are not snow.
        ## (((GREEN−SWIR1)/(GREEN+SWIR1))−0.8) / (0.6−0.8)
        ndsi = img.normalizedDifference(['SR_B3', 'SR_B5'])
        score =  score.min(rescale(ndsi, 'img', [0.8, 0.6])).multiply(100).byte();
        ##Map.addLayer(score,{'min':0,'max':100});
        
        ## Apply threshold
        score = score.lt(cloudThresh).rename('cloudMask')
        img = img.updateMask(img.mask().And(score))
        return ee.Image(img).addBands(score)
        
        
###############################################################################

# =============================================================================
# Function to mask land.

## Usage:
# image = image to apply land mask.
# geometry = feature (polygon) of land to create a mask.
# =============================================================================
def landMaskFunction(image,geometry):
    mask = ee.Image.constant(1).clip(geometry).mask().Not()
    return image.updateMask(mask)

###############################################################################


# =============================================================================
# Function to mask tidal flats.

## Usage:
# image = image to apply tidal flat mask.
# nir = str nir band
# green = str green band
# =============================================================================
def tidalMask(image,nir,green):
    ndwi = image.normalizedDifference([nir,green]).rename('ndwi')
    ndwiMask = ndwi.gte(-0.4).Not()
    imgMasked = image.updateMask(ndwiMask)
    return imgMasked

###############################################################################


# =============================================================================
# Function to mask turbidity.

## Usage:
# image = image to apply tidal flat mask.
# geometry = feature (polygon) of the are of interest.
# nir = str nir band
# swir = str swir band
# blue = str blue band
# land = raster to mask land
# =============================================================================
def turbidityMask(image,geometry,nir,swir,blue,land):
    ## Use NIR and SWIR1 bands to generate an index for turbidity
    ndti = image.normalizedDifference([nir,swir]).rename('NDTI')
    
    ## Apply kernel to smooth NDTI
    kernel = ee.Kernel.euclidean(**{
        'radius':3,'units':'pixels','normalize':False})
    ndti = ndti.convolve(kernel)
    
    ## Get median value in the region of interest and use as threshold.
    stats = ndti.reduceRegion(**{
      'reducer': ee.Reducer.median(),
      'geometry': geometry,
      'scale':10,
      'maxPixels': 1e13,
      'crs': 'EPSG:4326'})
    thr = ee.Number(stats.get('NDTI'))

    ## Create mask
    mask_ndti = ndti.gte(thr)

    ## apply mask to NIR band, which will be the most sensitive to
    ## turbidity in this case, even more than Red-Edge
    mask_img = image.select(nir).rename('NIR').updateMask(mask_ndti)
    
    ## Get mean and mode values
    stats2 = mask_img.reduceRegion(**{
      'reducer': ee.Reducer.mean().combine(**{
        'reducer2': ee.Reducer.mode(),
        'sharedInputs': True}),
      'geometry': geometry,
      'scale':10,
      'maxPixels': 1e13,
      'crs': 'EPSG:4326'})
    mean = ee.Number(stats2.get('NIR_mean'))
    mode = ee.Number(stats2.get('NIR_mode'))

    ## Use mode or mean values as threshold and mask turbidity
    maskTurbidity = ee.Algorithms.If(**{
      'condition': mode.gte(0.005),
      'trueCase': mask_img.updateMask(mask_img.gte(mode)).mask(),
      'falseCase': mask_img.updateMask(mask_img.gte(mean)).mask()
    })

    ## Separate turbidity from possible seagrass patches masked.
    ## NIR and Blue bands works better to mask shallow seagrass
    ## NDSI = normalizes difference seagrass index
    ndsi = image.normalizedDifference([nir,blue]).rename('NDSI')
    
    ## Get mean value of the 80-100 percentile
    stats3 = ndsi.reduceRegion(**{
      'reducer': ee.Reducer.intervalMean(80,100),
      'geometry': geometry,
      'scale':10,
      'maxPixels': 1e13,
      'crs': 'EPSG:4326'})
    thr2 = ee.Number(stats3.get('NDSI'))
    
    ## Apply threshold value and mask possible shallow seagrass patches.
    ndsi_mask = ndsi.gte(thr2).Not()
    final_mask = ee.Image(maskTurbidity).updateMask(ndsi_mask).unmask(0)
    final_mask = final_mask.updateMask(land.max()).clip(geometry).Not()
    output = image.updateMask(final_mask)
    
    return output

###############################################################################

# =============================================================================
#  Depth-Invariant Index
#
# Usage:
# image = image to apply DII (with at least 3 bands B1-B4 for Sentinel-2)
# bands = select 3 bands, e.g.: ['B1','B2','B3']
# sand = feature collection with polygons representing sand areas at different depths
#
# Output:
# ee.Image with three bands B1B2, B1B3, B2B3
# =============================================================================
def DII(image, scale, sand):
    
    ## Select the bands for the DIV
    #bands = ['B1','B2','B3']
    bands = [0,1,2]
    image_div = ee.Image(image).select(bands)
    
    ## Calculate standard deviation
    imgSTD = image_div.reduceRegion(**{
      'reducer': ee.Reducer.stdDev(),
      'geometry': sand,
      'scale': scale,
      'maxPixels': 3e9}).toArray()
    
    ## Calculate variance
    imgVAR = imgSTD.multiply(imgSTD).toList()
    
    ## Calculate mean
    imgMEAN = image_div.reduceRegion(**{
      'reducer': ee.Reducer.mean(),
      'geometry': sand,
      'scale': scale,
      'maxPixels': 3e9}).toArray()
    
    ## Calculate coefficient of variation
    CV = imgSTD.divide(imgMEAN)

    ## Covariance Matrix for band pairs
    #imgCOV = ee.Dictionary(image_div.subtract(imgMEAN).reduceRegion(ee.Reducer.centeredCovariance(),sand_poly))#assumes mean centered image
    imgCOV = image_div.toArray().reduceRegion(**{
      'reducer': ee.Reducer.covariance(),
      'geometry': sand,
      'scale': scale})
    imgCOV = ee.Array(imgCOV.get('array'))
    imgCOVB12 =  ee.Number(imgCOV.get([0,1]))
    imgCOVB13 =  ee.Number(imgCOV.get([0,2]))
    imgCOVB23 =  ee.Number(imgCOV.get([1,2]))

    ## Attenuation Coefficient (a) of band pairs
    var1 = ee.Number(imgVAR.get(0))
    var2 = ee.Number(imgVAR.get(1))
    var3 = ee.Number(imgVAR.get(2))
    a1_2 = (var1.subtract(var2)).divide(imgCOVB12.multiply(2))
    a1_3 = (var1.subtract(var3)).divide(imgCOVB13.multiply(2))
    a2_3 = (var2.subtract(var3)).divide(imgCOVB23.multiply(2))

    ## Ratio of Attenuation Coefficient
    k1_2 = a1_2.add(((a1_2.multiply(a1_2).add(1))).pow(0.5))
    k1_3 = a1_3.add(((a1_3.multiply(a1_3).add(1))).pow(0.5))
    k2_3 = a2_3.add(((a2_3.multiply(a2_3).add(1))).pow(0.5))

    ## Depth invariance index DII
    DII_1_2 = image_div.select(0).log().subtract(image_div.select(1).log().multiply(k1_2))
    DII_1_3 = image_div.select(0).log().subtract(image_div.select(2).log().multiply(k1_3))
    DII_2_3 = image_div.select(1).log().subtract(image_div.select(2).log().multiply(k2_3))

    ## Make depth invariance image
    DI_image = ee.Image()
    DI_image = DI_image.addBands(DII_1_2.select([0],['B1B2']))
    DI_image = DI_image.addBands(DII_1_3.select([0],['B1B3']))
    DI_image = DI_image.addBands(DII_2_3.select([0],['B2B3']))
    DII = DI_image.select('B1B2','B1B3','B2B3')
    
    return ee.Image(DII)

###############################################################################




