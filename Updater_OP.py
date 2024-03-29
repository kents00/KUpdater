import bpy
import webbrowser
from .Updater import *

# The `Release_Notes` class is an operator in Blender that opens the release notes of an addon in a
# web browser.
class Release_Notes(bpy.types.Operator):
    bl_label = "View the Release Notes"
    bl_idname = "addonupdater.release_notes"

    def execute(self, context):
        webbrowser.open(
            f"https://github.com/{engine.user}/{engine.repo}", new=1)
        return {'FINISHED'}


# The above class is an operator in Blender that checks for updates to an add-on and updates it if a
# new version is available.
class Update(bpy.types.Operator):
    bl_label = "Update"
    bl_idname = "addonupdater.checkupdate"

    @classmethod
    def poll(cls, context):
        return engine._current_version != engine._latest_version

    def execute(self, context):
        engine.update()
        if engine._response.status_code != 200:
            self.report({'ERROR'}, "Error getting update")
            return {'CANCELLED'}

        if engine._current_version == engine._latest_version:
            self.report(
                {'ERROR'}, "You are already using the latest version of the add-on.")
            return {'CANCELLED'}

        self.report(
            {'INFO'}, "Add-on has been updated. Please restart Blender to apply changes.")
        return {'FINISHED'}


# The Check_for_update class is a Blender operator that checks for updates to an add-on and reports if
# a new version is available.
class Check_for_update(bpy.types.Operator):
    bl_label = "Check Update"
    bl_idname = "addonupdater.update"

    def invoke(self, context, event):
        self.execute(self)
        return {'FINISHED'}

    def execute(self, context):
        engine.check_for_updates()
        if not engine.user or not engine.repo:
            self.report(
                {'ERROR'}, "GitHub user and repository details are not set.")
            return {'CANCELLED'}
        if engine._current_version != engine._latest_version:
            self.report({'INFO'}, "A new version is available!")
        elif engine._current_version == engine._latest_version:
            self.report(
                {'INFO'}, "You are already using the latest version of the add-on.")
        return {'FINISHED'}
