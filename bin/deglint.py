


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