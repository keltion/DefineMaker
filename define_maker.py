from difflib import unified_diff
from file_reader import File
from file_reader import FileReader
from version_control_system import VersionControlSystem
from version_control_system import Git

import re
import os   
import sys


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
            print(line)
            if self.is_skip_line(line):
                continue

            if self.is_diff_chunk_start_line(line):
                match = re.search(r"@@ -(\d+),(\d+) \+\d+,\d+ @@", line)
        
                current_chunk_begin_line = int(match.group(1))
                current_chunk_length = int(match.group(2))
                
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
target_file_name = sys.argv[2]

user_modified_file_name = target_file_name

git = Git()
file_reader = FileReader()


git.make_file_from_last_commit(f"{target_file_name}.orig", target_file_name)

user_modified_file = file_reader.read_file(user_modified_file_name)       
original_file = file_reader.read_file(f"{target_file_name}.orig")       


print(f"Start QuickDefine {target_file_name}")
moduleMaker = ModuleMaker(user_modified_file, original_file)
moduleMaker.modify_file_with_module()

os.remove(f"{target_file_name}.orig")
print(f"End QuickDefine")
