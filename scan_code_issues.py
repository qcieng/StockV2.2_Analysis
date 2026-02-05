import ast
import os
import sys

def check_imports(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=file_path)
        except SyntaxError as e:
            print(f"❌ Syntax Error in {os.path.basename(file_path)}: {e}")
            return False

    imported_names = set()
    used_names = set()
    
    # Built-in functions (incomplete list, but covers most common ones)
    builtins = {
        'print', 'len', 'range', 'int', 'str', 'float', 'list', 'dict', 'set', 'tuple',
        'bool', 'type', 'isinstance', 'enumerate', 'zip', 'open', 'sum', 'min', 'max',
        'abs', 'round', 'map', 'filter', 'sorted', 'reversed', 'super', 'id', 'dir',
        'help', 'input', 'exit', 'quit', 'Exception', 'ValueError', 'TypeError', 
        'KeyError', 'IndexError', 'ImportError', 'ModuleNotFoundError', 'AttributeError',
        'NotImplementedError', 'RuntimeError', 'True', 'False', 'None'
    }

    for node in ast.walk(tree):
        # Collect imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_names.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_names.add(node.module)
            for alias in node.names:
                imported_names.add(alias.asname or alias.name)
        
        # Collect usages (Name nodes)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used_names.add(node.id)
            
    # Simple check for common missing standard libs
    # This is a heuristic: if we see 'datetime.datetime', we expect 'datetime' to be imported.
    # If we see 'os.path', we expect 'os' to be imported.
    
    issues = []
    
    # Common libraries to check
    common_libs = ['datetime', 'os', 'sys', 'time', 'json', 're', 'random', 'math']
    
    for lib in common_libs:
        if lib in used_names and lib not in imported_names:
             # Check if it's a variable name shadowing the module (hard to be 100% sure without full scope analysis)
             # But usually 'datetime' or 'os' are not used as variable names.
             issues.append(f"❓ Possible missing import: '{lib}' is used but not imported.")

    if issues:
        print(f"⚠️ Issues in {os.path.basename(file_path)}:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print(f"✅ {os.path.basename(file_path)} passed basic static check.")
        return True

def main():
    print("🔍 Starting Code Static Analysis...")
    files = [f for f in os.listdir('.') if f.endswith('.py') and f != os.path.basename(__file__)]
    
    all_passed = True
    for file in files:
        if not check_imports(file):
            all_passed = False
            
    if all_passed:
        print("\n✨ All files passed basic checks.")
    else:
        print("\n⚠️ Some files have potential issues. Please review above.")

if __name__ == "__main__":
    main()
