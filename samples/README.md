# Open VFX Houdini ROP Samples

Pre-configured examples of the Open VFX Geometry Cache node to use in the Houdini Sop context.

## Description

This folder includes the following:

* 01_simple to demonstrate the simplest usage of the OVFX Geometry Cache
* 02_with_presets is similar to the previous but it adds presets with menus to control the cache format (bgeo or vdb). Adds also a browse and delete cache button.
* The Python yaml library (for both python 2.7 and 3.7)
* A fake project folder structure that includes shots and assets
* A [Houdini package](https://www.sidefx.com/docs/houdini/ref/plugins.html) file to configure the environment variables.
* The Open VFX configuration files *fragment.yaml* and *location.yaml*
* The *ovfx_geometry_cache.py* that is used to customize geometry cache paths

Those examples are meant to be self contained. In a production environment it's possible that the open-vfx-framework will live in a different place than the 2 other repositories.

The yaml library will probably live along other common Python libraries and made available from studio environment that includes it at the shell level.

In other words the json package file will probably be configured very differently than the one that comes with the samples folder.


## Installing

### Open VFX Repositories
For this example to work, the following repositories must live in the same folder. For example here we copied them into $HOME/OpenVFX

* $HOME/OpenVFX/open-vfx-framework
* $HOME/OpenVFX/open-vfx-houdini
* $HOME/OpenVFX/open-vfx-houdini-rop

### Houdini Json Package File
Copy ./01_simple/package_template/open_vfx_houdini_rop.json or create a symbolic link into a folder where Houdini will recognize the package file and source it. As a test for the current user, this folder can be $HOME/houdiniX.Y/packages.

A few environment variables defined in the json file refer to the $OVFX_PACKAGE_ROOT variable. This variable should be adjusted on your end to point where the repositories are copied. From the example above this would point to $HOME/OpenVFX.

**Note that $OVFX_PACKAGE_ROOT is not a variable that is required by the tool. This is used only in the case of the example so we were able to make everything self contained.**

If using a Houdini version that uses Python 2.7, change the **python3.7** to **python2.7** in the PYTHONPATH variable section.

## Testing

You can open the following scenes and confirm how the path on parameter *Output File* dynamically adapts to the current context on the different OVFX Geometry Cache nodes in the scene.

* ./projects/MyMovie/assets/vehicules/boat/lgt/houdini/hip/MyMovie_vehicule_boat_lgt_setupA_v001.hip
* ./projects/MyMovie/assets/vehicules/car/fx/houdini/hip/MyMovie_vehicule_car_fx_setupA_v001.hip
* ./projects/MyMovie/010/020/0030/fx/houdini/hip/MyMovie_010_020_0030_fx_setupA_v001.hip

From there you can experiment with a folder structure that matches your studio standard by altering the ./01_simple/config/houdini/utility/ovfx_geometry_cache.py