import datetime
import os
import zipfile
import io
import json
import webbrowser
import requests
import shutil
import bpy

bl_info = {"version": (1, 3, 11)}


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
                            if file == "version_info.json":
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
                    if not os.path.exists(destination_item_path):
                        shutil.copy2(source_item_path, destination_item_path)
                    else:
                        print(
                            f"File {item} already exists at the destination. Skipping.")
                elif os.path.isdir(source_item_path):
                    if not os.path.exists(destination_item_path):
                        shutil.copytree(source_item_path,
                                        destination_item_path)
                    else:
                        print(
                            f"Directory {item} already exists at the destination. Skipping.")
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

        return self._current_version, self._update_date, self._latest_version

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
