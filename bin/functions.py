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
        score = ee.Image(1.0)

        ## Clouds are reasonably bright in the blue band.
        ## (BLUE−0.1) / (0.5−0.1)
        score = score.min(rescale(img, 'img.B2', [0.01, 0.5])) #[0.01,0.5]-for ocean

        ## Aerosols.
        ## (AEROSOL−0.1) / (0.3−0.1)
        score = score.min(rescale(img, 'img.B1', [0.01, 0.5])) #[0.01,0.5]-for ocean

        ## Clouds are reasonably bright in all visible bands.
        ## (BLUE+GREEN+RED−0.2) / (0.8−0.2)
        score = score.min(rescale(img, 'img.B4 + img.B3 + img.B2', [0.02, 0.8]))

        ## (((NIR−SWIR1)/(NIR+SWIR1))+0.1) / (0.1+0.1)
        score =  score.min(rescaleThr(img, 'img.B8 + img.B11 + img.B12', [0.01, 0.8])) #.multiply(100).byte();

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
        score =  score.min(rescale(img, 'img.B5 + img.B6 + img.B7', [0.01, 0.8])) #.multiply(100).byte();

        ## Clouds are reasonably cool in temperature.
        score = score.min(rescale(img,'img.B10', [296, 280]));
        
        ## However, clouds are not snow.
        ## (((GREEN−SWIR1)/(GREEN+SWIR1))−0.8) / (0.6−0.8)
        ndsi = img.normalizedDifference(['B3', 'B6'])
        score =  score.min(rescale(ndsi, 'img', [0.8, 0.6])).multiply(100).byte();
        ##Map.addLayer(score,{'min':0,'max':100});
        
        ## Apply threshold
        score = score.lt(cloudThresh).rename('cloudMask')
        img = img.updateMask(img.mask().And(score))
        return ee.Image(img).addBands(score)
        
    elif 'Landsat7' in sat:
        ## Compute several indicators of cloudyness and take the minimum of them.
        score = ee.Image(1.0)

        ## Clouds are reasonably bright in the blue band.
        ## (BLUE−0.1) / (0.5−0.1)
        score = score.min(rescale(img, 'img.B1', [0.01, 0.3])) #[0.01,0.5]-for ocean

        ## Clouds are reasonably bright in all visible bands.
        ## (BLUE+GREEN+RED−0.2) / (0.8−0.2)
        score = score.min(rescale(img, 'img.B3 + img.B2 + img.B1', [0.01, 0.8]))

        ## (((NIR−SWIR1)/(NIR+SWIR1))+0.1) / (0.1+0.1)
        score =  score.min(rescale(img, 'img.B4 + img.B5 + img.B7', [0.01, 0.8])) #.multiply(100).byte();

        ## Clouds are reasonably cool in temperature.
        score = score.min(rescale(img,'img.B6_VCID_1', [296, 280]));
        
        ## However, clouds are not snow.
        ## (((GREEN−SWIR1)/(GREEN+SWIR1))−0.8) / (0.6−0.8)
        ndsi = img.normalizedDifference(['B3', 'B5'])
        score =  score.min(rescale(ndsi, 'img', [0.8, 0.6])).multiply(100).byte();
        ##Map.addLayer(score,{'min':0,'max':100});
        
        ## Apply threshold
        score = score.lt(cloudThresh).rename('cloudMask')
        img = img.updateMask(img.mask().And(score))
        return ee.Image(img).addBands(score)
    
    elif 'Landsat5' in sat:
        ## Compute several indicators of cloudyness and take the minimum of them.
        score = ee.Image(1.0)

        ## Clouds are reasonably bright in the blue band.
        ## (BLUE−0.1) / (0.5−0.1)
        score = score.min(rescale(img, 'img.B1', [0.01, 0.3])) #[0.01,0.5]-for ocean

        ## Clouds are reasonably bright in all visible bands.
        ## (BLUE+GREEN+RED−0.2) / (0.8−0.2)
        score = score.min(rescale(img, 'img.B3 + img.B2 + img.B1', [0.01, 0.8]))

        ## (((NIR−SWIR1)/(NIR+SWIR1))+0.1) / (0.1+0.1)
        score =  score.min(rescale(img, 'img.B4 + img.B5 + img.B7', [0.01, 0.8])) #.multiply(100).byte();

        ## Clouds are reasonably cool in temperature.
        score = score.min(rescale(img,'img.B6', [296, 280]));
        
        ## However, clouds are not snow.
        ## (((GREEN−SWIR1)/(GREEN+SWIR1))−0.8) / (0.6−0.8)
        ndsi = img.normalizedDifference(['B3', 'B5'])
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
#  KD CORRECTIONS
#
# Usage:
# image = image to correct (with at least bands B1-B4 for Sentinel-2)
# bathymetry = bathymetry raster file
# =============================================================================

## Assuming clear water, we can extract the effect of light attenuation on bands
## 1 to 4 (Sentinel-2). It will correct the reflectance values only for water (AOP),
## ignoring the effect of chlorophyll and particles (IOP).
## Kd values based on spectral absorption and backscattering coefficients of pure seawater
## by Smith and Baker (1981). Values are interpolated to match Sentinel-2 Bands.
## The calculations follow the Beer's law equation.


