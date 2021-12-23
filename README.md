# NMSIM-Python
A Python-based wrapper for Noise Model Simulation (NMSIM). Eases the creation of input files and joining data from GIS databases. Improves overall flexibility of the tool for diverse applications.

<!-- MarkdownTOC autolink=true depth=3 bracket=round -->

- [Purpose](##Purpose)
- [Files Associated With NMSIM](##Files-Associated-With-NMSIM)
  - [User-Provided Inputs](###User-Provided-Inputs)
  - [Intermediary Inputs](###Intermediary-Inputs-[as-facilitated-by-this-library)
  - [Outputs](###Outputs)
- [Site-Based Paradigm Example](##Site-Based-Paradigm-Example)
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

This repository provides a scripting toolkit for the development of acoustic propagation models with [Noise Model Simulation (NMSIM) software](https://www.blueridgeresearch.com/noise-models). At request of the National Park Service, NMSIM was updated in 2014 to use the [Nord2000 propagation algorithm](https://forcetechnology.com/en/innovation/completed-projects/nord2000-noise-calculation-method-auralisation), *"an advanced ray-tracing noise model that includes refraction by the atmosphere and diffraction around terrain."* The motivating factor of this current work is to sidestep NMSIM's arcane Graphical User Interface (GUI) while continuing to leverage Nord2000's extensive functionality, [standardization](https://www.iso.org/standard/20649.html), speed, and physical accuracy.

The eventual goal of `NMSIM-Python` is to provide an overarching `NMSIM` class corresponding to the **Control File** (see Figure 1, *.nms*) within which the parameters for a model scenario are described. Inter-related modelling scenarios could then be implemented gracefully with a `NMSIM` object. By a series of minor modifications, a specific sequence of predictions could be generated. Such a tool would enable iteration over whichever dimension(s) of a civic problem are in question (e.g., properties of the noise source, trajectory, reciever location, etc...) Such focus could greatly expedite mitigation work, ground-truthing or experiments in perception. 

For now, though, this repository exists only as:

>a set of loosely-connected python modules <br>
>a few select `Jupyter` notebooks <br>
>an `arcpy` toolbox meant for use with ArcGIS Pro <br>

You can think of `NMSIM-Python` as an “exploded view” of the modelling process, with functions to actualize each *input*, *intermediary*, or *output* filetype used by the software (Figure 1). Current design favors scripters working in a project-driven, maximally-flexible environment. The `Jupyter` notebooks demonstrate this style of flexible use *[note: they are only truly functional for National Park Service employees due to data-sharing issues. Please contact me if you would like to try them - I can figure out how to send you the appropriate data.]* For a deeper dive, interested readers are directed towards [Kirby Heck's work with `DENA-overflights`](https://github.com/dbetchkal/DENA-overflights) as a rich example of `NMSIM-Python` in use. 

<img src=https://github.com/dbetchkal/NMSIM-Python/blob/main/static/2021%2012%2022%20NMSIM-Python_flow.png  align=center width=700></img><br>
*Figure 1.) An "exploded view" the NMSIM modelling process as an information flow graph. The fundemental architecture is coded blue. Useful output types are encoded in amber, their respective raw NMSIM outputs in yellow, and input or intermediary file types in beige. Jupyter notebooks are green. Arcpy toolboxes are red.*

True batching (i.e., flexible compilation of batch files) should also be implemented, but currently isn’t. Batching isn’t purposeful for models containing sequences of isolated events, but as soon as overlapping events feature in a simulation batching *is required.* However, a batching routine would subsume the `NMSIM` Class, so writing it will have to wait until the class is available first!

Another (quite different) purpose involves records retention for models used in planning or compliance processes. It would be ideal to allow public models to be publicly available along with the documents where they feature prominently. Presumably this suggests that model objects should be able to be stored in memory for future reuse (i.e., as a `pickle` or other filetype).

Note: `NMSIM-Python` is a library in active development and therefore should be considered an unstable tool. For the same reason it would greatly benefit from the contributions of open-source programmers. It could also benefit from curious physicists/geographers/ecologists who have an interest in software testing and application.

---

## Files Associated With NMSIM

NMSIM models represent three coupled systems: 

>the geographic landscape and atmosphere represent a channel within which sound propagates<br>
>away from sound sources (which may or may not be in motion)<br>
>and the sound waves eventually arrive at various locations (where an observer may or may not be present)

Considering the [multiphysics](https://en.wikipedia.org/wiki/Multiphysics) involved - and also considering the RAM-limited era that NMSIM was originally developed in - there are lots of files required to operate the software. This section attempts to provide a brief list of every file type shown in Figure 1. Such knowledge is key to scripting in `NMSIM-Python` as well as understanding limitations of the toolkit.

### User-Provided Inputs
-	**NPS Unit Information**: the 4-letter alpha code for the park unit in question can provide a quick reference for looking up larger rasters. It also provides a handy lookup for administrative metadata used in automatic labelling/titles/filenames.
- **Site metadata**: microphone/observer coordinates (WGS84), microphone/observer height (meters).
-	**Study Area polygon** (*.shp*) usually rectangular, but can be any shape.
-	**Sound source data** represented in the form of one-to-many sound hemispheres (.avg) and their operational metadata (.src) mapped along a control [read: ‘power’] parameter. 
-	**Elevation rasters** (16-bit *.tif*) large regional-scale rasters clipped to within 20 km of park boundaries.
- ~~**Impedance raster** (16-bit .tif)~~ *not implemented!*
-	*OPTIONAL* **GPS points** for creation of flight (or ground) trajectories. The alternative is to use NMSIM’s built-in `FlightTrackBuilder.exe` module, which is geometrically arcane (and therefore extremely tedious.)
 
### Intermediary Inputs [as facilitated by this library]
-	**Standardized project directory** (or a blank project directory).
-	**Focused elevation raster** (*.flt*, but also importantly *.tif*) clipped from wider extent. The grid float file (*.flt*) will be ingested by NMSIM. The geotiff raster (*.tif*) is used in scenarios where external GPS data or other covariates are included in the model. Regardless, it is always created for mapping convenience.
- ~~**Focused impedance raster** (.flt)~~ *not implemented!*
-	**Trajectory** [read: ‘source positions'] (*.trj*) which can be from a previously-constructed file or generated from GPS coordinates + elevation raster.
-	**Site file** [read: ‘receiver’] (*.sit*) microphone/observer position from coordinates and height.
-	**Source files** [read: ‘source’ acoustic properties] (*.avg*, *.src*) hemispherical spectral sources and their associated metadata. NOTE: ISN'T SHOWN ON FIGURE 1.
-	**Control file** (*.nms*) which integrates all NMSIM inputs.
-	**Batch file** (*.txt*) which allows the model to be run from the Command Line Interface (CLI) program.
-	*OPTIONAL* **Weather file** (*.wea*) overrides the standard weather parameters prescribed by [ISO 9613-2:1996](https://www.iso.org/standard/20649.html) which is useful for studying inversions, wind shear, turbulence or other atmospheric effects.

### Outputs
-	**Site-based Model** [read: 3D spectrogram representation] (*.tis*) resulting from control file. One use of these data could be time-aligning model spectrograms with GPS data or acoustic measurements. Further description is outside of the scope of this README, but site-based models provide a much-needed recourse for the validation of field studies or compliance efforts.

-	**Grid-based Model** [read: 4D spectral raster representation] (*.tig*) resulting from control file. Reducing the dimensionality of the 4D spectral raster into a 2D metric raster is required for mapping (or basically any) purpose. Dimensionality reduction is identical to summarizing any one-third octave band acoustic time-series record with a simpler metric. 

---

## Site-Based Paradigm Example

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
