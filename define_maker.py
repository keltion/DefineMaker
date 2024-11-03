import json
import time
import re
import os   
import sys
import urllib.request
import base64

from difflib import unified_diff
from file_reader import File
from file_reader import FileReader
from version_control_system import VersionControlSystem
from version_control_system import Git


def progress_bar(target, current, total, bar_length=20):
    percent = float(current) / total
    arrow = '#' * int(round(percent * bar_length))
    spaces = ' ' * (bar_length - len(arrow))
    sys.stdout.write(f"\r[{arrow}{spaces}] {int(percent * 100)}%")
    sys.stdout.flush()

class DefineAdder:
    def __init__(self, project_name, url, issue_number, email, api_token, define_files):
        self._define_files = define_files
        self._issue_number = issue_number
        self._url = f"{url}/{issue_number}"
        self._email = email
        self._api_token = api_token

    def add_define_to_define_files(self, project_name, module_name):
        for file_path in self._define_files:
            with open(file_path, 'a') as file:
                file.write(f"### {self._url}/{project_name}-{self._issue_number}\n")
                file.write(f"### {self.get_summary_from_jira()}\n")
                file.write(f"#{module_name}\n")

    def get_summary_from_jira(self):
        credentials = f"{self._email}:{self._api_token}"
        encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json"
        }

        request = urllib.request.Request(self._url, headers=headers)

        summary = ""
        try:
            with urllib.request.urlopen(request) as response:
                if response.status == 200:
                    data = json.load(response)
                    summary = data.get("fields", {}).get("summary", "Summary not found")
                else:
                    print(f"Error: Unable to fetch data. Status code: {response.status}")
        except urllib.error.HTTPError as e:
            print(f"HTTP Error: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            print(f"URL Error: {e.reason}")
        return summary


class ModuleMaker:
    def __init__(self, user_modified_file, original_file):
        self._user_modified_file = user_modified_file
        self._original_file = original_file
        self._previous_chunk_end_line = 0
        self._addition_parts = []
        self._deletion_parts = []
        self._result = []

    def _is_skip_line(self, line):
        return line.startswith('---') or line.startswith('+++')

    def _is_diff_chunk_start_line(self, line):
        return line.startswith('@@')

    def _write_lines_after_previous_chunk_until(self, current_chunk_start_line):
        with open(self._original_file, 'r') as infile:
            for current_line, line_content in enumerate(infile, start=1):
                if current_line <= self._previous_chunk_end_line:
                    continue
                if current_line > current_chunk_start_line:
                    return
                self._result.append(line_content)

    def _write_ifdef_block(self, module_name):
        self._result.append(f"#ifdef {module_name}\n")
        self._result.append(''.join(self._addition_parts))
        self._result.append(f"#endif // {module_name}\n")

    def _write_ifndef_block(self, module_name):
        self._result.append(f"#ifndef {module_name}\n")
        self._result.append(''.join(self._deletion_parts))
        self._result.append(f"#endif // {module_name}\n")

    def _write_ifdef_else_block(self, module_name):
        self._result.append(f"#ifdef {module_name}\n")
        self._result.append(''.join(self._addition_parts))
        self._result.append(f"#else // {module_name}\n")
        self._result.append(''.join(self._deletion_parts))
        self._result.append(f"#endif // {module_name}\n")

    def _write_diff_with_module(self, module_name):
        if self._deletion_parts and self._addition_parts:
            self._write_ifdef_else_block(module_name)

        elif len(self._addition_parts) != 0:
            self._write_ifdef_block(module_name)

        elif len(self._deletion_parts) != 0:
            self._write_ifndef_block(module_name)

        self._clear_diff_buffers()

    def _clear_diff_buffers(self):
        self._addition_parts = []
        self._deletion_parts = []

    def _is_addition_part(self, line):
        return line.startswith('+') and not line.startswith('+++')

    def _is_deletion_part(self, line):
        return line.startswith('-') and not line.startswith('---')

    def modify_file_with_module(self, module_name):
        with open(self._original_file, 'r') as original, open(self._user_modified_file, 'r') as modified:
            original_lines = original.readlines()
            modified_lines = modified.readlines()

        for line in unified_diff(original_lines, modified_lines, fromfile=self._original_file,
                                 tofile=self._user_modified_file, lineterm=''):
            if self._is_skip_line(line):
                continue

            if self._is_diff_chunk_start_line(line):
                match = re.search(r"@@ -(\d+).*? @@", line)
                if match:
                    current_chunk_begin_line = int(match.group(1))

                match = re.search(r"@@ -\d+,(\d+).*? @@", line)
                if match:
                    current_chunk_length = int(match.group(1))
                else:
                    current_chunk_length = 1

                self._write_lines_after_previous_chunk_until(current_chunk_begin_line - 1)
                self._previous_chunk_end_line = current_chunk_begin_line + (current_chunk_length - 1)

                self._write_diff_with_module(module_name)

            elif self._is_addition_part(line):
                self._addition_parts.append(line[1:])

            elif self._is_deletion_part(line):
                self._deletion_parts.append(line[1:])

            else:
                self._write_diff_with_module(module_name)
                self._result.append(line[1:])

        self._write_diff_with_module(module_name)
        self._write_lines_after_previous_chunk_until(len(original_lines))

        with open(self._user_modified_file, 'w') as f:
            f.writelines(str(line) for line in self._result)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 define_maker.py MODULE_NAME FILENAME")
        sys.exit(1)

    moduleName = sys.argv[1]
    file_names = sys.argv[2:]
    file_count = len(file_names)

    git = Git()
    file_reader = FileReader()

    print(f"* start QuickDefine")
    for idx, target_file_name in enumerate(file_names):
        progress_bar(target_file_name, idx + 1, file_count)

        user_modified_file_name = target_file_name
        git.make_file_from_last_commit(f"{target_file_name}.orig", target_file_name)

        user_modified_file = file_reader.read_file(user_modified_file_name)
        original_file = file_reader.read_file(f"{target_file_name}.orig")


        moduleMaker = ModuleMaker(user_modified_file, original_file)
        moduleMaker.modify_file_with_module()

        os.remove(f"{target_file_name}.orig")
