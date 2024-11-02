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
        self.define_files = define_files
        self.issue_number = issue_number
        self.url = f"{url}/{issue_id}"

    def addDefineToDefineFiles(project_name, module_name):
        for file_path in self.define_files:
            with open(file_path, 'a') as file:
                file.write(f"### {self.url}/{project_name}-{self.issue_number}\n")
                file.write(f"### {self.getSummaryFromJira()}\n")
                file.write(f"#{module_name}\n")

    def getSummaryFromJira():
        credentials = f"{self.email}:{self.api_token}"
        encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json"
        }

        request = urllib.request.Request(self.url, headers=headers)

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
        self.user_modified_file = user_modified_file
        self.original_file = original_file
        self.previous_chunk_end_line = 0
        self.addition_parts = []
        self.deletion_parts = []
        self.result = []

    def is_skip_line(self, line):
        return line.startswith('---') or line.startswith('+++')

    def is_diff_chunk_start_line(self, line):
        return line.startswith('@@')

    def write_lines_after_previous_chunk_until(self, current_chunk_start_line :int):
        with open(self.original_file.name, 'r') as infile:
            for current_line, line_content in enumerate(infile, start=1):
                if current_line <= self.previous_chunk_end_line:
                    continue
                if current_line > current_chunk_start_line:
                    return
                self.result.append(line_content)
    
    def write_ifdef_block(self):
            self.result.append(f"#ifdef {moduleName}\n")
            self.result.append(''.join(self.addition_parts))
            self.result.append(f"#endif // {moduleName}\n")

    def write_ifndef_block(self):
            self.result.append(f"#ifndef {moduleName}\n")
            self.result.append(''.join(self.deletion_parts))
            self.result.append(f"#endif // {moduleName}\n")

    def write_ifdef_else_block(self):
        self.result.append(f"#ifdef {moduleName}\n")
        self.result.append(''.join(self.addition_parts))
        self.result.append(f"#else // {moduleName}\n")
        self.result.append(''.join(self.deletion_parts))
        self.result.append(f"#endif // {moduleName}\n")  
         
    def write_diff_with_module(self):
        if self.deletion_parts and self.addition_parts:
            self.write_ifdef_else_block()

        elif len(self.addition_parts) != 0:
            self.write_ifdef_block()
        
        elif len(self.deletion_parts) != 0:
            self.write_ifndef_block()
        
        self.clear_diff_buffers()

    def clear_diff_buffers(self):
        self.addition_parts = []
        self.deletion_parts = []

    def is_addtion_part(self, line):
        return line.startswith('+') and not line.startswith('+++')

    def is_deletion_part(self, line):
        return line.startswith('-') and not line.startswith('---')

    def modify_file_with_module(self):
        for line in unified_diff(self.original_file.lines, self.user_modified_file.lines, fromfile=self.original_file.name, tofile=self.user_modified_file.name, lineterm=''):
            ("line_count", original_file.end_of_file)            
            if self.is_skip_line(line):
                continue
            
            if self.is_diff_chunk_start_line(line):
                match = re.search(r"@@ -(\d+).*? @@", line)
                if match:
                    current_chunk_begin_line = int(match.group(1))
            
                match = re.search(r"@@ -\d+,(\d+).*? @@", line)
                if match:
                    current_chunk_length = int(match.group(1))
                else:
                    current_chunk_length = 1
                    
                self.write_lines_after_previous_chunk_until(current_chunk_begin_line - 1)
                self.previous_chunk_end_line = current_chunk_begin_line + (current_chunk_length - 1)

                self.write_diff_with_module()

            elif self.is_addtion_part(line):
                self.addition_parts.append(line[1:])

            elif self.is_deletion_part(line):
                self.deletion_parts.append(line[1:])
            
            else:
                self.write_diff_with_module()
                self.result.append(line[1:])
        
        self.write_diff_with_module()
        self.write_lines_after_previous_chunk_until(self.original_file.end_of_file)

        with open(self.user_modified_file.name, 'w') as f:
            f.writelines(str(line) for line in self.result)


if len(sys.argv) < 3:
    print("Usage: python3 wrap_diff.py MODULE_NAME FILENAME")
    sys.exit(1)

moduleName = sys.argv[1]
issue_number = sys.argv[2]
file_names = sys.argv[3:]
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
