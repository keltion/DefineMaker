from abc import ABC, abstractmethod
import subprocess
import sys
import re

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
    def parse_rpc_signature(self, line):
        # 정규식 패턴 정의
        pattern = r"rpc\s+(\w+)\s*\(\s*([\w.]+)\s*\)\s*returns\s*\(\s*([\w.]+)\s*\)"

        match = re.match(pattern, line)
        if match:
            function_name = match.group(1)
            argument = match.group(2)
            return_type = match.group(3)
            return function_name, argument, return_type
        else:
            return None

    def _get_file_contents_from_last_commit(self, f, file_name):
        subprocess.run(["git", "show", f"HEAD:{file_name}"], stdout=f, check=True)

    def parse_proto_from_last_commit(self):
        result = {}
        added_lines_for_proto = self.get_last_commit_added_lines_for_proto()

        if added_lines_for_proto:
            for file, lines in added_lines_for_proto.items():
                # print(f"\n--- {file} ---")
                # print(f"{lines}")
                # print("\n".join(lines))

                for line in lines:
                    if line.startswith('rpc'):
                        # print(line)
                        # print(self.parse_rpc_signature(line))
                        result.setdefault(file[:-len(".proto")], []).append(self.parse_rpc_signature(line))

                # print("\n" + "="*80)

        return result

    def get_last_commit_added_lines_for_proto(self):
        try:
            # 마지막 커밋의 diff에서 .proto 파일만 필터링
            result_diff = subprocess.run(
                ["git", "diff", "--unified=0", "HEAD~1", "HEAD"],
                capture_output=True, text=True, check=True
            )

            lines = result_diff.stdout.splitlines()
            added_lines = {}

            current_file = None

            for line in lines:
                # 파일 이름 감지 (diff 헤더에서 '+++ b/'로 시작하는 경우)
                if line.startswith('+++ b/') and line.endswith('.proto'):
                    current_file = line[6:].strip()  # '+++ b/' 제거 후 파일명 저장
                    added_lines[current_file] = []

                # 추가된 라인만 저장 ('+'로 시작하지만 파일 정보(`+++`)는 제외)
                elif current_file and line.startswith('+') and not line.startswith('+++'):
                    added_lines[current_file].append(line[1:].strip())  # '+' 제거 후 저장

            # 추가된 라인이 있는 경우만 출력
            return {file: lines for file, lines in added_lines.items() if lines}

        except subprocess.CalledProcessError as e:
            print(f"Git 명령 실행 오류: {e}")
            return {}

class Svn(VersionControlSystem):
    def get_file_contents_from_last_commit(self, f, file_name):
        subprocess.run(["svn", "cat", file_name], stdout=f, check=True)

