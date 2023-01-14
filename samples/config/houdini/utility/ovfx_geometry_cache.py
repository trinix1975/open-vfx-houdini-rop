import hou
import roputil

def browse(node):
    if node.parm('cachemode') and node.parm('cachemode').eval() == 2: # Proxy geometry
        path = ovfx.path.Path(node.parm('prxrpath').eval())
    else: # Standard geometry
        path = ovfx.path.Path(node.parm('rpath').eval())
    path = path.parent()
    if path.exists():
        os.system('thunar {}'.format(path.path()))

def delete_cache(node):
    if node.parm('cachemode') and node.parm('cachemode').eval() == 2: # Proxy geometry
        path = ovfx.path.Seq(node.parm('prxrpath').eval())
    else: # Standard geometry
        path = ovfx.path.Seq(node.parm('rpath').eval())
    #path = path.parent()
    if path.count() > 0:
        msg = 'Are you sure you want to delete the following?\n\n'
        msg += path.path(format('*'))
        result = hou.ui.displayMessage(msg, ('Ok', 'Cancel',), default_choice=1, close_choice=1)
        if result == 0:
            os.system('rm {}'.format(path.path(format='*')))
            node.parm('refreshinfo').pressButton()

# Initialize the roputil.Node and place it into the right dictionary based on the
# Houdini node category names. For example a sop node will go in hou.ovfx['rop']['Sop']
# and an output Rop will go in hou.ovfx['rop']['Driver']
if 'Sop' not in hou.ovfx['rop'].keys():
    hou.ovfx['rop']['Sop'] = {} # Create the node category if it doesn't already exist
geo = hou.ovfx['rop']['Sop']['geo'] = roputil.Node(node_category='Sop',
                                        node_type='ovfx_geometry_cache',
                                        version=hou.ovfx['loc']['scene'].bundle('ver').value())

if hou.ovfx['loc']['scene'].valid():
    sopoutput = geo.add_parm('sopoutput', bound_menu='sopoutput_menu')
    if hou.ovfx['loc']['scene'].bundle.frag('asset').value(): ################# ASSET ###################
        sopoutput.add_preset('bgeo', hou.ovfx['loc']['scene'].bundle.translate('$OVFX_PACKAGE_ROOT/open-vfx-houdini-rop/samples/projects/<proj>/assets/<assetcat>/<asset>/<task>/houdini/cache/geo/<task>_<scene_desc>_`chs("elem")``chs("tname")``chs("wedge")`/v`chs("wver")`/<proj>_<assetcat>_<asset>_<task>_<scene_desc>_`chs("elem")``chs("tname")``chs("wedge")`_v`chs("wver")``chs("wframe")`.bgeo.sc'))
        sopoutput.add_preset('vdb', hou.ovfx['loc']['scene'].bundle.translate('$OVFX_PACKAGE_ROOT/open-vfx-houdini-rop/samples/projects/<proj>/assets/<assetcat>/<asset>/<task>/houdini/cache/vdb/<task>_<scene_desc>_`chs("elem")``chs("tname")``chs("wedge")`/v`chs("wver")`/<proj>_<assetcat>_<asset>_<task>_<scene_desc>_`chs("elem")``chs("tname")``chs("wedge")`_v`chs("wver")``chs("wframe")`.vdb'))
        sopoutput.add_preset('obj', hou.ovfx['loc']['scene'].bundle.translate('$OVFX_PACKAGE_ROOT/open-vfx-houdini-rop/samples/projects/<proj>/assets/<assetcat>/<asset>/<task>/houdini/cache/obj/<task>_<scene_desc>_`chs("elem")``chs("tname")``chs("wedge")`/v`chs("wver")`/<proj>_<assetcat>_<asset>_<task>_<scene_desc>_`chs("elem")``chs("tname")``chs("wedge")`_v`chs("wver")``chs("wframe")`.obj'))

    else: ################# SHOT ###################
        sopoutput.add_preset('bgeo', hou.ovfx['loc']['scene'].bundle.translate('$OVFX_PACKAGE_ROOT/open-vfx-houdini-rop/samples/projects/<proj>/<epis>/<seq>/<shot>/<task>/houdini/cache/geo/<task>_<scene_desc>_`chs("elem")``chs("tname")``chs("wedge")`/v`chs("wver")`/<proj>_<epis>_<seq>_<shot>_<task>_<scene_desc>_`chs("elem")``chs("tname")``chs("wedge")`_v`chs("wver")``chs("wframe")`.bgeo.sc'))
        sopoutput.add_preset('vdb', hou.ovfx['loc']['scene'].bundle.translate('$OVFX_PACKAGE_ROOT/open-vfx-houdini-rop/samples/projects/<proj>/<epis>/<seq>/<shot>/<task>/houdini/cache/vdb/<task>_<scene_desc>_`chs("elem")``chs("tname")``chs("wedge")`/v`chs("wver")`/<proj>_<epis>_<seq>_<shot>_<task>_<scene_desc>_`chs("elem")``chs("tname")``chs("wedge")`_v`chs("wver")``chs("wframe")`.vdb'))
        sopoutput.add_preset('obj', hou.ovfx['loc']['scene'].bundle.translate('$OVFX_PACKAGE_ROOT/open-vfx-houdini-rop/samples/projects/<proj>/<epis>/<seq>/<shot>/<task>/houdini/cache/obj/<task>_<scene_desc>_`chs("elem")``chs("tname")``chs("wedge")`/v`chs("wver")`/<proj>_<epis>_<seq>_<shot>_<task>_<scene_desc>_`chs("elem")``chs("tname")``chs("wedge")`_v`chs("wver")``chs("wframe")`.obj'))

    # Geo Type
    geo.add_menu('sopoutput_menu', '', 'sopoutput', position='join', callback="hou.ovfx['rop']['Sop']['geo'].parm('sopoutput').apply_preset(hou.pwd(), force=True); hou.phm().update_read(hou.pwd())", values=geo.parm('sopoutput').unique_keys(0))

    # Frame Range
    f = geo.add_parm('f', bound_menu='f_menu')
    f.add_preset('scene', ('$FSTART', '$FEND', 1), language=('Hscript', 'Hscript', None))
    f.add_preset('parent', ('ch("../../f1")', 'ch("../../f2")', 1), language=('Hscript', 'Hscript', None))
    geo.add_menu('f_menu', '', 'f', position='join', callback="hou.ovfx['rop']['Sop']['geo'].parm('f').apply_preset(hou.pwd(), force=True)", values=geo.parm('f').unique_keys(0))

    # Browse Button
    geo.add_button('browse', 'Browse', 'refreshinfo', position='before', callback="hou.ovfx['rop']['Sop']['geo'].callback('browse')(hou.pwd())")
    geo.add_callback('browse', browse)

    # Delete Button
    geo.add_button('delete', 'Delete Cache...', 'refreshinfo', position='before', callback="hou.ovfx['rop']['Sop']['geo'].callback('delete_cache')(hou.pwd())")
    geo.add_callback('delete_cache', delete_cache)

geo.initialize_nodes()