def kdCorrection(image, bathymetry):
    kdB1 = ee.Number(-0.0169)  #445nm
    kdB2 = ee.Number(-0.02415) #495nm
    kdB3 = ee.Number(-0.0717)  #560nm
    kdB4 = ee.Number(-0.415)   #665nm
    
    ## Convert depth values to positive.
    BathyArray = bathymetry.abs()#.convolve(kernel)
    #BathyArray = etopo_clip
    bandB1 = image.select('B1')
    bandB2 = image.select('B2')
    bandB3 = image.select('B3')
    bandB4 = image.select('B4')
    expB1 = (BathyArray.multiply(kdB1)).exp()
    expB2 = (BathyArray.multiply(kdB2)).exp()
    expB3 = (BathyArray.multiply(kdB3)).exp()
    expB4 = (BathyArray.multiply(kdB4)).exp()
    EdB1 = bandB1.multiply(expB1);
    EdB2 = bandB2.multiply(expB2);
    EdB3 = bandB3.multiply(expB3);
    EdB4 = bandB4.multiply(expB4);
    
    ## Image after correcting the light attenuation effect
    imageKd = EdB1.addBands(EdB2).addBands(EdB3).addBands(EdB4)
    
    return ee.Image(imageKd)
###############################################################################

# =============================================================================
#  Depth-Invariant Index
#
# Usage:
# image = image to apply DIV (with at least 3 bands B1-B4 for Sentinel-2)
# bands = select 3 bands, e.g.: ['B1','B2','B3']
# sand = feature collection with polygons representing sand areas at different depths
#
# Output:
# ee.Image with three bands B1B2, B1B3, B2B3
# =============================================================================
def div(image, scale, sand):
    
    ## Select the bands for the DIV
    bands = ['B1','B2','B3']
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
    DII_1_2 = image_div.select('B1').log().subtract(image_div.select('B2').log().multiply(k1_2))
    DII_1_3 = image_div.select('B1').log().subtract(image_div.select('B3').log().multiply(k1_3))
    DII_2_3 = image_div.select('B2').log().subtract(image_div.select('B3').log().multiply(k2_3))

    ## Make depth invariance image
    DI_image = ee.Image()
    DI_image = DI_image.addBands(DII_1_2.select(['B1'],['B1B2']))
    DI_image = DI_image.addBands(DII_1_3.select(['B1'],['B1B3']))
    DI_image = DI_image.addBands(DII_2_3.select(['B2'],['B2B3']))
    DIV = DI_image.select('B1B2','B1B3','B2B3')
    
    return ee.Image(DIV)

###############################################################################

# =============================================================================
#  Sun-Glint Correction
#
# Usage:
# image = image with bands B1-B5
# bands = select 3 bands, e.g.: ['B1','B2','B3']
# glint = feature collection with polygons representing glinted areas of specific images
#
# Output:
# ee.Image with three bands B1, B2, B3, B4
# =============================================================================
##Function to correct for Sunglint
## Input: an water surface reflectance image
## Output: the image after Sunglint correction

def deglint(image):
    ## Fit a linear model between NIR and other bands, in the sunglint polygons
    ## Output: a dictionary such that: linear_fit.keys() =  ["coefficients","residuals"]
    linearFit1 = image.select(['B5', 'B1']).reduceRegion(**{
        'reducer': ee.Reducer.linearFit(),
        'geometry': sunglint,
        'scale': 30,
        'maxPixels': 1e12
        })
  
    linearFit2 = image.select(['B5', 'B2']).reduceRegion(**{
        'reducer': ee.Reducer.linearFit(),
        'geometry': sunglint,
        'scale': 30,
        'maxPixels': 1e12
        })
  
    linearFit3 = image.select(['B5', 'B3']).reduceRegion(**{
        'reducer': ee.Reducer.linearFit(),
        'geometry': sunglint,
        'scale': 30,
        'maxPixels': 1e12
        })
  
    linearFit4 = image.select(['B5', 'B4']).reduceRegion(**{
        'reducer': ee.Reducer.linearFit(),
        'geometry': sunglint,
        'scale': 30,
        'maxPixels': 1e12
        })

  
    ## Extract the slope of the fit, convert it into a constant image
    slopeImage = ee.Dictionary(**{'B1': linearFit1.get('scale'), 
                                  'B2': linearFit2.get('scale'), 
                                  'B3': linearFit2.get('scale'),
                                  'B4': linearFit3.get('scale')}).toImage()
  
    ## Calculate the minimum of NIR in the image, in the sunglint polygons
    minNIR = image.select('B5').reduceRegion(**{
        'reducer': ee.Reducer.min(),
        'geometry': sunglint,
        'scale': 30,
        'maxPixels': 1e12
        }).toImage(['B5']);
  
    ## Apply the expression  
    return image.select(['B1','B2', 'B3','B4']).subtract(slopeImage.multiply((image.select('B5')).subtract(minNIR)))


