"""
Interact with an OVFX Rop node
"""
import collections
import hou
import nodesearch
import os
import re
import time
import importlib

import ovfx.exceptions
import ovfx.path

class Parm(object):

    def __init__(self, node, name, bound_menu=None):

        self.__node = node # A roputil.Node instance
        self.__name = name
        self.__presets = collections.OrderedDict()
        self.__languages = collections.OrderedDict()
        self.__bound_menu = bound_menu # a single menu parm name or a tuple of parm names

    def __repr__(self):
        cl = self.__class__
        result = '<{}.{} object from {} at {}>'.format(cl.__module__, cl.__name__, self.__name, hex(id(self)))
        return result

    def __eq__(self, other):

        if type(other) == str: # compare with the parm name
            return self.__name == other
        else:
            raise NotImplementedError

    def node(self):
        return self.__node

    def name(self):
        return self.__name

    def unique_keys(self, index=0):

        values = []
        for data in self.__presets:
            if type(data) == tuple: # use the index
                if data[index] not in values:
                    values.append(data[index])
            else: # use the key directly as it's not a tuple
                values.append(data)

        return values

    def add_preset(self, key, value, language=None, is_template=False):

        preset = value
        self.__presets[key] = preset
        self.__languages[key] = language
        self.__is_template = is_template

    def __get_menu_selection(self, node):
        """Get the selected value(s) from the menu(s) bound to this parm"""
        if self.__bound_menu is None:
            return None #raise KeyError('Cannot extract the selected value from a menu. Make sure a menu is bound to parameter: {}'.format(self.__name))
        elif type(self.__bound_menu) == str: # Single menu
            return node.parm(self.__bound_menu).evalAsString()
        else: # a tuple or list
            result = []
            for parm_name in self.__bound_menu:
                result.append(node.parm(parm_name).evalAsString())
            return tuple(result)

    def apply_preset(self, node, force=False):

        key = self.__get_menu_selection(node)
        # Utility functions
        def set_value(parm, value, language):
            parm.deleteAllKeyframes()
            if language: # is an expression
                language = eval('hou.exprLanguage.{}'.format(language))
                parm.setExpression(value, language=language)
            else: # direct value
                parm.set(value)

        def revert_to_default(parm_name):
            parm = node.parm(parm_name)
            if not parm: # Try with parmTuple instead
                parm = node.parmTuple(self.__name)
            parm.revertToDefaults()

        # Main code
        if not key in self.__presets:
            raise KeyError('No preset found in {} for key {}'.format(self, key))
        if force or self.outdated(node):
            if self.__is_template: # Set the default value on the parmTemplate instead
                g = node.parmTemplateGroup()
                t = g.find(self.__name)
                if t: # sometimes the parameter is destroyed so we have to skip it
                    if self.__languages[key]: # At least one component has an expression
                        if t.dataType() == hou.parmData.String:
                            default_value = ['' for i in range(t.numComponents())] # ['', '', etc]
                        else:
                            default_value = [0 for i in range(t.numComponents())] # [0, 0, etc]
                        default_expr = ['' for i in range(t.numComponents())] # ['', '', etc]
                        default_language = [hou.scriptLanguage.Hscript for i in range(t.numComponents())] # ['', '', etc]

                        for i in range(len(self.__presets[key])):
                            language = self.__languages[key][i]
                            if language:
                                default_language[i] = eval('hou.scriptLanguage.{}'.format(language))
                                default_expr[i] = self.__presets[key][i]
                            else:
                                default_value[i] = self.__presets[key][i]

                        t.setDefaultValue(tuple(default_value))
                        t.setDefaultExpression(tuple(default_expr))
                        t.setDefaultExpressionLanguage(tuple(default_language))
                    else: # empty the expression tuple
                        t.setDefaultValue(self.__presets[key])
                        t.setDefaultExpression(tuple(['' for i in range(len(self.__presets))]))
                    g.replace(self.__name, t)
                    node.setParmTemplateGroup(g)
                    # Revert the parm to the default value we just set
                    if '#' in self.__name: # it's a multiparm. We need to go through each instances of that parm
                        first_parm = node.parm(self.__name.replace('#', '1'))
                        if first_parm:
                            for i in range(first_parm.parentMultiParm().eval()): # each multiparm instance
                                revert_to_default(self.__name.replace('#', str(i+1)))
                    else: # single parm
                        revert_to_default(self.__name)
            else: # Set the value directly on the parm
                parm = node.parm(self.__name)
                if parm: # a single parm
                    set_value(parm, self.__presets[key] , self.__languages[key])
                else: # Try with a tuple
                    parm = node.parmTuple(self.__name)
                    if parm:
                        for i in range(len(parm)):
                            set_value(parm[i], self.__presets[key][i], self.__languages[key][i])
            self.reset_outdated(node)

    def preset(self, key):
        return self.__presets[key]

    def presets(self):
        return self.__presets

    def reset_outdated(self, node):
        node.setUserData('ovfx:presets:{}'.format(self.__name), str(self.__presets))

    def outdated(self, node):
        if str(node.userData('ovfx:presets:{}'.format(self.__name))) == str(self.__presets): # keep the existing if nothing has changed.
            return False
        else:
            return True

