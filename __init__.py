# ----- BEGIN GPL LICENSE BLOCK -----
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ----- END GPL LICENSE BLOCK -----

bl_info = {
    'name': "Contents Viewer",
    'author': "Mackraken", "batFinger"
    'version': (0, 1, 5),
    'blender': (2, 80, 0),
    'location': "Text Editor > Right Click",
    'warning': "",
    'description': "List text's classes, definitions and create snippets",
    'wiki_url': "https://sites.google.com/site/aleonserra/home/scripts/class-viewer",
    'category': "Text Editor"}

import bpy, os, sys
from bpy.props import PointerProperty, IntProperty, StringProperty, BoolProperty
print(30*"-")

path = os.path.dirname(__file__)
#path = r"D:\Blender Foundation\2.69\scripts\addons\development_class_viewer"
#print(path, os.path.exists(path))


def open_folder():
    if os.name == "nt":
        os.startfile(path)
    elif os.name == "posix":
        os.system('xdg-open "%s"' % path)
    elif os.name == "mac":
        os.system('open "%s"' % path)


def get_snippets():
    snippets = []
    if not os.path.exists(path): return snippets

    files = os.listdir(path)

    for file in files:
        if file[-3::] == "txt":
            snippets.append(file[0:-4])
    return snippets


def current_text(context):
    if context.area.type == "TEXT_EDITOR":
        return context.area.spaces.active.text


def text_selection(context):
    txt = current_text(context)
    sel = ""

    if txt:
        sline = txt.current_line
        endline = txt.select_end_line
        if sline == endline: return sel

        rec = 0
        for i, l in enumerate(txt.lines):
            i=i+1
            line = l.body + "\n"
            if l == sline or l==endline:
                if rec == 0:
                    rec = 1
                    sel += line
                    continue
            if rec:
                sel += line
                if l == sline or l==endline:
                    break
    return sel


def getfunc(txt, sort = True):
    if not txt: return []

    defs = []
    classes = []
    comments = []
    tipoclass = "class "
    tipodef = "def "
    tipocomment = "### "

    for i, l in enumerate(txt.lines):
        i=i+1
        line = l.body

        ### find classes
        find = line.find(tipoclass)
        if find==0:
            class_name = line[len(tipoclass):line.find("(")]

            classes.append([class_name, i, []])
            #print(line, find, class_name)
            continue

        #find defs
        find = line.find(tipodef)
        if find>=0:
            defname = line[find+len(tipodef):line.find("(")]
        if find ==0:

            defs.append([defname, i])
            continue
        if classes and find>0 and find<5:
            classes[-1][2].append([defname, i])
            if sort: classes[-1][2] = sorted(classes[-1][2])
            continue

        #find comments
        find = line.find(tipocomment)
        if find>=0:
            comname = line[find+len(tipocomment)::].strip()
            comments.append([comname, i])
            continue

    if sort: return sorted(defs), sorted(classes), sorted(comments)
    return defs, classes, comments


def linejump(self, context):
    bpy.ops.text.jump(line = self.line)


def findword(self, context):
    if self.findtext:
        spc = context.area.spaces.active
        bpy.ops.text.jump(line=1)
        spc.find_text = self.findtext
        try:
            bpy.ops.text.find()
        except:
            pass


# get error from traceback
def get_error():
    if hasattr(sys, "last_traceback") and sys.last_traceback:
        i = 0
        last=sys.last_traceback.tb_next
        prev = None
        while last:
            i+=1
            prev = last
            last = last.tb_next
            if i>100:
                print("bad recursion")
                return False
        if prev:
            return prev.tb_lineno
        else:
            return sys.last_traceback.tb_lineno
    else:
        if sys.last_value:
            return sys.last_value.lineno
    return False


class ClassViewerProps(bpy.types.PropertyGroup):
    line: IntProperty(min=1, update=linejump)
    findtext: StringProperty(name = "Find Text", default = "" , update = findword)
    show_defs: BoolProperty(name="Show Sub Defs", default=True, description="Shows definitions under classes.")


bpy.utils.register_class(ClassViewerProps)
bpy.types.Scene.class_viewer = PointerProperty(type=ClassViewerProps)


#class TEXT_OT_Jumptoline(bpy.types.Operator):
#	'''Tooltip'''
#	bl_idname = "text.jumptoline"
#	bl_label = "Jump to line"
#
#	line = IntProperty(default=-1)
#
#	@classmethod
#	def poll(cls, context):
#		if context.area.spaces[0].type!="TEXT_EDITOR":
#			return False
#		else:
#			return context.area.spaces.active.text!=None
#
#	def execute(self, context):
#
#		if self.line==-1:
#			if hasattr(sys, "last_traceback"):
#				line = sys.last_traceback.tb_lineno
#				msg = sys.last_value.args[0]
#				self.line = line
#				self.report({'WARNING'}, msg)
#			else:
#				self.report({'WARNING'}, "No Last Error.")
#				return {'CANCELLED'}
#
#		linejump(self, context)
#
#		return {'FINISHED'}


def insert_snippet(name):
    filepath = os.path.join(path, name + ".txt")

    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            txt = f.read()
        bpy.ops.text.insert(text = txt)


def save_snippet(name, txt):
    filepath = os.path.join(path, name + ".txt")
    with open(filepath, "w") as f:
        f.write(txt)


