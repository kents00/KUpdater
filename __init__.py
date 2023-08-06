bl_info = {
    "name" : "Addon Updater",
    "description" : "Sample addon updater",
    "author" : "Kent Edoloverio",
    "blender" : (3,5,1),
    "version" : (6,22,23),
    "category" : "3D View",
    "location" : "3D View > Addon Updater",
    "warning" : "",
    "wiki_url" : "https://github.com/kents00/KLicense",
    "tracker_url" : "https://github.com/kents00/KLicense/issues",
}

import bpy
import requests
import json
import webbrowser

class AddCubeOperator(bpy.types.Operator):
    bl_label = "ADD CUBE"
    bl_idname = "add_simple.cube"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add()
        return {'FINISHED'}

class Release_Notes(bpy.types.Operator):
    bl_label = "View the Addon Release Notes"
    bl_idname = "addonupdater.release_notes"

    def execute(self, context):
        webbrowser.open('http://www.google.com/', new=2)
        return {'FINISHED'}

class Update(bpy.types.Operator):
    bl_label = "Update"
    bl_idname = "addonupdater.update"

    def execute(self, context):
        update_url = f"https://api.github.com/repos/kents00/KNTY-Updater/releases/latest"

        try:
            response = requests.get(update_url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print("Error checking for updates:", e)
            return {'CANCELLED'}

        data = json.loads(response.text)
        latest_version = data["tag_name"]

        current_version = f"{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}"
        if latest_version != current_version:
            update_url = data["html_url"]
            webbrowser.open(update_url)
        else:
            print("You are already using the latest version of the addon.")

        return {'FINISHED'}

class LicensePreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.scale_y = 2
        row.operator("addonupdater.release_notes", icon="HELP")
        row = box.row()
        row.scale_y = 2
        row.alert = True
        row.label(text=f"Version 1.1 of your addon is available!")
        row.operator("addonupdater.update", icon="MOD_WAVE")

class AddonUpdaterPanel(bpy.types.Panel):
    bl_label = "Addon Updater"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Addon Updater"
    bl_options = {'HEADER_LAYOUT_EXPAND'}

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.enabled = True
        col.scale_x = 2.0
        col.scale_y = 2.0
        col.operator(AddCubeOperator.bl_idname, icon="MESH_CUBE")
        return {'FINISHED'}

# Register classes
classes = (
    LicensePreferences,
    AddCubeOperator,
    Release_Notes,
    Update,
    AddonUpdaterPanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()