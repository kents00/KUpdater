import datetime
import os
import zipfile
import io
import json
import webbrowser
import requests
import shutil
import bpy
bl_info = {
    "name": "KUpdater",
    "description": "KUpdater allows users to directly update their addons in blender.",
    "author": "Kent Edoloverio",
    "blender": (3, 5, 1),
    "version": (1, 3, 1),
    "category": "3D View",
    "location": "3D View > KUpdater",
    "warning": "",
    "wiki_url": "https://github.com/kents00/KNTY-Updater",
    "tracker_url": "https://github.com/kents00/KNTY-Updater/issues",
}


class GithubEngine:
    def __init__(self):
        self._api_url = 'https://api.github.com'
        self._token = None
        self._user = None
        self._repo = None
        self._current_version = None
        self._latest_version = None
        self._response = None
        self._update_date = None

    def clear_state(self):
        self._token = None
        self._user = None
        self._repo = None
        self._current_version = None
        self._latest_version = None
        self._response = None
        self._update_date = None

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

    @property
    def update_date(self):
        return self._update_date

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

    def delete_file_in_folder(self):
        """
        The function `delete_file_in_folder` deletes all files inside a specified folder.
        """
        folder_path = os.path.join(
            os.path.dirname(__file__), "..", f"{self.repo}")

        directories = [item for item in os.listdir(
            folder_path) if os.path.isdir(os.path.join(folder_path, item))]

        try:
            for directory_name in directories:
                if directory_name.startswith(f"{self.user}"):
                    target_folder = os.path.join(folder_path, directory_name)
                    for root, dirs, files in os.walk(target_folder):
                        for file in files:
                            file_path = os.path.join(root, file)
                            os.remove(file_path)

            print(f"Files inside {folder_path} deleted successfully.")
        except FileNotFoundError as e:
            print(f"Error deleting files in {folder_path}: {e}")

    def delete_folder(self):
        """
        The `delete_folder` function deletes a specific folder and its contents within a given
        repository.
        """
        folder_path = os.path.join(
            os.path.dirname(__file__), "..", f"{self.repo}")

        directories = [item for item in os.listdir(
            folder_path) if os.path.isdir(os.path.join(folder_path, item))]
        try:
            for directory_name in directories:
                if directory_name.startswith(f"{self.user}"):
                    target_folder = os.path.join(folder_path, directory_name)
                    shutil.rmtree(target_folder)
            print(f"Folder {folder_path} deleted successfully.")
        except FileNotFoundError as e:
            print(f"Error deleting folder {folder_path}: {e}")

    def extract_folder(self):
        """
        The function `extract_folder` extracts the contents of a specific folder from a given repository
        and copies them to the base path.
        """
        folder_path = os.path.join(
            os.path.dirname(__file__), "..", f"{self.repo}")
        directories = [item for item in os.listdir(
            folder_path) if os.path.isdir(os.path.join(folder_path, item))]
        # Find the specific folder that starts with username
        target_folder = None
        for directory_name in directories:
            if directory_name.startswith(f"{self.user}"):
                target_folder = os.path.join(folder_path, directory_name)
                break

        if target_folder is not None:
            destination_folder = folder_path
            print(f"Found target folder: {target_folder}")
            for item in os.listdir(target_folder):
                source_item_path = os.path.join(target_folder, item)
                destination_item_path = os.path.join(destination_folder, item)

                if os.path.isfile(source_item_path):
                    shutil.copy2(source_item_path, destination_item_path)
                elif os.path.isdir(source_item_path):
                    shutil.copytree(source_item_path, destination_item_path)
            print("Contents extracted to base path.")
        else:
            print("Target folder not found.")

    @bpy.app.handlers.persistent
    def check_for_updates(self):
        """
        The above function checks for updates of a Blender add-on by making a request to a specified API
        endpoint and compares the latest version with the current version of the add-on.
        :return: The code is returning the latest version of the addon, the current version of the
        addon, and the update date.
        """
        update_url = f"{self.api_url}/repos/{self.user}/{self.repo}/releases/latest"
        addon_path = os.path.dirname(__file__)

        try:
            response = requests.get(update_url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print("Error checking for updates:", e)
            if response.status_code != 200:
                print("Response content:", response.content)
            return None

        data = json.loads(response.text)
        date = datetime.datetime.now()
        latest_version = data["tag_name"]
        current_version = f"{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}"

        addon_version = {
            "current_version": current_version,
            "latest_version": latest_version,
            "update_date": str(date),
        }
        json_file_path = os.path.join(addon_path, "version_info.json")
        try:
            with open(json_file_path, 'w') as json_file:
                json.dump(addon_version, json_file, indent=1)
        except zipfile.BadZipFile as e:
            print("Error extracting zip file:", e)
            return None
        if self._latest_version != self._current_version:
            return self._latest_version
        return self._current_version, self._update_date

    @bpy.app.handlers.persistent
    def update(self):
        """
        The `update` function downloads a zip file from a specified URL, extracts its contents, and
        performs some additional operations on the extracted files.
        :return: None if there is an error extracting the zip file.
        """
        zipball_url = f"{self.api_url}/repos/{self.user}/{self.repo}/zipball/{self.check_for_updates()}"

        response = requests.get(zipball_url)
        self._response = response

        addon_path = os.path.dirname(__file__)
        zip_data = io.BytesIO(response.content)

        try:
            with zipfile.ZipFile(zip_data, 'r') as zip_ref:
                zip_ref.extractall(addon_path)
                self.extract_folder()
                self.delete_file_in_folder()
                self.delete_folder()
        except zipfile.BadZipFile as e:
            print("Error extracting zip file:", e)
            return None


engine = GithubEngine()


class AddCubeOperator(bpy.types.Operator):
    bl_label = "ADD CUBE"
    bl_idname = "add_simple.cube"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add()
        return {'FINISHED'}


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


# The above class is an addon preferences class in Python that displays information about the latest
# version of the addon and provides options to check for updates and update the addon.
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
    engine.token = None  # Set your GitHub token here if necessary

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    engine.clear_state()
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
