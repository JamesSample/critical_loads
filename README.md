# Exceedance of critical loads for water, soil and vegetation in Norway

Atmospheric deposition of nitrogen and sulphur play an important role in acidification. As part of the [UNECE Convention on Long-range Transboundary Air Pollution (LRTAP)](https://www.unece.org/env/lrtap/welcome.html), the [International Co-operative Programme (ICP) on Modelling and Mapping](http://www.icpmapping.org/) attempts to assess the extent and seriousness of air pollution effects, in part by estimating exceedances of "critical load" thresholds. 

In Norway, exceedances of critical loads are estimated every four years by [NIVA](http://www.niva.no/), in collaboration with [NILU](http://www.nilu.no/) and [Met.no](https://www.met.no/). The code in this repository documents an updated workflow prepared at NIVA during 2017. 

## Workflow

 1. **[Exceedance of critical loads for vegetation](http://nbviewer.jupyter.org/github/JamesSample/critical_loads/blob/master/notebooks/critical_loads_vegetation.ipynb)**. A raster-based workflow for the vegetation calculations
 
 2. **[Exceedance of critical loads for water](http://nbviewer.jupyter.org/github/JamesSample/critical_loads/blob/master/notebooks/critical_loads_water.ipynb)**. Exceedances for water are calculated using two models: SSWC and FAB. This notebook describes a new approach for the FAB calculations and compares results from the previous methodology (for both models) with the new output
 
 3. **[Interactive map of exceedances for water (2007 to 2011)](https://fusiontables.googleusercontent.com/embedviz?q=select+col6+from+1FJbAbZ-fB6UcDGABLkv5TKHljKmGTHGRLEukTI9R&viz=MAP&h=false&lat=61.63863460204371&lng=9.56805419921875&t=1&z=6&l=col6&y=2&tmplt=2&hml=KML)**. Results are based on the updated methodology for the FAB model. Clicking on any grid cell on the map will display summary information, including the "critical load function", which is described in detail [here](http://www.rivm.nl/media/documenten/cce/manual/binnenop17Juni/Ch7-MapMan-2016-04-26_vf.pdf)
