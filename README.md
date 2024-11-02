이 프로그램은 버전 관리 시스템으로 관리되는 파일의 수정사항을 분석하여 ifdef, ifdef~else, ifndef 블록으로 수정 사항을 자동으로 래핑해주는 Python 스크립트입니다. 

# 사용 방법
## 실행 명령어
``` bash
python3 define_maker.py MODULE_NAME FILENAME
```
## 파라미터
1. MODULE_NAME: 추가할 모듈 이름.
2. FILENAME: 모듈 이름을 추가할 파일 경로들. 여러 개의 파일을 한 번에 지정할 수 있습니다.

## 주의사항
1. 이 스크립트는 Git 명령어를 사용하기 때문에 Git 리포지토리에서 실행되어야 하며, 파일이 Git에 의해 관리되고 있어야 합니다. (svn도 지원가능)
2. define파일에 define을 자도응로 추가해주는 `class DefineAdder`는 아직 미완성
3. 고정적으로 사용하는 인자에 대해서는 설정파일로 추후에 뺄 예정 (ex, git or svn 중 어떤 버전관리를 이용하는지에 따라 다르게 동작, jira url, project name 등)