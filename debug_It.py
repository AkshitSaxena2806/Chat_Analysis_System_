import traceback

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
