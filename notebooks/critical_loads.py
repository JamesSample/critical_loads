def reclassify_raster(in_tif, mask_tif, out_tif, reclass_df, reclass_col, ndv):
    """ Reclassify categorical values in a raster using a mapping
        in a dataframe. The dataframe index must contain the classes
        in in_tif and the 'reclass_col' must specify the new classes.
        
        Only cells with value=1 in mask_tif are written to output.
    """
    from osgeo import gdal, ogr
    from osgeo.gdalconst import GA_ReadOnly as GA_ReadOnly
    import numpy as np
    import pandas as pd

    # Open source file, read data
    src_ds = gdal.Open(in_tif, GA_ReadOnly)
    assert(src_ds)
    rb = src_ds.GetRasterBand(1)
    src_data = rb.ReadAsArray()

    # Open mask, read data
    mask_ds = gdal.Open(mask_tif, GA_ReadOnly)
    assert(mask_ds)
    mb = mask_ds.GetRasterBand(1)
    mask_data = mb.ReadAsArray()
    
    # Reclassify
    rc_data = src_data.copy()
    for idx, row in reclass_df.iterrows():
        rc_data[src_data==idx] = row[reclass_col]

    # Apply mask
    rc_data[mask_data!=1] = ndv
    
    # Write output
    driver = gdal.GetDriverByName('GTiff')
    dst_ds = driver.CreateCopy(out_tif, src_ds, 0)
    out_band = dst_ds.GetRasterBand(1)
    out_band.SetNoDataValue(ndv)
    out_band.WriteArray(rc_data)

    # Flush data and close datasets
    dst_ds = None
    src_ds = None
    mask_ds = None
    
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
    
def exceed_ns_icpm(cln_min, cln_max, cls_min, cls_max, dep_n, dep_s):
    """ Calculates exceedances based on the methodology outlined by Max
        Posch in the ICP Mapping manual (section VII.4):
        
        http://www.rivm.nl/media/documenten/cce/manual/binnenop17Juni/Ch7-MapMan-2016-04-26_vf.pdf
        
        NB: All units should be in eq/l.
        
    Args:
        cln_min: Float. Parameter to define "critical load function" (see PDF)
        cln_max: Float. Parameter to define "critical load function" (see PDF)
        cls_min: Float. Parameter to define "critical load function" (see PDF)
        cls_max: Float. Parameter to define "critical load function" (see PDF)
        dep_n:   Float. Total N deposition
        dep_s:   Float. Total (non-marine) S deposition
        
    Returns:
        Tuple (ex_n, ex_s, reg_id)
        
        ex_n and ex_s are the exceedances for N and S depositions dep_n and dep_s
        and the CLF defined by (cln_min, cls_max) and (cln_max, cls_min). The 
        overall exceedance is (ex_n + ex_s). 
        
        reg_id is an integer region ID, as defined in Figure VII.3 of the PDF.
    """
    # Check inputs
    assert (dep_n >= 0) and (dep_s >= 0), 'Deposition cannot be negative.'
    
    # Make sure floats
    cln_min = float(cln_min)
    cln_max = float(cln_max)
    cls_min = float(cls_min)
    cls_max = float(cls_max)
    dep_n = float(dep_n)
    dep_s = float(dep_s)    
    
    # Handle edge cases
    # CLF pars < 0
    if (cln_min < 0) or (cln_max < 0) or (cls_min <0) or (cls_max < 0):
        # Pars not valid
        return (-1, -1, -1)
    
    # CL = 0
    if (cls_max == 0) and (cln_max == 0):
        # All dep is above CL
        return (dep_n, dep_s, 9)
    
    # Otherwise, we're somewhere on Fig. VII.3
    dn = cln_min - cln_max
    ds = cls_max - cls_min
    
    if ((dep_s <= cls_max) and (dep_n <= cln_max) and
        ((dep_n - cln_max)*ds <= (dep_s - cls_min)*dn)):
        # Non-exceedance
        return (0, 0, 0)
    
    elif (dep_s <= cls_min):
        # Region 1
        ex_s = 0
        ex_n = dep_n - cln_max
        
        return (ex_n, ex_s, 1)

    elif (dep_n <= cln_min):
        # Region 5
        ex_s = dep_s - cls_max
        ex_n = 0
        
        return (ex_n, ex_s, 5)        

    elif (-(dep_n - cln_max)*dn >= (dep_s - cls_min)*ds):
        # Region 2
        ex_n = dep_n - cln_max
        ex_s = dep_s - cls_min
        
        return (ex_n, ex_s, 2)         
           
    elif (-(dep_n - cln_min)*dn <= (dep_s - cls_max)*ds):
        # Region 4
        ex_n = dep_n - cln_min
        ex_s = dep_s - cls_max
        
        return (ex_n, ex_s, 4)
    
    else:
        # Region 3
        dd = dn**2 + ds**2
        s = dep_n*dn + dep_s*ds
        v = cln_max*ds - cls_min*dn
        xf = (dn*s + ds*v)/dd
        yf = (ds*s - dn*v)/dd
        ex_n = dep_n - xf
        ex_s = dep_s - yf  
        
        return (ex_n, ex_s, 3)
    
