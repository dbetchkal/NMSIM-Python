## NMSIM_Create_Base_Layers.py
#
#  Questions? Davyd_Betchkal@nps.gov 
#
#  The purpose of this toolbox script is to rapidly prepare base layer inputs for NMSIM models.
#  With the associated DEM files, it will work for models ≤ 20km from NPS lands.
#

import os
import pandas as pd
import arcpy


def make(path):
    """
    Safely create a folder
    """

    if not os.path.exists(path):
        os.makedirs(path)


def make_NMSIM_project_dir(projectDir):

	"""
	Create a canonical NMSIM project directory.

	Inputs
	------
	projectDir (str): a path location where an NMSIM project directory will be created

	"""

	# a list of all the subfolders for a project
	subfolders = [r"Input_Data", r"Input_Data\01_ELEVATION", r"Input_Data\02_IMPEDANCE", r"Input_Data\03_TRAJECTORY",
	            r"Input_Data\04_LAYERS", r"Input_Data\05_SITES", r"Input_Data\06_AMBIENCE", r"Input_Data\07_WEATHER",
	            r"Input_Data\08_TREES", r"Output_Data", r"Output_Data\ASCII", r"Output_Data\IMAGES", r"Output_Data\SITE", 
	            r"Output_Data\TIG_TIS"]

	# make all the subfolders
	for folderExt in subfolders:
	    make(projectDir + os.sep + folderExt)


def find_UTM_zone(studyArea):

	"""
	NMSIM references an entire project to the westernmost extent
	of the elevation (or landcover) file. Given that, return the 
	UTM Zone the project will eventually use.

	Inputs
	------
	studyArea (.shp) the area you wish to model with NMSIM

	Returns
	-------
	UTM_zone (int) the UTM zone of the eventual NMSIM project

	"""

	# we need to know the western extent in degrees longitude
	NAD83 = arcpy.SpatialReference(4326)

	with arcpy.da.SearchCursor(studyArea, "Shape@", spatial_reference=NAD83) as search_rows:
		for row in search_rows:

			UTM_w = row[0].extent.XMin

	# use integer divide to return the ceiling to the nearest 6°
	nearest_west = int(6*(UTM_w//6))

	# a lookup table for UTM zone's western boundary
	UTM_zone_lookup = {l:i+1 for i, l in enumerate(range(-180, 180, 6))}

	# what is the project's UTM zone
	UTM_zone = UTM_zone_lookup[nearest_west]

	return UTM_zone


def DEM_selector(alphaCode, raster_folder):

	"""
	Find the correct DEM raster to use for the model.
	"""

	# this looks for a file called "NPSParkUnits.csv" at the same diretory level as this script
	NPS_units_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "NPS_Unit_to_DEM.csv")
	
	# read in table using `pandas`
	NPS_units = pd.read_csv(NPS_units_path, encoding = "ISO-8859-1")

	# look up the beginning of the raster name
	Raster = NPS_units.loc[NPS_units.UNIT_CODE == alphaCode, "DEM_Name"].values[0]

	# this is where the appropriate DEM for the unit is located
	fullRasterpath = raster_folder + os.sep + Raster

	return fullRasterpath


def create_baselayers(alphaCode, studyArea, projectDir, raster_folder):

	"""
	Use the study area to select the right DEM, clip it, project it, 
	and save it in a canonical NPS NMSIM project directory.
	
	Inputs
	------
	alphaCode (str): standard NPS four-letter code for the park you are modelling
	studyArea (shapefile or feature class) the area you wish to model with NMSIM, **AREA LIMITATION??**
	projectDir (str): a path location where an NMSIM project directory will be created

	Returns
	-------
	None

	"""

	# select the raster associated with this park
	try:
		DEM_path = DEM_selector(alphaCode, raster_folder)

		print(DEM_path)

	except:
		print("The correct DEM could not be found for this unit. Please check:\n(1) DEM files in your NMSIM folder in a subfolder called 'NPS_DEM'\n(2) 'NPS_Unit_to_DEM.csv' is in the same directory as this script.")


	# NMSIM uses the following spatial reference: GCS_North_American_1983; WKID: 4269
	SR = arcpy.SpatialReference(4269)

	# clip elevation data
	dem_clip = arcpy.Clip_management(in_raster=DEM_path, 
									rectangle="#", 
									out_raster="NMSIM_DEM_clip", 
									in_template_dataset=studyArea, 
									nodata_value="-99999", 
									clipping_geometry="ClippingGeometry", 
									maintain_clipping_extent="NO_MAINTAIN_EXTENT")

	# project the elevation data
	dem_proj = arcpy.ProjectRaster_management(dem_clip, "NMSIM_DEM_proj", SR)

	# try making the project directory
	try:
		make_NMSIM_project_dir(projectDir)

	except: 
		# might fail if the directory already exists
		print("Uh oh the function `make_NMSIM_project_dir` encountered an error!")

	# from now on, we'll store UTM zone information in the filenames
	# look up the UTM zone that NMSIM will use for this study area
	try:
		UTM_zone = find_UTM_zone(studyArea)

		print("NMSIM will use UTM Zone", UTM_zone)

	except:
		print("Uh oh the function `find_UTM_zone` encountered an error!")

	# combine all the elements to make the elevation gridfloat file's path
	elevPath = projectDir + os.sep + r"Input_Data\01_ELEVATION" + os.sep + "elevation_nad83_utm" + str(UTM_zone) + ".flt"

	# convert the elevation raster to grid float, as NMSIM needs
	arcpy.RasterToFloat_conversion(dem_proj, elevPath)

	print("Saved gridfloat file successfully.")


# ---------------------------------------------------
# --------------- RUN THE TOOL ----------------------

# park unit 4-letter alpha code
alphaCode = arcpy.GetParameterAsText(0)

# study area used to clip the base layers
studyArea = arcpy.GetParameterAsText(1)

# full path of the new project's root folder
projectDir = arcpy.GetParameterAsText(2)

# path to the folder containing baselayers
baselayer_path = arcpy.GetParameterAsText(3)

# run the function
create_baselayers(alphaCode, studyArea, projectDir, baselayer_path)

# ---------------------------------------------------