class Menu(object):

    def __init__(self, name, label, adjacent_parm ,position='join', script=None, values=[]):

        self.__name = name
        self.__label = label
        self.__adjacent_parm = adjacent_parm
        self.__position = position
        self.__script = script
        self.__values = []
        self.__labels = []
        if values:
            self.set_values(values)

    def __repr__(self):
        cl = self.__class__
        result = '<{}.{} object from {} at {}>'.format(cl.__module__, cl.__name__, self.__name, hex(id(self)))
        return result

    def __eq__(self, other):

        if type(other) == str: # compare with the parm name
            return self.__name == other
        else:
            raise NotImplementedError

    def name(self):
        return self.__name

    def set_values(self, values):

        self.__values = values
        self.__labels = []
        for value in self.__values:
            self.__labels.append(' '.join([s.capitalize() for s in value.split('_')]))

    def values(self):
        return self.__values

    def create(self, node, force=False):

        user_data_name = 'ovfx:presets:{}'.format(self.__name)
        create_menu = True
        g = node.parmTemplateGroup()
        existing_parm = g.find(self.__name)
        if existing_parm:
            if node.userData(user_data_name) == str(self.__values): # keep the existing if nothing has changed.
                create_menu = False

        result = False
        if force or create_menu:
            if g.find(self.__name):
                g.remove(self.__name)
            # Create the parm template
            parm_template = hou.MenuParmTemplate(self.__name, self.__label, self.__values, menu_labels=self.__labels, script_callback=self.__script, script_callback_language=hou.scriptLanguage.Python, tags={'is_ovfx_parm': '1'})
            # Set the combo label visibility
            parm_template.hideLabel(not self.__label)

            if self.__position == 'before': # set the combo before the parm
                g.insertBefore(self.__adjacent_parm, parm_template)
            elif self.__position == 'after': # set the combo after the parm
                g.insertAfter(self.__adjacent_parm, parm_template)
            elif self.__position == 'join': # set the combo at the end of the parm
                # Set a tag that tells which parameter it's joined to
                tags = parm_template.tags()
                tags['ovfx_join_parm'] = self.__adjacent_parm
                parm_template.setTags(tags)
                # Join the parm
                g.insertAfter(self.__adjacent_parm, parm_template)
                t = g.find(self.__adjacent_parm) # The parm which to place next to
                t.setJoinWithNext(True)
                # Apply the parmTemplateGroup
                g.replace(self.__adjacent_parm, t)

            node.setParmTemplateGroup(g)
            node.setUserData(user_data_name, str(self.__values))
            result = True
        return result