def plot_critical_loads_func(cln_min, cln_max, cls_min, cls_max, ndeps, sdeps,
                             title=None, save_png=False, png_path=None):
    """ Plots the critical load function, as defined in section VII.4 here:
    
        http://www.rivm.nl/media/documenten/cce/manual/binnenop17Juni/Ch7-MapMan-2016-04-26_vf.pdf
        
    Args:
        cln_min:  Float. Parameter to define "critical load function" (see PDF)
        cln_max:  Float. Parameter to define "critical load function" (see PDF)
        cls_min:  Float. Parameter to define "critical load function" (see PDF)
        cls_max:  Float. Parameter to define "critical load function" (see PDF)
        ndeps:    Array like. List of x-coords for points
        sdeps:    Array like. List of x-coords for points
        title:    Str. Plot title, if desired
        save_png: Bool. Whether to save plot as PNG
        png_path: Raw str. Output path (if save_png=True)
        
    Returns:
        None
    """
    import matplotlib.pyplot as plt
    import seaborn as sn
    sn.set_context('poster')

    # Make sure floats
    cln_min = float(cln_min)
    cln_max = float(cln_max)
    cls_min = float(cls_min)
    cls_max = float(cls_max)
    
    # Plot
    fig = plt.figure(figsize=(8,8))
    
    # Get max extent for maintaining aspect
    all_vals = [cln_max, cls_max] + ndeps + sdeps
    max_ext = 1.2*max(all_vals)
    
    # CLF
    plt.plot([0, cln_min], [cls_max, cls_max], 'k-')
    plt.plot([cln_max, cln_max], [0, cls_min], 'k-') 
    plt.plot([cln_min, cln_max], [cls_max, cls_min], 'k-')
    
    # Regions 1 and 5
    plt.plot([cln_min, cln_min], [cls_max, max_ext], 'k--')
    plt.plot([cln_max, max_ext], [cls_min, cls_min], 'k--')
    
    # Regions 2, 3 and 4
    if (cln_max - cln_min) == 0:
        perp = 0
    else:
        grad = (cls_min - cls_max)/(cln_max - cln_min)
        perp = -1/grad
    
    plt.plot([cln_min, max_ext], 
             [cls_max, perp*max_ext + cls_max - perp*cln_min], 'k--')
    
    plt.plot([cln_max, max_ext], 
             [cls_min, perp*max_ext + cls_min - perp*cln_max], 'k--')
    
    # Points
    plt.plot(ndeps, sdeps, 'ro')
    
    # Tidy
    plt.xlim((0, max_ext))
    plt.ylim((0, max_ext))
    plt.xlabel('$N_{dep}$', fontsize=26)
    plt.ylabel('$S_{dep}$', fontsize=26)
    if title:
        plt.title(title)
        
    # Save
    if save_png:
        plt.savefig(png_path, dpi=200)