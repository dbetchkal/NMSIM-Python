# NMSIM-Python
A Python-based wrapper for Noise Model Simulation (NMSIM). Eases the creation of input files and joining data from GIS databases. Improves overall flexibility of the tool for diverse applications.

<!-- MarkdownTOC autolink=true depth=3 bracket=round -->

- [Purpose](##Purpose)
- [Files Associated With NMSIM](##Files-Associated-With-NMSIM)
  - [User-Provided Inputs](###User-Provided-Inputs)
  - [Intermediary Inputs](###Intermediary-Inputs-[as-facilitated-by-this-library)
  - [Outputs](###Outputs)
- [Example: Site-Based Paradigm](##Example:-Site-Based-Paradigm)
  - [1. Initialize an NMSIM project from study area](###1-initialize)
  - [2. Create a site file (.sit) from metadata](###2-reciever)
  - [3. Create flight trajectory (.trj) from the overflights database](###3-path)
  - [4. Compile model to create site-specific analysis (.tis)](###4-putting-it-all-together)
  - [5. Review the results by comparing to acoustic measurements](###5-comparing-theory-to-obs)
- [Public domain](##public-domain)

<!-- /MarkdownTOC -->

## Purpose

>“The Purpose of a System is What it Does.”
>-- Stafford Beer

This repository provides a scripting framework for the development of acoustic propagation models using Blue Ridge Research and Consulting's Noise Model Simulation (NMSIM) software. NMSIM is a ray-based acoustic propagation model based on a source-path-reciever paradigm. The motivating factor of this work was to sidestep the tedium of the software’s arcane Graphical User Interface (GUI) while leveraging use of the software’s speed, physical accuracy, and standardization.

The eventual goal of `NMSIM-Python` is to provide an overarching `NMSIM` class corresponding with the Control File (.nms), within which the parameters for a model scenario are described. Inter-related modelling scenarios could be implemented gracefully with an `NMSIM` object. By a series of minor modifications, a rapid sequence of predictions could be generated. Such a tool would enable subtle iteration over dimensions of the civic problem which are variable (e.g., properties of the noise source, trajectory, reciever location, etc...). 

For now, though, this repository exists only as a set of loosely-connected modules, a few select `Jupyter` notebooks, and an `arcpy` toolbox. (For a deeper dive, interested readers are directed towards [Kirby Heck's work with `DENA-overflights`](https://github.com/dbetchkal/DENA-overflights) as a rich example of `NMSIM-Python` in use.) As it stands, you can think of `NMSIM-Python` collectively as an “exploded view” of the modelling process, with functions for each *input*, *transduction*, or *output* of file type used by the GUI (Figure 1). Use is currently geared towards scripters working in a project-driven, maximally-flexible environment. The `Jupyter` notebooks demonstrate this style of flexible use [note: they are only truly functional for Department of the Interior employees due to data-sharing issues. Please contact me if you would like to try them - I can figure out how to send you the appropriate data.] 

<img src=https://github.com/dbetchkal/NMSIM-Python/blob/main/static/2021%2012%2022%20NMSIM-Python_flow.png  align=center width=700></img><br>
*Figure 1.) An "exploded view" the NMSIM modelling process as an information flow graph. The fundemental architecture is coded blue. Useful output types are encoded in amber, their respective raw NMSIM outputs in yellow, and input or intermediary file types in beige. Jupyter notebooks are green. Arcpy toolboxes are red.*

True batching (i.e., with the Batch File) should also be implemented, but currently isn’t. Batching isn’t purposeful for models containing sequences of isolated events, but as soon as overlapping events feature in a simulation batching is required. Because a batching routine would subsume the `NMSIM` Class, writing it will have to wait until the class is available first!

Another (quite different) purpose is appropriate records retention for models used in planning or compliance processes. It would be ideal to allow public models to be publicly available along with the documents where they feature prominently. Presumably this suggests that model objects should be able to be stored in memory for future reuse (i.e., as a `pickle` or other filetype).

Note: `NMSIM-Python` is a library in active development and therefore should be considered an unstable tool. For the same reason it is would also greatly benefit from the contributions of open-source programmers or curious physicists/geographers/ecologist with a taste for software testing.

---

## Files Associated With NMSIM

NMSIM represents a tripartite coupling of systems: the geographic landscape provides the space for sound to spread out away from sound sources (which may or may not be in motion) and arrive at various locations (where an observer may or may not be present). On account of this - and also considering the RAM-limited era that NMSIM was originally developed in - there are lots of files involved. Understanding them is key to the conceptualization of `NMSIM-Python` and also a survey of it's limitations. This section attempts to provide a brief list of every file type shown in Figure 1:

### User-Provided Inputs
- **Site metadata**: coordinates (WGS84), microphone height (m)
-	**Study Area polygon** (.shp)
-	**Sound source data** represented in the form of one-to-many sound hemispheres (.avg) and their operational metadata (.src) mapped along a control [read: ‘power’] parameter. 
-	**Elevation rasters** (16-bit .tif)
~~-	**Impedance raster** (16-bit .tif)~~ *not implemented!*
-	*OPTIONAL* **GPS points** for creation of flight (or ground) trajectories. The alternative is to use NMSIM’s built-in `FlightTrackBuilder.exe` module, which is geometrically arcane (and therefore extremely tedious.)

### Intermediary Inputs [as facilitated by this library]
-	**Standardized project directory** (or a blank project directory).
-	**Site files** [read: ‘receiver’] (.sit) from coordinates.
-	**Focused elevation raster** (.flt, but also importantly .tif) clipped from wider extent. The grid float file (.flt) will be ingested by NMSIM. The geotiff raster (.tif) is used in scenarios where external GPS data or other covariates are included in the model. Regardless, it is always created for mapping convenience.
~~- **Focused impedance raster** (.flt)~~ *not implemented!*
-	**Control file** (.nms) which integrates all inputs and also provides metaparameters for model visualization in the GUI
-	**Batch file** (.txt) which allows the model to be run from the Command Line Interface (CLI) program.

### Outputs
-	**Site-based Model** [read: 3D spectrogram representation] (.tis) from control file. One use of these data are to time-align model spectrograms with GPS data or acoustic measurements. Further description is outside of the scope of this README, but it represents an obvious experimental need for validation of field studies or compliance efforts.

-	**Grid-based Model** [read: 4D spectral raster representation] (.tig) from control file. Reducing the dimensionality of the 4D spectral raster into a 2D metric raster is required for mapping (or pretty much any) purpose. It is a similar process to summarizing any one-third octave band acoustic record. 


## Example: Site-Based Paradigm

The following section demonstrates use of `NMSIM-Python` to model within a site-based paradigm. In this example there is a single reciever which 'observes' the acoustic morphology of a propeller aircraft as it transits the landscape along a specific trajectory. The model results in a spectrogram (i.e., 2D representation of sound in time and frequency.)



<img src=https://github.com/dbetchkal/NMSIM-Python/blob/pyproj_1p9/static/2020%2010%2022%20NMSIM%20source%20improvement%20schema.png width=700><br> *Figure 2.) NMSIM modelling via a site-based paradigm. Like Figure 1, the process is represented as an information flow graph. User-based inputs are shown as green arrows on the left margin. These lead to intermediary inputs, which are finally organized together into the fundemental NMSIM Control File for this model. In turn, the Control File is referenced by the Batch File, which is ultimately used by NMSIM.* 

### 1. Initialize an NMSIM project from study area
### 2. Create a site file (.sit) from metadata
### 3. Create flight trajectory (.trj) from the overflights database
### 4. Compile model to create site-specific analysis (.tis)
### 5. Review the results by comparing to acoustic measurements




---

## Public domain

This project is in the worldwide [public domain](LICENSE.md). As stated in [CONTRIBUTING](CONTRIBUTING.md):

> This project is in the public domain within the United States,
> and copyright and related rights in the work worldwide are waived through the
> [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).
>
> All contributions to this project will be released under the CC0 dedication.
> By submitting a pull request, you are agreeing to comply with this waiver of copyright interest.
