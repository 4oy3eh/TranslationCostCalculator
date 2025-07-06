#!/usr/bin/env python3
"""
Precise Column Debug - найдем точные позиции Words колонок
"""

import sys
import csv
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent if __file__.endswith('precise_column_debug.py') else Path.cwd()
sys.path.insert(0, str(project_root))

def analyze_exact_word_positions():
    """Точный анализ позиций Words колонок."""
    print("🔍 PRECISE WORD COLUMN ANALYSIS")
    print("=" * 60)
    
    file1 = project_root / "test_data" / "csv_Analysis_example_1.csv"
    file2 = project_root / "test_data" / "csv_Analysis_example_2.csv"
    
    for file_path in [file1, file2]:
        if not file_path.exists():
            continue
            
        print(f"\n📄 Analyzing: {file_path.name}")
        print("-" * 40)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            rows = list(reader)
        
        if len(rows) < 3:
            continue
        
        header1, header2 = rows[0], rows[1]
        data_row = rows[2]  # First data row
        
        print(f"📊 Total columns: {len(header2)}")
        print(f"📊 Data columns: {len(data_row)}")
        
        # Find all Words columns by scanning header2
        words_columns = []
        for i, header in enumerate(header2):
            if 'Words' in header:
                value = data_row[i] if i < len(data_row) else "N/A"
                words_columns.append((i, header, value))
        
        print(f"\n🔤 Words columns found:")
        total_from_words_cols = 0
        for col_idx, header, value in words_columns:
            try:
                numeric_value = float(value) if value and value != "N/A" else 0
                total_from_words_cols += numeric_value
                print(f"   Col {col_idx:2d}: {header} = {value} ({numeric_value})")
            except:
                print(f"   Col {col_idx:2d}: {header} = {value} (invalid)")
        
        print(f"📝 Total from Words columns: {total_from_words_cols}")
        
        # Show category structure from header1
        print(f"\n🏷️ Category analysis:")
        categories = []
        for h in header1:
            if h.strip() and h.strip() not in ['Total', 'File'] and h.strip() not in categories:
                categories.append(h.strip())
        
        print(f"   Categories: {categories}")
        
        # Manual mapping of categories to word columns
        print(f"\n🎯 Category to Words mapping:")
        
        # Expected pattern: File(0), TaggingErrors(1), Chars/Word(2), then categories start at 3
        col_idx = 3
        format_type = 'with_characters' if len(header2) >= 45 else 'without_characters'
        fields_per_cat = 5 if format_type == 'with_characters' else 4
        
        print(f"   Format: {format_type} ({fields_per_cat} fields per category)")
        
        category_word_mapping = {}
        for cat_idx, category in enumerate(categories):
            words_col = col_idx + 1  # Words is typically 2nd field (after Segments)
            if words_col < len(data_row):
                try:
                    words_value = float(data_row[words_col]) if data_row[words_col] else 0
                    category_word_mapping[category] = (words_col, words_value)
                    print(f"   {category}: col {words_col} = {words_value}")
                except:
                    category_word_mapping[category] = (words_col, 0)
                    print(f"   {category}: col {words_col} = 0 (invalid)")
            col_idx += fields_per_cat
        
        manual_total = sum(value for _, value in category_word_mapping.values())
        print(f"📝 Manual category total: {manual_total}")
        
        # Compare all totals
        print(f"\n📊 COMPARISON:")
        print(f"   Words columns total: {total_from_words_cols}")
        print(f"   Category mapping total: {manual_total}")
        
        # Show the difference
        if abs(total_from_words_cols - manual_total) > 0.01:
            print(f"   ⚠️ DIFFERENCE: {total_from_words_cols - manual_total}")
            print(f"   🔍 Need to check column alignment!")
        else:
            print(f"   ✅ Values match")

