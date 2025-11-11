import os
import fnmatch

def read_file(path:str) -> str:
    '''
    Reads the content of the file and returns the content as string
    '''
    try:
        with open(path,'r') as f:
            return f.read()
    except FileNotFoundError:
        return f"File not found: {path}"
    except Exception as e:
        return f"Error while reading the file {path}:{e}"

def file_tree_structure(path: str = os.getcwd()) -> str:
    '''
    String representation of the directory tree structure of files and folders
    '''
    if not os.path.exists(path):
        return f"Path doesn't exists"
    
    root = os.path.abspath(path)
    gitignore_path = os.path.join(root, '.gitignore')
    ignore_patterns = ['.git']
    
    # getting the pattern
    if os.path.exists(gitignore_path):
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('!'):
                        ignore_patterns.append(line)
        except Exception as _:
            pass
    
    def should_ignore(rel_path: str, is_dir: bool = False) -> bool:
        if is_dir:
            # removing the dir
            for pattern in ignore_patterns:
                if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(rel_path + os.sep, pattern):
                    return True
        else:
            # removing the files
            for pattern in ignore_patterns:
                if fnmatch.fnmatch(rel_path, pattern):
                    return True
        return False
    
    tree_lines = []
    for root_dir, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not should_ignore(os.path.relpath(os.path.join(root_dir, d), root), is_dir=True)]
        level = root_dir.replace(root, '').count(os.sep)
        indent = '│   ' * (level - 1) + '├── ' if level > 0 else ''
        dir_name = os.path.basename(root_dir)
        if not dir_name:
            dir_name = os.path.basename(os.path.normpath(root)) or 'root'
        tree_lines.append(f"{indent}{dir_name}/")
        
        files = [f for f in files if not should_ignore(os.path.relpath(os.path.join(root_dir, f), root))]
        files.sort()
        for file in files:
            file_indent = '│   ' * (level - 1) + '│   ' if level > 0 else '├── '
            tree_lines.append(f"{file_indent}{file}")
    
    return '\n'.join(tree_lines)