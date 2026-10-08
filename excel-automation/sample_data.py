"""
Generate sample input Excel files for demonstration
"""

import pandas as pd
from pathlib import Path

def create_sample_data():
    """Create sample customer data with intentional issues for processing"""
    
    # Sample data with duplicates, empty rows, inconsistent formatting
    data = {
        'customer_id': [1001, 1002, 1002, 1003, '', 1004, 1005, 1005, 1006, ''],
        'name': ['  John Smith  ', 'JANE DOE', 'jane doe', 'Bob Wilson', '', 'Alice Brown', 'Charlie Davis', 'Charlie Davis', 'Emma Wilson', ''],
        'email': ['john@example.com', 'JANE@EXAMPLE.COM', 'jane@example.com', 'bob@test.com', '', 'alice@demo.com', 'charlie@test.com', 'charlie@test.com', 'emma@example.com', ''],
        'age': [28, 35, 35, 42, '', 31, 25, 25, 29, ''],
        'country': ['usa', 'UK', 'uk', 'Canada', '', 'USA', 'Australia', 'australia', 'USA', ''],
        'purchase_amount': [150.50, 230.00, 230.00, 89.99, '', 450.75, 120.00, 120.00, 340.20, '']
    }
    
    df = pd.DataFrame(data)
    
    # Save sample input
    samples_dir = Path("sample_inputs")
    samples_dir.mkdir(exist_ok=True)
    
    output_path = samples_dir / "customers_raw.xlsx"
    df.to_excel(output_path, index=False, engine='openpyxl')
    print(f"Created sample file: {output_path}")
    
    # Create sample rules file
    rules = {
        "dedupe_columns": ["email"],
        "transformations": {
            "name": "title",
            "email": "lowercase",
            "country": "uppercase"
        },
        "filters": {
            "age": {
                "min_value": 18,
                "max_value": 100
            }
        }
    }
    
    import json
    rules_path = samples_dir / "rules.json"
    with open(rules_path, "w") as f:
        json.dump(rules, f, indent=2)
    print(f"Created sample rules: {rules_path}")
    
    print("\nSample data includes:")
    print("- 10 rows (2 empty)")
    print("- 3 exact duplicates")
    print("- Inconsistent formatting (whitespace, case)")
    print("- Mixed country name formats")
    print("\nExpected output: 6 clean, unique records")


if __name__ == "__main__":
    create_sample_data()
