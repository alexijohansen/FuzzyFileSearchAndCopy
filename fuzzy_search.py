import argparse
import json
import csv
import sys
import os
import shutil
import re
from thefuzz import fuzz

def clean_string(s):
    # Convert to lowercase
    s = s.lower()
    # Remove hyphens, underscores, dots
    s = re.sub(r'[-_\.]', '', s)
    return s

def main():
    parser = argparse.ArgumentParser(description="Fuzzy file search and copy")
    parser.add_argument("config", help="Path to the JSON configuration file")
    args = parser.parse_args()

    config_path = args.config

    if not os.path.exists(config_path):
        print(f"Error: Configuration file '{config_path}' not found.")
        sys.exit(1)

    with open(config_path, 'r') as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in config file: {e}")
            sys.exit(1)

    required_keys = ['data_path', 'column_index', 'source_dir', 'dest_dir']
    for key in required_keys:
        if key not in config:
            print(f"Error: Missing required key '{key}' in config file.")
            sys.exit(1)

    data_path = config['data_path']
    column_index = config['column_index']
    source_dir = config['source_dir']
    dest_dir = config['dest_dir']
    threshold = config.get('match_confidence_threshold', 80) # Default to 80 if not provided

    # Check if files and paths exist
    if not os.path.exists(data_path):
        print(f"Error: CSV file '{data_path}' not found.")
        sys.exit(1)

    if not os.path.isdir(source_dir):
        print(f"Error: Source directory '{source_dir}' not found or is not a directory.")
        sys.exit(1)

    if not os.path.isdir(dest_dir):
        try:
            os.makedirs(dest_dir)
            print(f"Created destination directory: '{dest_dir}'")
        except Exception as e:
            print(f"Error: Could not create destination directory '{dest_dir}': {e}")
            sys.exit(1)

    if not isinstance(column_index, int):
        print(f"Error: 'column_index' in config must be an integer.")
        sys.exit(1)

    # Load CSV file and get names mapped with row numbers
    # List of tuples: (row_num, original_name, cleaned_name)
    csv_items = []
    try:
        with open(data_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            try:
                header = next(reader) # Skip the first row (header)
                platform_name = header[column_index].strip() if len(header) > column_index else "Unknown_Platform"
            except StopIteration:
                print("Error: CSV file is empty.")
                sys.exit(1)
            
            for row_num, row in enumerate(reader, start=2): # Start at 2 because row 1 is header
                if len(row) > column_index:
                    orig_name = row[column_index].strip()
                    if orig_name: # Only add if not empty
                        csv_items.append((row_num, orig_name, clean_string(orig_name)))
                else:
                    print(f"Warning: Row {row_num} has fewer columns than the specified index {column_index}: {row}")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)

    print(f"Successfully loaded {len(csv_items)} names from the CSV.")

    json_out_dir = os.path.join(os.path.dirname(data_path), platform_name)
    try:
        os.makedirs(json_out_dir, exist_ok=True)
        print(f"JSON metadata will be saved to: '{json_out_dir}'")
    except Exception as e:
        print(f"Error: Could not create JSON output directory '{json_out_dir}': {e}")
        sys.exit(1)

    # Get source files
    # List of tuples: (original_filename, cleaned_filename_root)
    source_files = []
    try:
        for filename in os.listdir(source_dir):
            file_path = os.path.join(source_dir, filename)
            if os.path.isfile(file_path):
                # Separate extension
                root, ext = os.path.splitext(filename)
                clean_root = clean_string(root)
                source_files.append((filename, clean_root))
    except Exception as e:
        print(f"Error reading source directory: {e}")
        sys.exit(1)

    print(f"Found {len(source_files)} files in the source directory.")

    matches_found = 0
    files_copied = 0
    unmatched_entries = []

    # Matching logic
    for row_num, orig_csv_name, clean_csv_name in csv_items:
        current_matches = []
        
        # Phase 1: Exact Match
        for orig_file, clean_file in source_files:
            if clean_csv_name == clean_file:
                current_matches.append(orig_file)
        
        # Phase 2: Fuzzy Match (only if no exact matches)
        if not current_matches:
            for orig_file, clean_file in source_files:
                score = fuzz.token_set_ratio(clean_csv_name, clean_file)
                if score >= threshold:
                    current_matches.append(orig_file)
        
        # Copy matched files
        if current_matches:
            matches_found += 1
            new_filenames_list = []
            for orig_file in current_matches:
                src_path = os.path.join(source_dir, orig_file)
                root, ext = os.path.splitext(orig_file)
                
                # Format: 00X_originalroot.ext (using 3-digit padded row number as prefix)
                new_filename = f"{row_num:03d}_{root}{ext}"
                dest_path = os.path.join(dest_dir, new_filename)
                
                try:
                    shutil.copy2(src_path, dest_path)
                    files_copied += 1
                    new_filenames_list.append(new_filename)
                    print(f"Matched '{orig_csv_name}' -> Copied '{orig_file}' to '{new_filename}'")
                except Exception as e:
                    print(f"Error copying '{orig_file}': {e}")
            
            if new_filenames_list:
                metadata = {
                    "platform": platform_name,
                    "name": orig_csv_name,
                    "rom_names": new_filenames_list,
                    "year": None,
                    "genre": None,
                    "publisher": None,
                    "description": None
                }
                
                # Sanitize filename for JSON
                safe_name = re.sub(r'[\\/*?:"<>|]', "", orig_csv_name).strip()
                json_path = os.path.join(json_out_dir, f"{safe_name}.json")
                try:
                    with open(json_path, 'w', encoding='utf-8') as json_file:
                        json.dump(metadata, json_file, indent=4)
                except Exception as e:
                    print(f"Error writing JSON metadata for '{orig_csv_name}': {e}")
        else:
            print(f"No match found for: '{orig_csv_name}'")
            unmatched_entries.append(f"Row {row_num:03d}: {orig_csv_name}")

    print(f"\nSummary: Found matches for {matches_found} out of {len(csv_items)} CSV entries.")
    print(f"Total files copied: {files_copied}")

    if unmatched_entries:
        log_path = os.path.join(dest_dir, "log_no_match.txt")
        try:
            with open(log_path, 'w', encoding='utf-8') as log_file:
                for entry in unmatched_entries:
                    log_file.write(entry + '\n')
            print(f"Logged {len(unmatched_entries)} unmatched entries to '{log_path}'.")
        except Exception as e:
            print(f"Error writing unmatched log: {e}")

if __name__ == "__main__":
    main()