def compare_word_column_positions():
    """Сравнение позиций Words колонок между файлами."""
    print(f"\n🔄 WORD COLUMN POSITION COMPARISON")
    print("=" * 60)
    
    file1 = project_root / "test_data" / "csv_Analysis_example_1.csv"
    file2 = project_root / "test_data" / "csv_Analysis_example_2.csv"
    
    files_data = {}
    
    for file_path in [file1, file2]:
        if not file_path.exists():
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            rows = list(reader)
        
        if len(rows) < 3:
            continue
        
        header2 = rows[1]
        data_row = rows[2]
        
        # Find Words columns
        words_positions = []
        for i, header in enumerate(header2):
            if 'Words' in header and i < len(data_row):
                try:
                    value = float(data_row[i]) if data_row[i] else 0
                    words_positions.append((i, value))
                except:
                    words_positions.append((i, 0))
        
        files_data[file_path.name] = words_positions
    
    print("📊 Words column positions:")
    for filename, positions in files_data.items():
        print(f"\n   {filename}:")
        for col_idx, value in positions:
            print(f"     Col {col_idx:2d}: {value}")
    
    # Compare if same values appear in different positions
    if len(files_data) == 2:
        file1_name, file2_name = list(files_data.keys())
        file1_values = [value for _, value in files_data[file1_name]]
        file2_values = [value for _, value in files_data[file2_name]]
        
        print(f"\n🔍 Value comparison:")
        print(f"   {file1_name} values: {file1_values}")
        print(f"   {file2_name} values: {file2_values}")
        
        if file1_values == file2_values:
            print(f"   ⚠️ IDENTICAL VALUES - this should NOT happen!")
            print(f"   🔧 Check if parsing same physical location")
        else:
            print(f"   ✅ Different values - parsing is working correctly")

def debug_raw_data_extraction():
    """Дебаг сырого извлечения данных."""
    print(f"\n🔧 RAW DATA EXTRACTION DEBUG") 
    print("=" * 60)
    
    file1 = project_root / "test_data" / "csv_Analysis_example_1.csv"
    file2 = project_root / "test_data" / "csv_Analysis_example_2.csv"
    
    for file_path in [file1, file2]:
        if not file_path.exists():
            continue
            
        print(f"\n📄 Raw extraction: {file_path.name}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            rows = list(reader)
        
        data_row = rows[2]
        filename = data_row[0]
        
        print(f"   Filename: {filename}")
        print(f"   Raw data length: {len(data_row)}")
        
        # Show values at key positions we're extracting from
        key_positions = [4, 8, 9, 12, 14, 16, 19, 20, 24, 28, 32, 36]  # Common word column positions
        
        print(f"   Values at key positions:")
        for pos in key_positions:
            if pos < len(data_row):
                print(f"     Col {pos:2d}: '{data_row[pos]}'")
        
        # Show actual calculation we're doing
        print(f"   Our algorithm extracts:")
        col_idx = 3
        format_type = 'with_characters' if len(data_row) >= 45 else 'without_characters'
        fields_per_cat = 5 if format_type == 'with_characters' else 4
        
        total = 0
        for cat_idx in range(8):  # 8 categories
            words_col = col_idx + 1
            if words_col < len(data_row):
                try:
                    value = float(data_row[words_col]) if data_row[words_col] else 0
                    total += value
                    print(f"     Cat {cat_idx+1} (col {words_col}): {value}")
                except:
                    print(f"     Cat {cat_idx+1} (col {words_col}): invalid")
            col_idx += fields_per_cat
        
        print(f"   📝 Calculated total: {total}")

def main():
    """Запуск точного анализа колонок."""
    print("🚀 PRECISE COLUMN POSITION DEBUG")
    print("=" * 70)
    
    # Step 1: Analyze exact word positions
    analyze_exact_word_positions()
    
    # Step 2: Compare word column positions between files
    compare_word_column_positions()
    
    # Step 3: Debug raw data extraction
    debug_raw_data_extraction()
    
    print("\n" + "=" * 70)
    print("🏁 Precise column debug completed")

if __name__ == "__main__":
    main()