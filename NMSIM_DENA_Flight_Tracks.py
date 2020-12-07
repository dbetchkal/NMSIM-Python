#-----------------------------------------------------------------------------#
# NMSIM_DENA_Flight_Tracks.py
#
# NPS Natural Sounds Program
#
# Last updated: 2030 12 03
#
# This module is used to initialize a workspace
#
# 
#
#
# History:
#	D. Halyn Betchkal -- Created
#
#-----------------------------------------------------------------------------#

# ================ Import Libraries =======================

# some very standard libraries
import sys
import datetime as dt
import os
import re
import glob
import shutil
import subprocess
from functools import partial
import numpy as np
import pandas as pd
pd.options.display.float_format = '{:.5f}'.format
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.axes_grid1 import make_axes_locatable
from scipy.interpolate import UnivariateSpline
from itertools import islice

# geoprocessing libraries
import fiona
from fiona.crs import from_epsg
import pyproj
import geopandas as gpd
from shapely.ops import transform
from shapely.geometry import mapping, Point, Polygon

# We also need two specialized NPS libaries: `soundDB` and `iyore`
# we expect them in the same directory as this repository
try:
    sys.path.append(os.path.join(os.path.dirname(os.getcwd()), "soundDB"))
    from soundDB import *

except ModuleNotFoundError:
    print("Can't find library `soundDB`, please clone the repository from https://github.com/gjoseph92/soundDB to",
          os.path.dirname(os.getcwd()))

try:
    sys.path.append(os.path.join(os.path.dirname(os.getcwd()), "iyore"))
    import iyore
    
except ModuleNotFoundError:
    print("Can't find library `iyore`, please clone the repository from https://github.com/nationalparkservice/iyore to",
          os.path.dirname(os.getcwd()), "or install using pip")


# ============ Set up a few paths and connections ===============

# DENA RDS computer
RDS = r"\\inpdenards\overflights"

try:
    sys.path.append(os.path.join(RDS, "scripts"))
    from query_tracks import query_tracks
    
except:
    print("While importing `query_tracks` encountered an error.")

# DENA Render computer (and an iyore dataset)
Render = r"\\inpdenarender\E\Sound Data"
archive = iyore.Dataset(Render)


# ===========================  Define functions  =======================================

def get_utm_zone(longitude):
    
    return (int(1+(longitude+180.0)/6.0))


def climb_angle(v):
    
    """
    compute the 'climb angle' of a vector
    A = 𝑛•𝑏=|𝑛||𝑏|𝑠𝑖𝑛(𝜃)
    """
    
    # a unit normal vector perpendicular to the xy plane
    n = np.array([0,0,1])
    
    degrees = np.degrees(np.arcsin( np.dot(n, v)/(np.linalg.norm(n)*np.linalg.norm(v))))
    return degrees


def point_buffer(lat, lon, km):
    
    wgs84 = pyproj.Proj('epsg:4326')

    # Azimuthal equidistant projection
    aeqd_formatter = '+proj=aeqd +lat_0={lat} +lon_0={lon} +x_0=0 +y_0=0'
    aeqd = pyproj.Proj(aeqd_formatter.format(lat=lat, lon=lon))
    
    # set up two transformation objects
    projector = pyproj.Transformer.from_proj('EPSG:4326', aeqd)
    reprojector = pyproj.Transformer.from_proj(aeqd, 'EPSG:4326')
    
    # project the site coordinate into aeqd
    long_m, lat_m = projector.transform(lat, lon)

    # buffer using a radius in meters
    buf_m = Point(long_m, lat_m).buffer(km * 1000)  # distance in metres

    # convert the polygon from aeqd back into wgs84
    # note that this uses both `shapely` and `pyproj`
    buf = transform(reprojector.transform, buf_m)  # apply projection

    return buf


