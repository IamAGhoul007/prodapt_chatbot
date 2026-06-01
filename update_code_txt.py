import os

def collect_code():
    base_dir = r"d:\capstone2"
    output_file = os.path.join(base_dir, "code.txt")
    
    exclude_dirs = {"venv", "__pycache__", ".git", ".gemini", "data", "adk_services_env"}
    
    with open(output_file, "w", encoding="utf-8") as outfile:
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith(".py") or file == ".env" or file == "README.md":
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, base_dir)
                    
                    outfile.write(f"\n{'='*80}\n")
                    outfile.write(f"File: {rel_path}\n")
                    outfile.write(f"{'='*80}\n\n")
                    
                    try:
                        with open(filepath, "r", encoding="utf-8") as infile:
                            outfile.write(infile.read())
                    except Exception as e:
                        outfile.write(f"<Error reading file: {e}>\n")
                        
collect_code()
