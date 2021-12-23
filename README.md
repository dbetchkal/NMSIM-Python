# NMSIM-Python
A Python-based wrapper for Noise Model Simulation (NMSIM). Eases the creation of input files and joining data from GIS databases. Improves overall flexibility of the tool for diverse applications.

## Purpose

>“The Purpose of a System is What it Does.”
>-- Stafford Beer

This repository provides a scripting framework for the development of acoustic propagation models using Blue Ridge Research and Consulting's Noise Model Simulation (NMSIM) software. The motivating factor was to sidestep the tedium of the software’s arcane Graphical User Interface (GUI) while retaining use of the software’s speed and physical accuracy.

The eventual goal of `NMSIM-Python` is to provide an overarching `NMSIM` class corresponding with the Control File (.nms). Then interrelated modelling scenarios could be easily implemented by modifying the NMSIM object and recomputing the prediction. It would only be necessary to iterate over parts of the scenario which are variable (e.g., properties of the noise source, trajectory, reciever location, etc...).

For now, though, this repository exists only as a set of loosely-connected modules, a few `Jupyter` notebooks, and an `arcpy` toolbox. As it stands, you can think of `NMSIM-Python` collectively as an “exploded view” of the modelling process, with functions for each *input*, *transduction*, or *output* of file type used by the GUI (Figure 1). The modules contain diverse utility functions for staging and advancing modelling scripts in an *ad hoc*, maximally-flexible environment. The `Jupyter` notebooks demonstrate this style of flexible use [note: they are only truly functional for Department of the Interior employees due to data-sharing issues. Please contact me if you would like to try them and I can see about getting you the data.] 

*True batching (i.e., with the Batch File) should probably also be implemented, but currently isn’t.* Batching isn’t purposeful for models containing sequences of isolated events, but as soon as overlapping events feature in a simulation batching is required. Because a batching routine would subsume the `NMSIM` Class, writing it will have to wait until the class is available first!

Another (quite different) purpose is appropriate records retention for models used in planning or compliance processes. It would be ideal to allow public models to be publicly available along with the documents where they feature prominently. Presumably this suggests that model objects should be able to be stored in memory for future reuse (i.e., as a `pickle` or other filetype).

Note: `NMSIM-Python` is a library in active development and therefore should be considered an unstable tool. For the same reason it is would also greatly benefit from the contributions of open-source programmers or curious physicists/geographers/ecologist with a taste for software testing.


<!-- MarkdownTOC autolink=true depth=3 bracket=round -->

- [NMSIM Model Creation Workflow: Under a Site-Based Paradigm](##NMSIMworkflow)
  - [1. Initialize an NMSIM project from study area](##1-initialize)
  - [2. Create a site file (.sit) from metadata](##2-reciever)
  - [3. Create flight trajectory (.trj) from the overflights database](##3-path)
  - [4. Compile model to create site-specific analysis (.tis)](##4-putting-it-all-together)
  - [5. Review the results by comparing to acoustic measurements](##5-comparing-theory-to-obs)
- [Public domain](##public-domain)

<!-- /MarkdownTOC -->


## NMSIM Model Creation Workflow: Under a Site-Based Paradigm

<img src=https://github.com/dbetchkal/NMSIM-Python/blob/pyproj_1p9/static/2020%2010%2022%20NMSIM%20source%20improvement%20schema.png width=700>
<br>

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