class Button(object):

    def __init__(self, name, label, adjacent_parm ,position='join', script=None):

        self.__name = name
        self.__label = label
        self.__adjacent_parm = adjacent_parm
        self.__position = position
        self.__script = script

    def __repr__(self):
        cl = self.__class__
        result = '<{}.{} object from {} at {}>'.format(cl.__module__, cl.__name__, self.__name, hex(id(self)))
        return result

    def name(self):
        return self.__name

    def create(self, node):

        g = node.parmTemplateGroup()
        existing_parm = g.find(self.__name)
        if existing_parm:
            if g.find(self.__name):
                g.remove(self.__name)
        # Validate the parm doesn't already exist on the asset
        if node.type().definition().parmTemplateGroup().find(self.__name):
            raise ovfx.AlreadyExists('Cannot add button named: {}. A parameter with the same name already exists on the HDA.'.format(self.__name))
        # Create the parm template
        parm_template = hou.ButtonParmTemplate(self.__name, self.__label, script_callback=self.__script, script_callback_language=hou.scriptLanguage.Python, tags={'is_ovfx_parm': '1'})
        if self.__position == 'before': # set the combo before the parm
            g.insertBefore(self.__adjacent_parm, parm_template)
        elif self.__position == 'after': # set the combo after the parm
            g.insertAfter(self.__adjacent_parm, parm_template)
        elif self.__position == 'join': # set the combo at the end of the parm
            # Set a tag that tells which parameter it's joined to
            tags = parm_template.tags()
            tags['ovfx_join_parm'] = self.__adjacent_parm
            parm_template.setTags(tags)
            # Join the parm
            g.insertAfter(self.__adjacent_parm, parm_template)
            t = g.find(self.__adjacent_parm) # The parm which to place next to
            t.setJoinWithNext(True)
            g.replace(self.__adjacent_parm, t)

        node.setParmTemplateGroup(g)


