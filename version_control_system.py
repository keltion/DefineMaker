from abc import ABC, abstractmethod
import subprocess
import sys

class VersionControlSystem:
    def make_file_from_last_commit(self, orinal_file_name, file_name):
        try:
            with open(orinal_file_name, 'w') as f:
                self.get_file_contents_from_last_commit(f, file_name)
        except subprocess.CalledProcessError:
            print("Error: Unable to retrieve original file from Git.")
            sys.exit(1)

    @abstractmethod
    def get_file_contents_from_last_commit(self, f, file_name):
        pass

class Git(VersionControlSystem):
    def get_file_contents_from_last_commit(self, f, file_name):
        subprocess.run(["git", "show", f"HEAD:{file_name}"], stdout=f, check=True)

class Svn(VersionControlSystem):
    def get_file_contents_from_last_commit(self, f, file_name):
        subprocess.run(["svn", "cat", file_name], stdout=f, check=True)