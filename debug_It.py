import traceback
import os

java_paths = [
    r"C:\Program Files\Common Files\Oracle\Java\javapath",
    r"C:\Program Files (x86)\Common Files\Oracle\Java\java8path"
]
for p in java_paths:
    if os.path.exists(p) and p.lower() not in os.environ.get('PATH', '').lower():
        os.environ['PATH'] = p + os.pathsep + os.environ.get('PATH', '')

try:
    import language_tool_python
    print("Module language_tool_python loaded successfully.")
    
    # Try to initialize it
    print("Initializing LanguageTool...")
    tool = language_tool_python.LanguageTool('en-US')
    print("Initialize successful!")
except Exception as e:
    print("Error initializing LanguageTool:")
    traceback.print_exc()
