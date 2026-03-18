import pandas as pd
import helper

def run_test():
    print("Initializing Language Tool Test...")
    if not helper.LANG_TOOL_AVAILABLE:
        print("LanguageTool is not available!")
        return

    data = {
        'date': ['2025-01-01', '2025-01-02', '2025-01-03'],
        'user': ['Alice', 'Bob', 'System'],
        'message': [
            'He go to school every day.', 
            'The dogs is barking loud.',
            'System Message'
        ]
    }
    df = pd.DataFrame(data)
    
    print("Testing detect_linguistic_errors...")
    error_df = helper.detect_linguistic_errors('Overall', df)
    
    print("\nTest Results:")
    for _, row in error_df.iterrows():
        print(f"User: {row['User']}")
        print(f"Text: {row['Original Text']}")
        print(f"Errors Found: {row['Total Errors']} (Grammar: {row['Grammar']}, Agreement: {row['Agreement']}, Tense: {row['Tense']}, Typo: {row['Typo']})")
        print(f"Highlighted: {row['Highlighted Text']}")
        print("-" * 30)

if __name__ == "__main__":
    run_test()
