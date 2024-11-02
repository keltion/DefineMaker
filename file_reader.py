class File:
    def __init__(self, name, lines, end_of_file):
        self.name = name
        self.lines = lines
        self.end_of_file = end_of_file

class FileReader:
    def read_file(self, file_name):
        with open(file_name, 'r') as file:
            lines = file.readlines()
        end_of_file = len(lines)
        return File(file_name, lines, end_of_file)