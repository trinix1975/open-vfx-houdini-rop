import hou
import roputil

# Initialize the roputil.Node and place it into the right dictionary based on the
# Houdini node category names. For example a sop node will go in hou.ovfx['rop']['Sop']
# and an output Rop will go in hou.ovfx['rop']['Driver']
if 'Sop' not in hou.ovfx['rop'].keys():
    hou.ovfx['rop']['Sop'] = {} # Create the node category if it doesn't already exist
geo = hou.ovfx['rop']['Sop']['geo'] = roputil.Node(node_category='Sop',
                                        node_type='ovfx_geometry_cache',
                                        version=hou.ovfx['loc']['scene'].bundle('ver').value())

if hou.ovfx['loc']['scene'].valid():
    sopoutput = geo.add_parm('sopoutput')
    if hou.ovfx['loc']['scene'].bundle.frag('asset').value(): ################# ASSET ###################
        sopoutput.add_preset(None, hou.ovfx['loc']['scene'].bundle.translate('$OVFX_PACKAGE_ROOT/open-vfx-houdini-rop/samples/projects/<proj>/assets/<assetcat>/<asset>/<task>/houdini/cache/geo/<task>_<scene_desc>_`chs("elem")``chs("tname")``chs("wedge")`/v`chs("wver")`/<proj>_<assetcat>_<asset>_<task>_<scene_desc>_`chs("elem")``chs("tname")``chs("wedge")`_v`chs("wver")``chs("wframe")`.bgeo.sc'))
    else: ################# SHOT ###################
        sopoutput.add_preset(None, hou.ovfx['loc']['scene'].bundle.translate('$OVFX_PACKAGE_ROOT/open-vfx-houdini-rop/samples/projects/<proj>/<epis>/<seq>/<shot>/<task>/houdini/cache/geo/<task>_<scene_desc>_`chs("elem")``chs("tname")``chs("wedge")`/v`chs("wver")`/<proj>_<epis>_<seq>_<shot>_<task>_<scene_desc>_`chs("elem")``chs("tname")``chs("wedge")`_v`chs("wver")``chs("wframe")`.bgeo.sc'))

geo.initialize_nodes()
