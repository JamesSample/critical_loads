def reclassify_raster(in_tif, out_tif, reclass_df, reclass_col, ndv):
    """ Reclassify categorical values in a raster using a mapping
        in a dataframe. The dataframe index must contain the classes
        in in_tif and the 'reclass_col' must specify the new classes.
    """
    from osgeo import gdal, ogr
    from osgeo.gdalconst import GA_ReadOnly as GA_ReadOnly
    import numpy as np
    import pandas as pd

    # Open source file, read data
    src_ds = gdal.Open(in_tif, GA_ReadOnly)
    assert(src_ds)
    rb = src_ds.GetRasterBand(1)
    data = rb.ReadAsArray()
    
    # Reclassify
    for idx, row in reclass_df.iterrows():
        data[data==idx] = row[reclass_col]

    # Write output
    driver = gdal.GetDriverByName('GTiff')
    dst_ds = driver.CreateCopy(out_tif, src_ds, 0)
    out_band = dst_ds.GetRasterBand(1)
    out_band.SetNoDataValue(ndv)
    out_band.WriteArray(data)

    # Flush data and close datasets
    dst_ds = None
    src_ds = None
    
def vec_to_ras(in_shp, out_tif, snap_tif, attrib, ndv, data_type,
               fmt='GTiff'):
    """ Converts a shapefile to a raster with values taken from
        the 'attrib' field. The 'snap_tif' is used to set the 
        resolution and extent of the output raster.
        
    Args:
        in_shp:    Str. Raw string to shapefile
        out_tif:   Str. Raw string for geotiff to create
        snap_tif:  Str. Raw string to geotiff used to set resolution
                   and extent
        attrib:    Str. Shapefile field for values
        ndv:       Int. No data value
        data_type: Bit depth etc. e.g. gdal.GDT_UInt32
        fmt:       Str. Format string.
        
    Returns:
        None. Raster is saved.
    """
    from osgeo import ogr
    from osgeo import gdal
    
    # 1. Create new, empty raster with correct dimensions
    # Get properties from snap_tif
    snap_ras = gdal.Open(snap_tif)
    cols = snap_ras.RasterXSize
    rows = snap_ras.RasterYSize
    proj = snap_ras.GetProjection()
    geotr = snap_ras.GetGeoTransform()
    
    # Create out_tif
    driver = gdal.GetDriverByName(fmt)
    out_ras = driver.Create(out_tif, cols, rows, 1, data_type)
    out_ras.SetProjection(proj)
    out_ras.SetGeoTransform(geotr)
    
    # Fill output with NoData
    out_ras.GetRasterBand(1).SetNoDataValue(ndv)
    out_ras.GetRasterBand(1).Fill(ndv)

    # 2. Rasterize shapefile
    shp_ds = ogr.Open(in_shp)
    shp_lyr = shp_ds.GetLayer()

    gdal.RasterizeLayer(out_ras, [1], shp_lyr, 
                        options=['ATTRIBUTE=%s' % attrib])

    # Flush and close
    snap_ras = None
    out_ras = None
    shp_ds = None
    
def read_geotiff(geotiff_path):
    """ Reads a GeoTiff file to a numpy array.
    
    Args:
        geotiff_path Path to file
    
    Returns:
        Tuple: (array, NDV, (xmin, xmax, ymin, ymax))
        No data values in the array are set to np.nan
    """
    from osgeo import gdal, gdalconst
    import numpy as np

    # Register drivers
    gdal.AllRegister()

    # Read to array
    ds = gdal.Open(geotiff_path, gdalconst.GA_ReadOnly)
    assert(ds)
    band = ds.GetRasterBand(1)
    ndv = band.GetNoDataValue()   
    data = band.ReadAsArray()  

    # Flip. The data was flipped when it was created (see array_to_gtiff, 
    # above), so need to flip it back. Not sure why this is necessary? 
    # Beware in future!
    #data = data[::-1,:]
    
    # Close the dataset
    ds = None

    return (data, ndv)

def write_geotiff(data, out_tif, snap_tif, ndv, data_type):
    """ Write a numpy array to a geotiff.
    
    Args:
        data:      Array.
        out_tif:   Str. File to create
        snap_tif:  Str. Path to existing tif with same resolution
                   and extent as target
        ndv:       Int. No data value
        data_type: Bit depth etc. e.g. gdal.GDT_UInt32
        
    Returns:
        None. Geotiff is saved.        
    """
    from osgeo import ogr
    from osgeo import gdal
    
    # 1. Create new, empty raster with correct dimensions
    # Get properties from snap_tif
    snap_ras = gdal.Open(snap_tif)
    cols = snap_ras.RasterXSize
    rows = snap_ras.RasterYSize
    proj = snap_ras.GetProjection()
    geotr = snap_ras.GetGeoTransform()
    
    # Create out_tif
    driver = gdal.GetDriverByName('GTiff')
    out_ras = driver.Create(out_tif, cols, rows, 1, data_type)
    out_ras.SetProjection(proj)
    out_ras.SetGeoTransform(geotr)
    
    # Write data
    out_band = out_ras.GetRasterBand(1)
    out_band.SetNoDataValue(ndv)
    out_band.WriteArray(data)

    # Flush and close
    snap_ras = None
    out_band = None
    out_ras = None