class TEXT_OT_class_viewer(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "text.class_viewer"
    bl_label = "Class Viewer"

    line: IntProperty(default=0, options={'HIDDEN'})
    cmd: StringProperty(default="", options={'HIDDEN'})
    snippet: StringProperty(default="", options={'HIDDEN'})
    snippetname: StringProperty(name="Snippet Name")


    @classmethod
    def poll(cls, context):
        return context.active_object is not None


    def execute(self, context):
        line = self.line
        cmd = self.cmd
        snippet = self.snippet
        #print("execute", cmd, line, snippet)

        if cmd == "ADD_SNIPPET":
            name = self.snippetname.strip()
            sel = text_selection(context)
            print (sel)

            if name and sel:
                save_snippet(name, sel)

        if cmd == "<open folder>":
            open_folder()

        elif cmd == "LAST_ERROR":
            line = get_error()
            if not line:
                self.report({'WARNING'}, "No Last Error")
            else:
                self.report({'WARNING'}, sys.last_value.args[0])


        if line>0:
            bpy.ops.text.jump(line=line)

        if snippet:
            insert_snippet(snippet)

        self.cmd = 	""
        self.line = -1
        self.snippet = ""
        self.snippetname = ""

        return {'FINISHED'}


    def invoke(self, context, event):
        #print("invoking", self.cmd)
        if self.cmd == "ADD_SNIPPET":
            if text_selection(context):
                wm = context.window_manager
                return wm.invoke_props_dialog(self)
            else:
                self.report({'INFO'}, "Select some text.")
        else:
            return self.execute(context)
        self.cmd = 	""
        self.line = -1
        self.snippet = ""
        self.snippetname = ""
        return {'FINISHED'}


class TEXT_MT_def_viewer(bpy.types.Menu):
    bl_idname = "text.def_viewer_menu"
    bl_label = "Defs Viewer Menu"

    @classmethod
    def poll(cls, context):
        return context.area.spaces.active.type=="TEXT_EDITOR" and context.area.spaces.active.text

    def draw(self, context):
        layout = self.layout
        txt = current_text(context)
        items = getfunc(txt, 1)[0]

        for it in items:
            layout.operator("text.class_viewer",text=it[0]).line = it[1]


class TEXT_MT_class_viewer(bpy.types.Menu):
    bl_idname = "text.class_viewer_menu"
    bl_label = "Class Viewer Menu"

    @classmethod
    def poll(cls, context):
        return context.area.spaces.active.type=="TEXT_EDITOR" and context.area.spaces.active.text

    def draw(self, context):
        layout = self.layout
        txt = current_text(context)
        items = getfunc(txt)[1]
        showdefs = context.scene.class_viewer.show_defs

        for it in items:
            cname = it[0]
            cline = it[1]
            cdefs = it[2]
            layout.operator("text.class_viewer",text=cname).line = cline
            if showdefs:
                for d in cdefs:
                    dname = "      " + d[0]
                    dline = d[1]
                    layout.operator("text.class_viewer",text=dname).line = dline
        layout.separator()
        layout.prop(context.scene.class_viewer, "show_defs")

class TEXT_MT_comment_viewer(bpy.types.Menu):
    bl_idname = "text.comment_viewer_menu"
    bl_label = "Comments Viewer Menu"

    @classmethod
    def poll(cls, context):
        return context.area.spaces.active.type=="TEXT_EDITOR" and context.area.spaces.active.text

    def draw(self, context):
        layout = self.layout
        txt = current_text(context)
        items = getfunc(txt)[2]

        for it in items:
            layout.operator("text.class_viewer",text=it[0]).line = it[1]


class TEXT_MT_snippet_viewer(bpy.types.Menu):
    bl_idname = "text.snippet_viewer_menu"
    bl_label = "Snippets Viewer Menu"

    @classmethod
    def poll(cls, context):
        return os.path.exists(path)

    def draw(self, context):
        layout = self.layout

        snippets = get_snippets()
        for item in snippets:
            layout.operator("text.class_viewer", text = item).snippet = item

        layout.separator()
        layout.operator("text.class_viewer", text = "Open Folder").cmd = "<open folder>"



def draw_items(self, context):
    self.layout.separator()
    self.layout.menu("text.def_viewer_menu", text="Defs")
    self.layout.menu("text.class_viewer_menu", text="Classes")
    self.layout.menu("text.comment_viewer_menu", text="Comments")
    self.layout.separator()
    self.layout.menu("text.snippet_viewer_menu", text="Snippets")
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator("text.class_viewer", text="Save a Snippet").cmd="ADD_SNIPPET"
    self.layout.separator()
    self.layout.operator("text.class_viewer", text="Go to Last Error", icon="ERROR").cmd = "LAST_ERROR"
    self.layout.separator()
    self.layout.prop(context.scene.class_viewer, "line", text="       Jump to")#, icon="LINENUMBERS_ON")
    self.layout.prop(context.scene.class_viewer, "findtext", text="", icon="VIEWZOOM")


classes = [	TEXT_MT_def_viewer,
            TEXT_MT_class_viewer,
            TEXT_MT_comment_viewer,
            TEXT_MT_snippet_viewer,
            TEXT_OT_class_viewer ]


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.TEXT_MT_context_menu.append(draw_items)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()
