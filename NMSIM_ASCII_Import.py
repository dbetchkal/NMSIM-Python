## NMSIM_ASCII_Import.py
#
# The purpose of this toolbox script is to rapidly import the results of NMSIM models
# into ArcMap as a raster file.
#
#

import arcpy

# the model results as ASCII
asc = arcpy.GetParameterAsText(0)

# spatial reference as text
SRtxt = arcpy.GetParameterAsText(1)
SR = arcpy.SpatialReference() # an empty spatial reference object
SR.loadFromString(SRtxt)

# filepath for output file
out = arcpy.GetParameterAsText(2)

# convert from ASCII to Raster
ras = arcpy.ASCIIToRaster_conversion(in_ascii_file=asc, out_raster=out, data_type="FLOAT")

# define the projection
arcpy.DefineProjection_management(in_dataset=ras, coor_system=SR)

# add the raster to the map
arcpy.MakeRasterLayer_management(out, "NMSIM results")