def create_NMSIM_site_file(project_dir, unit, site, long_utm, lat_utm, height):

    '''
    Create an NMSIM site file for a given NPS monitoring deployment.
    
    Inputs
    ------
    
    project_dir (str): a canonical NMSIM project directory
    unit (str): 4-character NPS Alpha Code, e.g. "BITH", "YUCH"
    site (str): alpha-numeric acoustic monitoring site code, e.g., "002", "TRLA"
    long_utm (float): longitude in meters for the NMSIM project's UTM zone
    lat_utm (float): latitude in meters for the NMSIM project's UTM zone
    height (float): microphone height in meters
    
    Returns
    -------
    None
    
    '''
    
    # the full path to the eventual NMSIM site file
    out_path = project_dir + os.sep + r"Input_Data\05_SITES" + os.sep + unit + site + ".sit"
    
    # open a file and write to it
    with open(out_path, 'w') as site_file:

        site_file.write("    0\n")
        site_file.write("    1\n")
        site_file.write("{0:19.0f}.{1:9.0f}.{2:10.5f} {3:20}\n".format(long_utm, lat_utm, height, unit+site))
        site_file.write(glob.glob(project_dir + os.sep + r"Input_Data\01_ELEVATION\*.flt")[0]+"\n")


def tracks_within(ds, site, year, search_within_km = 20, climb_ang_max = 20, aircraft_specs=False, clip=False, NMSIM_proj_dir=None):
    
    '''
    AN EVENTUAL DOCSTRING HERE
    '''

    unit = "DENA" # it always will be for this tool

    # set up the output folders
    if(NMSIM_proj_dir is not None):

        # check that the folder for NMSIM .trj outputs exists, if not make it
        trj_out = NMSIM_proj_dir + os.sep + r"Input_Data\03_TRAJECTORY"
        if not os.path.exists(trj_out):
            os.makedirs(trj_out)

        # check that the folder for NMSIM .trj outputs exists, if not make it
        sit_out = NMSIM_proj_dir + os.sep + r"Input_Data\05_SITES"
        if not os.path.exists(sit_out):
            os.makedirs(sit_out)
            
    else:

        # a path to the site's computational outputs folder
        cOut = [e.path for e in ds.dataDir(unit=unit, site=site, year=year)][0] + \
                os.sep + r"02 ANALYSIS\Computational Outputs"

        # make a folder for NMSIM .trj outputs
        trj_out = cOut + os.sep + "NMSIM_trj"
        if not os.path.exists(trj_out):
            os.makedirs(trj_out)

        # make a folder for NMSIM .sit outputs
        sit_out = cOut + os.sep + "NMSIM_sit"
        if not os.path.exists(trj_out):
            os.makedirs(trj_out)
    
    # ===== first part; site coordinate wrangling =====================
    
    # load the metadata sheet
    metadata = pd.read_csv(r"\\inpdenafiles\sound\Complete_Metadata_AKR_2001-2020.txt", 
                           delimiter="\t", encoding = "ISO-8859-1")

    # look up the site's coordinates in WGS84
    lat_in, long_in = metadata.loc[(metadata["code"] == site)&(metadata["year"] == year), "lat":"long"].values[0]

    # lookup the UTM zone using the first point
    zone = get_utm_zone(long_in)

    # epsg codes for Alaskan UTM zones
    epsg_lookup = {1:'epsg:26901', 2:'epsg:26902', 3:'epsg:26903', 4:'epsg:26904', 5:'epsg:26905', 
                   6:'epsg:26906', 7:'epsg:26907', 8:'epsg:26908', 9:'epsg:26909', 10:'epsg:26910'}

    # convert from D.d (WGS84) to meters (NAD83)
    projector = pyproj.Transformer.from_crs('epsg:4326', epsg_lookup[zone])

    # convert into NMSIM's coordinate system
    long, lat = projector.transform(lat_in, long_in)

    # ===== second part; mic height to feet, write NMSIM .sit file =====================

    # look up the site's coordinates in WGS84
    height = metadata.loc[(metadata["code"] == site)&(metadata["year"] == year), "microphone_height"].values[0]

    print(unit+site+str(year)+":", "{0:.0f},".format(long), "{0:.0f}".format(lat), "- UTM zone", zone)
    print("\tmicrophone height", "{0:.2f} feet.".format(height*3.28084))

    # now write the microphone's position to an NMSIM .sit file
    create_NMSIM_site_file(NMSIM_proj_dir, unit, site, long, lat, height)


    # ===== third part; save mask file using the buffer radius of choice ===============

    # create the buffer polygon
    buf = point_buffer(lat_in, long_in, search_within_km)  

    # Define a polygon feature geometry with one attribute
    schema = {'geometry': 'Polygon', 'properties': {'id': 'int'},}

    # where should the buffer be saved?
    buffer_path = os.path.join(os.getcwd(), "site_buf.shp")

    # write a new shapefile with the buffered polygon
    with fiona.open(buffer_path, 'w', 'ESRI Shapefile', schema, crs=from_epsg(4326)) as c:
        
        ## If there are multiple geometries, put the "for" loop here
        c.write({'geometry': mapping(buf),'properties': {'id': 0},})

    print("\n\tShapefile containing " + str(search_within_km)+"km radius buffer has been written!")
    
    # plot the buffer within the park boundary
    DENA_outline_path = r"T:\ResMgmt\WAGS\Sound\GIS\Denali\DENA_outline.shp"
    gpd_buffer = gpd.read_file(buffer_path)
    gpd_DENA = gpd.read_file(DENA_outline_path)
    base = gpd_buffer.plot(color='white', edgecolor='black', aspect=0.5)
    #base.set_aspect(2)
    plt.show()
    

    # ===== fourth part; determine the date range of NVSPL files ===============

    # load the datetime of every NVSPL file
    NVSPL_dts = pd.Series([dt.datetime(year=int(e.year),
                                       month=int(e.month),
                                       day=int(e.day),
                                       hour=int(e.hour),
                                       minute=0,
                                       second=0) for e in ds.nvspl(unit=unit, site=site, year=year)])

    # everything should be in chronological order, but just in case...
    NVSPL_dts.sort_values(inplace=True, ascending=True)

    # retrieve the start/end bounds and convert back to YYYY-MM-DD strings
    start, end = (dt.datetime.strftime(d, "%Y-%m-%d") for d in [NVSPL_dts.iloc[0], NVSPL_dts.iloc[-1]])
    print("\n\tRecord begins", start, "and ends", end, "\n")
    
    # # load tracks from the database over a certain daterange, using the buffered site
    # tracks = query_tracks(connection_txt=os.path.join(RDS, "config\connection_info.txt"), 
    #                       start_date=start, end_date=end, 
    #                       mask=gpd_buffer, clip_output=clip,
    #                       aircraft_info=aircraft_specs)

    # load tracks from the database over a certain daterange, using the buffered site
    tracks = query_tracks(connection_txt=os.path.join(RDS, "config\connection_info.txt"), 
                          start_date=start, end_date=end, 
                          clip_output=clip,
                          aircraft_info=aircraft_specs)
    
    # make a dataframe to hold distances and times
    closest_approaches = pd.DataFrame([], index=np.unique(tracks["id"]), columns=["closest_distance", "closest_time"])
    
    # process each unique flight track in sequence
    for f_id, data in tracks.groupby("flight_id"):
        
        if(len(data) > 1): # "one point does not a trajectory make"
        
            # double check that the data are sorted by time
            data = data.sort_values("ak_datetime")

            # convert the GPS points from wgs84 to the correct UTM zone for the NMSIM elevation file
            long_utm, lat_utm = projector.transform(data["latitude"].values, data["longitude"].values)

            # assign back into the dataframe for subsequent use
            data.loc[:, "long_UTM"] = long_utm
            data.loc[:, "lat_UTM"] = lat_utm

            # coordinates of each point
            coords = np.array([[lo, la, e] for lo, la, e in zip(data["long_UTM"], 
                                                                data["lat_UTM"], 
                                                                0.3048*data["altitude_ft"])])

            # convert the coordinates to vectors
            V = np.diff(coords, axis=0)

            # compute the climb angle for each point: 
            climb_angs = np.array([climb_angle(V[n]) for n in np.arange(len(V))])

            # if the climb angle is greater than 20° something strange is going on: reset to zero
            climb_angs[np.abs(climb_angs) > climb_ang_max] = 0

            # we don't know what the last point's angle should be, but NMSIM requires a value
            # just repeat the penultimate point's value
            climb_angs = np.append(climb_angs, climb_angs[-1])

            # assign the climb angles to the array
            data["ClimbAngle"] = climb_angs

            # NMSIM probably won't like nan... replace those with zero as well
            data["ClimbAngle"].fillna(0, inplace=True)

            # this is the start time of the track
            start = data["ak_datetime"].iloc[0]

            # truncate starting time to nearest hour to check against the NVSPL list
            check = start.replace(minute=0, second=0)

            # 1 if there is a match, 0 if not
            match_bool = NVSPL_dts.apply(lambda date: date in [check]).sum()

            if(match_bool == 0):

                tracks = tracks[tracks["flight_id"] != f_id]
                print("\t\t", "Flight starting", start, "has no matching acoustic record")

            elif(match_bool == 1):

                # find the time at which the flight passes closest to the station
                site_coords = np.array([long, lat])
                GPSpoints_xy = np.array([data["long_UTM"], data["lat_UTM"]])

                # which point made the closest approach to the site?
                min_distance = np.min(np.linalg.norm(site_coords - GPSpoints_xy.T, axis=1))/1000

                # keep track of the closest approach by id
                closest_approaches.loc[data["flight_id"].iloc[0], "closest_distance"] = min_distance

                # at what time did the closest approach occur?
                closest_time = data.iloc[np.argmin(np.linalg.norm(site_coords - GPSpoints_xy.T, axis=1))]['ak_datetime']

                # likewise keep track of the closest time
                closest_approaches.loc[data["flight_id"].iloc[0], "closest_time"] = closest_time

                print("\t\t", "#"+str(f_id), "expected closest at", closest_time, "{0:0.1f}km".format(min_distance))

                # create a time-elapsed column
                data["time_elapsed"] = (data["ak_datetime"] - data["ak_datetime"].min()).apply(lambda t: t.total_seconds())

                # we'll only save the trajectory if it's within the specified search radius!
                if(min_distance <= search_within_km):

                    # ======= densify the GPS points for NMSIM ========

                    print("\n\t\t\t", "Flight is within search distance. Attempting to densify", 
                          data.shape[0], "points...")

                    new_points = gpd.GeoDataFrame([])
                    for row in data.itertuples():

                        try:

                            next_ind = data.index[np.argwhere(data.index == row.Index)+1][0][0]

                            # this represents time steps < 1 second
                            interpSteps = int(1.1*(data.loc[next_ind, "ak_datetime"] - row.ak_datetime).total_seconds())
                            print("trying for", interpSteps, "steps between points")

                            # interpolate the indices, longitudes, latitudes, and altitudes
                            # we don't need the first or last values - they're already in the dataframe
                            indi = np.linspace(row.Index, next_ind, interpSteps)[1:-1]
                            ti = np.linspace(row.time_elapsed, data.loc[next_ind, "time_elapsed"], interpSteps)[1:-1]
                            xi = np.linspace(row.longitude, data.loc[next_ind, "longitude"], interpSteps)[1:-1]
                            yi = np.linspace(row.latitude, data.loc[next_ind, "latitude"], interpSteps)[1:-1]
                            zi = np.linspace(row.altitude_ft, data.loc[next_ind, "altitude_ft"], interpSteps)[1:-1]
                            utm_xi = np.linspace(row.long_UTM, data.loc[next_ind, "long_UTM"], interpSteps)[1:-1]
                            utm_yi = np.linspace(row.lat_UTM, data.loc[next_ind, "lat_UTM"], interpSteps)[1:-1]
                            cai = np.linspace(row.ClimbAngle, data.loc[next_ind, "ClimbAngle"], interpSteps)[1:-1]
                            hi = np.linspace(row.heading, data.loc[next_ind, "heading"], interpSteps)[1:-1]
                            vi = np.linspace(row.knots, data.loc[next_ind, "knots"], interpSteps)[1:-1]

                            # generate geometry objects for each new interpolated point
                            gi = [Point(xyz) for xyz in zip(xi, yi, zi)]

                            # create a dictionary of the interpolated values to their column
                            d = {'time_elapsed': ti,
                                 'longitude': xi, 
                                 'latitude': yi,
                                 'altitude_ft': zi,
                                 'long_UTM': utm_xi,
                                 'lat_UTM': utm_yi,
                                 'ClimbAngle': cai,
                                 'heading': hi,
                                 'knots': vi,
                                 'geom': gi}


                            # turn the newly interpolated values into a GeoDataFrame 
                            rowsi = gpd.GeoDataFrame(d, index=indi, crs="EPSG:4326")

                            # append to the track's overall new points
                            new_points = new_points.append(rowsi)

                        # there is no next index on the last row... pass through
                        except IndexError:
                            pass


                    # append the new points and sort by index (which is also by time)
                    data = data.append(new_points)
                    data = data.sort_index()

                    print("\t\t\t", "...trajectory now has", 
                          data.shape[0], "points!\n")

                    # ======= write the trajectory file! ==============

                    print("\t\t\t", "Densification complete, writing trajectory file...")

                    # add N-number and begin time
                    start_time = dt.datetime.strftime(data["utc_datetime"].min(), "%Y-%m-%d %H:%M:%S")
                    file_name_dt = dt.datetime.strftime(data["utc_datetime"].min(), "_%Y%m%d_%H%M%S")
                    N_number = data["registration"].iloc[0]

                    # path to the specific .trj file to be written
                    trj_path = trj_out + os.sep + str(N_number) + str(file_name_dt) + ".trj"

                    with open(trj_path, 'w') as trajectory:

                        # write the header information
                        trajectory.write("Flight track trajectory variable description:\n")
                        trajectory.write(" time - time in seconds from the reference time\n")
                        trajectory.write(" Xpos - x coordinate (UTM)\n")
                        trajectory.write(" Ypos - y coordinate (UTM)\n")
                        trajectory.write(" UTM Zone  "+str(zone)+"\n")
                        trajectory.write(" Zpos - z coordinate in meters MSL\n")
                        trajectory.write(" heading - aircraft compass bearing in degrees\n")
                        trajectory.write(" climbANG - aircraft climb angle in degrees\n")
                        trajectory.write(" vel - aircraft velocity in knots\n")
                        trajectory.write(" power - % engine power\n")
                        trajectory.write(" roll - bank angle (right wing down), degrees\n")
                        trajectory.write("FLIGHT " + str(N_number) + " beginning " + start_time +" UTC\n")
                        trajectory.write("TEMP.  59.0\n")
                        trajectory.write("Humid.  70.0\n")
                        trajectory.write("\n")
                        trajectory.write("         time(s)        Xpos           Ypos           Zpos         heading        climbANG       Vel            power          rol\n")

                        # now write the data section row by row
                        for ind, point in data.iterrows():

                            # write the line
                            trajectory.write("{0:15.3f}".format(point["time_elapsed"]) + \
                                             "{0:15.3f}".format(point["long_UTM"]) + \
                                             "{0:15.3f}".format(point["lat_UTM"]) + \
                                             "{0:15.3f}".format(0.3048*point["altitude_ft"]) + \
                                             "{0:15.3f}".format(point["heading"]) + \
                                             "{0:15.3f}".format(point["ClimbAngle"]) + \
                                             "{0:15.3f}".format(point["knots"]) + \
                                             "{0:15.3f}".format(95) + \
                                             "{0:15.3f}".format(0) + "\n")

                        print("\t\t\t...finished writing .trj", "\n")
                        print("-----------------------------------------------------------------------------------------")

                
                # (closes `if` from line 253) the flight was not within the search radius...
                else:
                    tracks = tracks[tracks["flight_id"] != f_id] # ...drop the flight ID from the table
                    print("\t\t", "Flight starting", start, "was not within the search radius.")
    
    print(tracks.size)
    if(tracks.shape[0] <= 1):
        
        print("\nSorry, no tracks in the database coincide with this deployment.")
        
        tracks = gpd.GeoDataFrame([], columns=tracks.columns) # return an empty geodataframe with the original columns
        return tracks
    
    elif(tracks.shape[0] > 1):
        
        u = np.unique(tracks["id"])
        print("\nThere are", len(u), "tracks in the database which coincide with this deployment.")
        print("Identification numbers:", u)
        
        # iterate through each id number and add the closest approach information
        for track_id, flight in closest_approaches.iterrows():
            
            tracks.loc[tracks["flight_id"] == track_id, "closest_time"] = flight["closest_time"]
            tracks.loc[tracks["flight_id"] == track_id, "closest_distance"] = flight["closest_distance"]
        
        return tracks
    
    
