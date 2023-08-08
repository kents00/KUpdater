bl_info = {
    "name" : "Addon Updater",
    "description" : "Sample addon updater",
    "author" : "Kent Edoloverio",
    "blender" : (3,5,1),
    "version" : (6,22,23),
    "category" : "3D View",
    "location" : "3D View > Addon Updater",
    "warning" : "",
    "wiki_url" : "https://github.com/kents00/KNTY-Updater",
    "tracker_url" : "https://github.com/kents00/KNTY-Updater/issues",
}

import bpy
import requests
import webbrowser
import threading
import json
import io
import zipfile
import os

class GithubEngine:
    def __init__(self):
        self._api_url = 'https://api.github.com'
        self._token = None
        self._user = None
        self._repo = None

    def clear_state(self):
        self._token = None
        self._user = None
        self._repo = None

    # Getters and Setters for GitHub repository details

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, value):
        if value is None:
            self._token = None
        else:
            self._token = str(value)

    @property
    def user(self):
        return self._user

    @user.setter
    def user(self, value):
        self._user = str(value)

    @property
    def repo(self):
        return self._repo

    @repo.setter
    def repo(self, value):
        self._repo = str(value)

    @property
    def api_url(self):
        return self._api_url

    @api_url.setter
    def api_url(self, value):
        if not self.check_is_url(value):
            raise ValueError("Not a valid URL: " + value)
        self._api_url = value

    @staticmethod
    def check_is_url(url):
        if not ("http://" in url or "https://" in url):
            return False
        if "." not in url:
            return False
        return True


    @bpy.app.handlers.persistent
    def check_for_updates(self):
        if not self._user or not self._repo:
            print("GitHub user and repository details are not set.")
            return None

        update_url = f"{self._api_url}/repos/{self._user}/{self._repo}/releases/latest"

        try:
            response = requests.get(update_url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print("Error checking for updates:", e)
            return None

        data = json.loads(response.text)
        latest_version = data["tag_name"]

        current_version = f"{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}"
        if latest_version != current_version:
            print("A new version is available!")
            return latest_version
        else:
            print("You are already using the latest version of the add-on.")
            return None

engine = GithubEngine()

class AddCubeOperator(bpy.types.Operator):
    bl_label = "ADD CUBE"
    bl_idname = "add_simple.cube"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add()
        return {'FINISHED'}

class Release_Notes(bpy.types.Operator):
    bl_label = "View the Release Notes"
    bl_idname = "addonupdater.release_notes"

    def execute(self, context):
        webbrowser.open(f"https://github.com/{engine.user}/{engine.repo}", new=2)
        return {'FINISHED'}

class Update(bpy.types.Operator):
    bl_label = "Update"
    bl_idname = "addonupdater.update"

    def invoke(self, context, event):
        threading.Thread(target=self.execute, args=(context,)).start()
        return {'FINISHED'}

    def execute(self, context):
        if engine.check_for_updates():
            zipball_url = f"{engine.api_url}/repos/{engine.user}/{engine.repo}/zipball/{engine.check_for_updates()}"

            response = requests.get(zipball_url)
            if response.status_code != 200:
                self.report({'ERROR'},"Error getting update")
                return {'CANCELLED'}

            addon_path = os.path.dirname(__file__)
            zip_data = io.BytesIO(response.content)

            with zipfile.ZipFile(zip_data, 'r') as zip_ref:
                # Check if the extracted files already exist and delete them
                for name in zip_ref.namelist():
                    file_path = os.path.join(addon_path, name)
                    if os.path.exists(file_path):
                        os.rmdir(file_path)
                # Extract the contents of the zipball to the add-on's directory
                zip_ref.extractall(addon_path)
            self.report({'INFO'}, "Add-on has been updated. Please restart Blender to apply changes.")
        return {'FINISHED'}

class LicensePreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.scale_y = 2
        row.operator("addonupdater.release_notes", icon="HELP")
        if engine.check_for_updates():
            row = box.row()
            row.scale_y = 2
            row.alert = True
            row.label(text=f"Version {engine.check_for_updates()} is available!")
            row.operator("addonupdater.update", icon="MOD_WAVE")
        else:
            row = box.row()
            row.scale_y = 2
            row.label(text=f"Addon is running on latest version")

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

    engine.user = "kents00"
    engine.repo = "KNTY-Updater"  # Replace this with your repository name
    engine.token = None  # Set your GitHub token here if necessary

    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    engine.clear_state()
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
