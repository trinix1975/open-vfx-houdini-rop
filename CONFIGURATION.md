# Configuration
In addition to the required configuration made on the dependent Open VFX Houdini package, a Python script must be created for each type of Rop you wish to use.

## Initialization Scripts
The Open VFX Houdini Rop nodes need to be re-initialized every time a scene is opened or saved to adjust the custom paths that every studio use. We use the mechanism in place from the Open VFX Houdini package which executes all Python scripts found in OVFX_CONFIG_FOLDER/houdini/utility.

Technically we could have a big script that takes care of all Rop node customization but we recommend to use one script per Rop node. In the following examples we are using *ovfx_geometry_cache.py*. This is the script attached to the OVFX Geometry Cache.

The name of each Rop node scripts don't have to use a particular naming but it is advised to keep the name on the example script that are provided in the **sample** folder structure. They simply follow the same name as the HDA type name.

### roputil.Node Creation
The roputil.Node is a class that manages all nodes of a given type. It allows a scene wide refresh on those nodes when the context changes and takes care of automating the parameters creation and update.

This is the code that initialize the OVFX Geometry Cache node type.
```
if 'Sop' not in hou.ovfx['rop'].keys():
    hou.ovfx['rop']['Sop'] = {} # Create the node category if it doesn't already exist
geo = hou.ovfx['rop']['Sop']['geo'] = roputil.Node(node_category='Sop',
                                        node_type='ovfx_geometry_cache',
                                        version=hou.ovfx['loc']['scene'].bundle('ver').value())
```

### Detecting The Context Type
Most studios have multiple types of path that make up a valid context. For example there could be two different folder structures for the shots and assets. Before we set the paths on a Rop node we need to determine what kind of path it will be based on the current context.

Each studio is different but most studios should be able to use something similar to the following in order to do that.

```
if hou.ovfx['loc']['scene'].bundle.frag('asset').value(): ################# ASSET ###################
```
In this example we check if the fragment bundle on the scene context has a value in the **asset** fragment. If it does than it means it is an asset. What follows will be the code to set the asset context paths. If it doesn't then it means it's a **shot**. If the studio has other type of contexts we can simply keep testing for the different types and set the paths for those contexts until all context types have been taken care of.

### Adding Parameter Presets
Paths are filled on the Rop nodes by the roputil.Node instance when the **initialize_nodes()** method is called. However we need to tell the roputil.Node object what parameters will be updated on the real Houdini Rop node parameters and with what value.

This is an example of how we include a parameter to be updated at the context change. 
In the following example we add a connection to the *sopoutput* parameter and we tell it to bind to the menu called *sopoutput_menu*.
```
sopoutput = geo.add_parm('sopoutput', bound_menu='sopoutput_menu')
```
The result object of type roputil.Parm is set to the variable *sopoutput*.

Now that we have a roputil.Parm object we can use it to tell what value to put on the parameter. Technically we don't write a parameter value but instead a preset. This gives flexibility because we can add more than one preset per parameter. A typical use of that is if you have a path that can be either a .bgeo.sc or a .obj file type. In other words if you don't have multiple types of path for the same context, you still create a preset but because there is only one it's treated as if it was a simple value.

Here is an example of a preset created on the previous **sopoutput** parameter.
```
sopoutput.add_preset('bgeo', hou.ovfx['loc']['scene'].bundle.translate('$HOME/RopExample/projects/<proj>/assets/<assetcat>/<asset>/<task>/houdini/cache/geo/<task>_<scene_desc>_`chs("elem")``chs("tname")``chs("wedge")`/v`chs("wver")`/<proj>_<assetcat>_<asset>_<task>_<scene_desc>_`chs("elem")``chs("tname")``chs("wedge")`_v`chs("wver")``chs("wframe")`.bgeo.sc'))```
```

The preset is called **bgeo** and is followed by a rather complex expression that will allow the frame to be included or not based on a toggle, will include the take name or not etc.

### Presets Menu
You can create a menu that will automatically drive a parameter presets. The following will add a dynamic menu joined to the **sopoutput** parameter with a callback that applies the selected preset and force a refresh on the read parameter (through a function that is defined on the geometry cache HDA). Note how the menu values are filled from the roputil.Parm unique_keys() method to get all presets name defined for this node type.

```
geo.add_menu('sopoutput_menu', '', 'sopoutput', position='join', callback="hou.ovfx['rop']['Sop']['geo'].parm('sopoutput').apply_preset(hou.pwd(), force=True); hou.phm().update_read(hou.pwd())", values=geo.parm('sopoutput').unique_keys(0))
```