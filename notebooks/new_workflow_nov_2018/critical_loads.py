#-------------------------------------------------------------------------------
# Name:        critical_loads.py
# Purpose:     Functions to implement the updated (November 2018) Critical Loads 
#              workflow.
#
# Author:      James Sample
#
# Created:     20/11/2018
# Copyright:   (c) James Sample and NIVA, 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

def upload_nilu_0_1deg_dep_data(data_fold, eng, series_id):
    """ Process .dat files containing deposition data supplied by NILU. This 
        function is based on the data supplied by NILU during 2017, which uses 
        the new 0.1 degree deposition grid.
    
    Args:
        dat_fold:  Str. Path to folder containing .dat files provided by NILU
        eng:       Obj. Active database connection object connect to the Docker
                   PostGIS db
        series_id: Int. 'series_id' for this dataset from the table 
                   deposition.dep_series_defs
        
    Returns:
        DataFrame of the data added to the database.
    """
    import glob
    import os
    import pandas as pd

    # Read NILU data
    search_path = os.path.join(data_fold, '*.dat')
    file_list = glob.glob(search_path)

    df_list = []
    for fpath in file_list:
        # Get par name
        name = os.path.split(fpath)[1].split('_')[:2]
        name = '_'.join(name)

        # Read file
        df = pd.read_csv(fpath, delim_whitespace=True, header=None,
                         names=['lat', 'lon', name])
        df.set_index(['lat', 'lon'], inplace=True)    
        df_list.append(df)

    # Combine
    df = pd.concat(df_list, axis=1)
    df.reset_index(inplace=True)

    # Calculate unique integer cell ID as latlon 
    # (both *100 and padded to 4 digits)
    df['cell_id'] = ((df['lat']*100).astype(int).map('{:04d}'.format) + 
                     (df['lon']*100).astype(int).map('{:04d}'.format))
    df['cell_id'] = df['cell_id'].astype(int)
    del df['lat'], df['lon'], df['tot_n']

    # Rename
    df.rename(columns={'tot_nhx':2, # N (red)
                       'tot_nox':1, # N (oks)
                       'tot_s':4},  # Non-marine S
              inplace=True)

    # Melt 
    df = pd.melt(df, var_name='param_id', id_vars='cell_id')

    # Add series ID
    df['series_id'] = series_id

    # Add to db
    df.to_sql('dep_values_0_1deg_grid', 
              con=eng, 
              schema='deposition', 
              if_exists='append', 
              index=False)
    
    return df