import bpy
import os
from .Updater import engine
from .Updater_OP import *

bl_info = {
    "name": "KUpdater",
    "author": "Kent Edoloverio",
    "description": "Update your addon easily by using this addon",
    "blender": (4, 0, 2),
    "version": (1, 3, 2),
    "location": "3D View > KUpdater",
    "warning": "",
    "category": "3D View",
}


class AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.scale_y = 2
        row.operator("addonupdater.release_notes", icon="HELP")
        row = box.row()
        row.scale_y = 2
        row.operator(Check_for_update.bl_idname, icon="TRIA_DOWN_BAR")
        row.scale_y = 2
        row.alert = True
        row.operator(Update.bl_idname, icon="FILE_REFRESH")

        json_file_path = os.path.join(
            os.path.dirname(__file__), "version_info.json")

        try:
            with open(json_file_path, 'r') as json_file:
                version_info = json.load(json_file)
                engine._update_date = version_info.get("update_date")
                engine._latest_version = version_info.get("latest_version")
                engine._current_version = version_info.get("current_version")

                if engine._latest_version is not None:
                    row = box.row()
                    row.label(
                        text=f"Version: {engine._latest_version}")
                elif engine._current_version == engine._latest_version:
                    row = box.row()
                    row.label(
                        text=f"You are using the latest version: {engine._latest_version}")
                if engine._update_date is not None:
                    row = box.row()
                    row.label(text=f"Last update: {engine._update_date}")
        except json.decoder.JSONDecodeError as e:
            print(f"Error loading JSON file: {e}")
            row = box.row()
            row.label(text="Last update: Never")
        except FileNotFoundError:
            row = box.row()
            row.label(text="Error loading version information.")


class AddCubeOperator(bpy.types.Operator):
    bl_label = "ADD CUBE"
    bl_idname = "add_simple.cube"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add()
        return {'FINISHED'}


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


classes = (
    AddonPreferences,
    AddCubeOperator,
    Release_Notes,
    Check_for_update,
    Update,
    AddonUpdaterPanel,
)


def register():

    engine.user = "kents00"  # Replace this with your username
    engine.repo = "KUpdater"  # Replace this with your repository name

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    engine.clear_state()
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
