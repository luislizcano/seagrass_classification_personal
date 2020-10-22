# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 13:08:56 2020

@author: lizca
"""

import ee
ee.Initialize()
# =============================================================================
#  KD CORRECTIONS
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