class Node(object):
    """
    Used to hold file cache settings and manage nodes refresh

    By convention an instance of this object is created on the hou object, e.g hou.ovfx['rop']['Sop']['geo'], hou.ovfx['rop']['Driver'], hou.ovfx['rop']['Sop']['abc']
    """

    def __init__(self, node_category, node_type, version=1, version_padding=3, frame_padding=4, element_separator='-'):

        self.__node_category = node_category
        self.__node_type = node_type
        self.__version = version
        self.__version_padding = version_padding
        self.__frame_padding = frame_padding
        self.__element_separator = element_separator

        self.__paths = collections.OrderedDict()
        self.__frame_ranges = collections.OrderedDict()
        self.__callbacks = {}

        self.__parms = []
        self.__menus = []
        self.__buttons = []

    def initialize_nodes(self):
        """
        Iterates through all nodes of the specified type in the scene and
        and run the initialize setup if the Auto Update parameter is checked.

        This is usually run when the shot/asset context is updated.
        """
        matcher = nodesearch.NodeType(self.__node_type, self.__node_category)
        for node in matcher.nodes(hou.node('/'), recursive=True):
            if node.parm('autoupdate').eval() == True:
                node.hdaModule().setup_node(node)

    @staticmethod
    def cleanup_user_data(node):
        """
        Remove all user data related to this class.

        The cleanup needs to happen when a new node instance is created to
        prevent having old data from the original node used to save the HDA.
        """
        for key in node.userDataDict().keys():
            ovfx_key = 'ovfx:presets:'
            if key[:len(ovfx_key)] == ovfx_key:
                node.destroyUserData(key)

    @staticmethod
    def delete_ovfx_parms(node):
        """
        Delete all spare parameters with the tag attribute is_ovfx_parm=1.

        This tag attribute is attribute is added to all dynamic parameters created
        by the ovfx tool like preset menus or push buttons.
        """
        g = node.parmTemplateGroup()
        for p in node.parms():
            if 'is_ovfx_parm' in p.parmTemplate().tags():
                if 'ovfx_join_parm' in p.parmTemplate().tags():
                    join_parm_name = p.parmTemplate().tags()['ovfx_join_parm']
                    t = g.find(join_parm_name)
                    if t is not None: # the parameter might have already been removed
                        t.setJoinWithNext(False) # Uncheck the join with next parm
                        g.replace(join_parm_name, t)
                g.remove(p.parmTemplate()) # Remove the parm
        node.setParmTemplateGroup(g)

    @staticmethod
    def file_info(path, show_size=True):
        """
        Return the file information like the frame count, frame range and
        date range of the files found on disk that match the input path
        """
        def file_date(path):
            return time.ctime(os.path.getmtime(path))

        seq = ovfx.path.Seq(path)
        info = 'No Files Found'
        count = seq.count()

        if count:
            info = 'Total File(s): {}'.format(count)
            if count == 1:
                if seq.is_seq():
                    info += '\nFrame        : {}'.format(seq.first_frame())
                else: # Static Frame
                    info += '\nFrame        : Static'
                if show_size:
                    info += '\nSize         : {}'.format(seq.size())
                info += '\nDate         : {}'.format(file_date(seq.files()[0]))
            else: # more than one file
                info += '\nFrames       : {} - {}'.format(seq.first_frame(), seq.last_frame())
                if show_size:
                    info += '\nSize         : {}'.format(seq.size())
                info += '\nDate     From: {}'.format(file_date(seq.files()[0]))
                info += '\n           To: {}'.format(file_date(seq.files()[-1]))
                time_diff = os.path.getmtime(seq.files()[-1]) - os.path.getmtime(seq.files()[0])
                hour = int(time_diff / 3600)
                minute = int((time_diff - (hour * 3600)) / 60)
                second = round(time_diff - (hour * 3600) - (minute * 60))
                info += '\n     Time Diff: {}h {}m {}s'.format(hour, minute, second)
        return info

    def format_version(self, version):
        """
        Return the version with the padding. Uses the instance number of padding "version_padding"

        Args:
            version (int | string)       : The integer version you want to format with padding.

        Returns:
            Padded version, e.g. 011
        """
        if type(version) == str: # convert the string to an int to get rid of existing padding
            version = int(version)
        version = str(version)

        return version.zfill(self.__version_padding)

    def add_parm(self, name, bound_menu=None):
        if name in self.__parms: # Delete the existing so we can recreate it
            self.__parms.remove(name)
        parm = Parm(self, name, bound_menu)
        self.__parms.append(parm)
        return parm

    def parm(self, name):
        if name not in self.__parms:
            raise KeyError('roputil.Parm "{}" cannot be found in roputil.Node "{}".'.format(name, self))
        return self.__parms[self.__parms.index(name)]

    def parms(self):
        return self.__parms

    def add_menu(self, name, label, adjacent_parm ,position='join', callback=None, values=[]):
        if name not in self.__menus: # make sure it doesn't already exists
            self.__menus.append(Menu(name, label, adjacent_parm, position, callback, values))

    def menu(self, name):
        if name in self.__menus:
            index = self.__menus.index(name)
            return self.__menus[index]

    def menus(self):
        return self.__menus

    def create_menus(self, node, force=False):
        for menu in self.menus():
            if menu.create(node, force=force): # The menu was successfully (re)created
                node.parm(menu.name()).set(0) # Every time a menu is recreated we initialize the selection

    def add_button(self, name, label, adjacent_parm ,position='join', callback=None):
        if name not in self.__menus: # make sure it doesn't already exists
            self.__buttons.append(Button(name, label, adjacent_parm, position, callback))

    def button(self, name):
        if name in self.__buttons:
            index = self.__buttons.index(name)
            return self.__buttons[index]

    def buttons(self):
        return self.__buttons

    def add_callback(self, parm_name, func):
        self.__callbacks[parm_name] = func

    def callback(self, parm_name):
        if parm_name in self.__callbacks:
            return self.__callbacks[parm_name]

    def callbacks(self):
        return self.__callbacks

    def version_padding(self):
        return self.__version_padding

    def version(self):
        return self.__version

    def formatted_version(self):
        return self.format_version(self.__version)

    def frame_padding(self):
        return self.__frame_padding

    def element_name(self, node, add_prx=False):
        parent = node
        for i in range(node.parm('parentprefix').eval()):
            parent = parent.parent()

        name = node.name()
        if add_prx: # Add the proxy suffixe
            name = '{}{}prx'.format(name, self.__element_separator)
        if parent == node:
            return name
        else:
            return '{}{}{}'.format(parent.name(), self.__element_separator, name)

    def take_name(self, node):
        result = ''
        if node.parm('includetake').eval():
            take = node.parm('take').evalAsString()
            scene_take = hou.takes.currentTake().name()
            if take == '_current_' and scene_take != 'Main': # the scene take
                result = '{}{}'.format(self.__element_separator, scene_take)
            elif take not in ('_current_', 'Main'):
            # elif (take != '_current_' and take != 'Main'): # directly the given take
                result = '{}{}'.format(self.__element_separator, take)
        return result

    def wedge_name(self, node):
        result = ''
        if node.parm('wedgename').evalAsString() == 'number':
            result = '{}{}'.format(self.__element_separator, hou.text.expandString('$WEDGENUM'))
        elif node.parm('wedgename').evalAsString() == 'name':
            result = '{}{}'.format(self.__element_separator, hou.text.expandString('$WEDGE'))

        return result