def NMSIM_create_tis(project_dir, source_path, Nnumber=None, NMSIMpath=None):
    
    '''
    Create a site-based model run (.tis) using the NMSIM batch processor.
    
    Inputs
    ------
    
    Returns
    -------
    
    None
    
    '''
    
    # ======= (1) define obvious, one-to-one project files ================
    
    elev_file = project_dir + os.sep + r"Input_Data\01_ELEVATION" + os.sep + "elevation.flt"
    
    # imped_file = project_dir + os.sep + "Input_Data\01_IMPEDANCE" + os.sep + "landcover.flt"
    imped_file = None

    trj_files = glob.glob(project_dir + os.sep + r"Input_Data\03_TRAJECTORY\*.trj")

    # eventually the batch file is going to want this
    tis_out_dir = project_dir + os.sep + r"Output_Data\TIG_TIS"
    
    # ======= (2) define less obvious project files - these still need thought! ================
    
    # site files need some thinking through... there COULD be more than one per study area
    # (it's quite project dependant)
    site_file = glob.glob(project_dir + os.sep + r"Input_Data\05_SITES\*.sit")[0]
    
    # strip out the FAA registration number
    registrations = [t.split("_")[-3][11:] for t in trj_files]

    # the .tis name preserves: reciever + source + time (roughly 'source : path : reciever')
    site_prefix = os.path.basename(site_file)[:-4]

    tis_files = [tis_out_dir + os.sep + site_prefix + "_" + os.path.basename(t)[:-4] for t in trj_files]

    trajectories = pd.DataFrame([registrations, trj_files, tis_files], index=["N_Number","TRJ_Path","TIS_Path"]).T
    
    # ======= (3) write the control + batch files for command line control of NMSIM ================
        
    # set up the two files we want to write
    control_file = project_dir + os.sep + "control.nms"
    batch_file = project_dir + os.sep + "batch.txt"
    
    # select the trajectories to process
    if(Nnumber == None):

        trj_to_process = trajectories
    
    else:

        trj_to_process = trajectories.loc[trajectories["N_Number"] == Nnumber, :]
    
    
    if(NMSIMpath == None):
        
        # assume that the project folder is in "..\NMSIM_2014\Data"
        # and look for Nord2000batch.exe two directories up
        Nord = os.path.dirname(os.path.dirname(project_dir)) + os.sep + "Nord2000batch.exe"
        
    else:
        
        Nord = NMSIMpath

    for meta, flight in trj_to_process.iterrows():
    

        # write the control file for this situation
        with open(control_file, 'w') as nms:

            nms.write(elev_file+"\n") # elevation path
            
            if(imped_file != None):
                nms.write(imped_file+"\n") # impedance path
            else:
                nms.write("-\n")
                
            nms.write(site_file+"\n") # site path
            nms.write(flight["TRJ_Path"]+"\n")
            nms.write("-\n")
            nms.write("-\n")
            nms.write(source_path+"\n")
            nms.write("{0:11.4f}   \n".format(500.0000))
            nms.write("-\n")
            nms.write("-")    

        # write the batch file to create a site-based analysis
        with open(batch_file, 'w') as batch:

            batch.write("open\n")
            batch.write(control_file+"\n")
            batch.write("site\n")
            batch.write(flight["TIS_Path"]+"\n")
            batch.write("dbf: no\n")
            batch.write("hrs: 0\n")
            batch.write("min: 0\n")
            batch.write("sec: 0.0")
        
        # ======= (4) compute the theoretically observed trace on the site's microphone ================
        
        print(flight["TRJ_Path"]+"\n")
        
        process = subprocess.Popen([Nord, batch_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = process.communicate()

        output_messages = stdout.decode("utf-8").split("\r\n")
        output_messages = [ out for out in output_messages if out.strip() != '' ]
        
        print("\tthe following lines are directly from NMSIM:")
        for s in output_messages+["\n"]:
            print("\t"+s)

        # slightly messier printing for error messages
        if(stderr != None):
            for s in sterr.decode("utf-8").split("\r\n"):
                print(s.strip()) 
                

def pair_trj_to_tis_results(project_dir):
    
    '''
    Join a directory of .tis results created by NMSIM
      to the .trj files that created them.
      
    Inputs
    ------
    project_dir (str): the path to a canonical NPS-style NMSIM project directory
    
    Returns
    -------
    iterator (zip object): an iterator containing the paired .tis and .trj file paths
    
    '''
    
    # find all the '.tis' files
    successful_tis = glob.glob(project_dir + os.sep + "Output_Data\TIG_TIS\*.tis")

    # find all the '.trj' files
    trajectories = [project_dir + os.sep + "Input_Data\\03_TRAJECTORY" + \
                    os.sep + os.path.basename(f)[9:-4] + ".trj" for f in successful_tis]
    
    iterator = zip(trajectories, successful_tis)
    
    return iterator


def tis_resampler(tis_path, dt_start, utc_offset=-8):
    
    '''
    '''
    
    # read the data line-by-line
    with open(tis_path) as f:

        content = list(islice(f, 18 + (3600*24)))
    
    
    # find the line index where the header ends
    splitBegin = content.index('---End File Header---\n')

    # take out the whitespace and two empty columns at either end
    spectral_data = [re.split(r'\s+',c) for c in content[splitBegin+10:]] 
    spectral_data = [d[1:-2] for d in spectral_data]      
    
    # initalize a pandas dataframe using the raw spectral data and the expected column headers
    tis = pd.DataFrame(spectral_data, columns=["SP#","TIME","F","A","10", "12.5","15.8","20","25","31.5","40","50","63",
                                                "80","100","125","160","200","250","315","400","500","630","800","1000",
                                                "1250","1600","2000","2500","3150","4000","5000","6300","8000","10000",
                                                "12500"], dtype='float') #,"20000"

    # there's a weird text line at the end of the file (is this true for all .tis files?)
    tis.drop(tis.tail(1).index,inplace=True) # drop last n rows

    # these columns are stubborn
    tis["TIME"] = tis["TIME"].astype('float')
    tis["SP#"] = tis["SP#"].astype('float').apply(lambda f: int(f))
    tis["F"] = tis["F"].astype('int')

    # convert relevant columns to decibels (dB) from centibels (cB)
    tis.loc[:,'A':'12500'] *= 0.1

    # timedelta to adjust to local time
    utc_offset = dt.timedelta(hours=utc_offset) 

    # reindex the dataframe to AKT
    tis.index = tis["TIME"].astype('float').apply(lambda t: dt_start + dt.timedelta(seconds=t) + utc_offset)

    # resample to match NVSPL time resolution
    clean_tis = tis.sort_index().resample('1S').quantile(0.5)
    
    return clean_tis


def NVSPL_to_match_tis(ds, project_dir, startdate, clean_tis, trj, unit, site, year, utc_offset=-8, pad_length=5):
    
    '''
    '''
    
    # timedelta to adjust to local time
    utc_offset = dt.timedelta(hours=utc_offset) 
    
    # convert startdate to Alaska Time
    ak_start = startdate + utc_offset
    print("Alaska start time", ak_start)
    
    # tidy up the TIS spectrogram by converting np.nan to -99.9
    clean_tis.fillna(-99.9).values.T
    
    # we can only compare 1/3rd octave bands down to 12.5 Hz... drop the rest
    clean_tis = clean_tis.loc[:, ~clean_tis.columns.isin(["SP#", "TIME", "F", "A", "10"])]

    # load NVSPL for the day of the event
    nv = nvspl(ds,
               unit=unit,
               site=site,
               year=ak_start.year,
               month=str(ak_start.month).zfill(2),
               day=str(ak_start.day).zfill(2),
               hour=[str(h).zfill(2) for h in np.unique(clean_tis.index.hour.values)],
               columns=["H"+s.replace(".", "p") for s in clean_tis.columns]).combine()

    # if multiple hours, drop the heirarchical index
    if isinstance(nv.index, pd.MultiIndex):
        nv.index = nv.index.droplevel(0)

    # select the SPL data that corresponds 
    pad = dt.timedelta(minutes=pad_length)
    
    # find the NVSPL data the specifically corresponds to the timing of the model
    event_SPL = nv.loc[clean_tis.index[0]-pad : clean_tis.index[-1]+pad,:]
    
    print("NVSPL shape:", event_SPL.shape)

    # pad the theoretical data as well
    spect_pad = np.full((int(pad.total_seconds()), clean_tis.shape[1]), -99.9)
    theoretical = np.vstack((spect_pad, clean_tis))

    print("NMSIM shape:", theoretical.shape)
    
    fig, ax = plt.subplots(nrows=2, ncols=1, figsize=(18,5), sharex=True)
    
    # convert the NVSPL's nice datetime axis to numbers
    x_lims = mdates.date2num(event_SPL.index)
    
    ax[0].set_title("NMISIM results", loc="left")
    ax[0].imshow(theoretical.T, aspect='auto', origin='lower', 
                 extent=[x_lims[0], x_lims[-1], 0, event_SPL.shape[1]],
                 cmap='plasma', interpolation=None, vmin=-10, vmax=80, zorder=-5)

    ax[0].set_yticks(np.arange(event_SPL.shape[1])[::4])
    ax[0].set_yticklabels(event_SPL.columns.astype('float')[::4])
    
    # tell matplotlib that the numeric axis should be formatted as dates
    ax[0].xaxis_date()
    ax[0].xaxis.set_major_formatter(mdates.DateFormatter("%b-%d\n%H:%M")) # tidy them!
    
    ax[1].set_title("microphone measurement at "+unit+site, loc="left")
    im = ax[1].imshow(event_SPL.T, aspect='auto', origin='lower', 
                      extent=[x_lims[0], x_lims[-1], 0, event_SPL.shape[1]],
                      cmap='plasma', interpolation=None, vmin=-10, vmax=80)
    
    # the same as for the first plot
    ax[1].set_yticks(np.arange(event_SPL.shape[1])[::4])
    ax[1].set_yticklabels(event_SPL.columns.astype('float')[::4])
    ax[1].xaxis_date()
    ax[1].xaxis.set_major_formatter(mdates.DateFormatter("%b-%d\n%H:%M")) # tidy them!

    fig.colorbar(im, ax=ax.ravel().tolist(), anchor=(2.2, 0.0))
    fig.text(1.06, 0.5, "Sound Level (Leq, 1s)", va='center', rotation='vertical', fontsize=10)
    fig.text(-0.02, 0.55, "Frequency Band (Hz)", va='center', rotation='vertical', fontsize=13)
    
    title = os.path.basename(trj)[:-4]
    
    plt.suptitle(title, y=1.05, fontsize=17, ha="center")

    fig.tight_layout()

    plt.savefig(project_dir + os.sep + r"Output_Data\IMAGES" + os.sep + title + "_comparison.png", dpi=300, bbox_inches="tight")
    plt.show()
    
    return event_SPL