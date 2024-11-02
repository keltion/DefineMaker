from abc import ABC, abstractmethod
import subprocess
import sys

class VersionControlSystem:
    def make_file_from_last_commit(self, original_file_name, file_name):
        try:
            if not self.is_tracked_by_git(file_name):
                with open(original_file_name, 'w') as f:
                    return
            with open(original_file_name, 'w') as f:
                self.get_file_contents_from_last_commit(f, file_name)
        except subprocess.CalledProcessError:
            print("Error: Unable to retrieve original file from Git.")
            sys.exit(1)

    def is_tracked_by_git(self, file_name):
        # 파일이 Git에 의해 추적되고 있는지 확인하는 명령어 실행
        result = subprocess.run(["git", "ls-tree", "HEAD", file_name], 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return bool(result.stdout.strip())

    @abstractmethod
    def get_file_contents_from_last_commit(self, f, file_name):
        pass

class Git(VersionControlSystem):
    def get_file_contents_from_last_commit(self, f, file_name):
        subprocess.run(["git", "show", f"HEAD:{file_name}"], stdout=f, check=True)

class Svn(VersionControlSystem):
    def get_file_contents_from_last_commit(self, f, file_name):
        subprocess.run(["svn", "cat", file_name], stdout=f, check=True)