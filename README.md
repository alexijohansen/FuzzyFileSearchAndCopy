# FuzzyFileSearchAndCopy

A Python project for finding files in a directory using fuzzy string matching.

This script reads a JSON configuration file to extract names from a specified CSV file column, finds corresponding files in a source directory using exact and fuzzy matching (via the `rapidfuzz` library), copies them to a destination directory with padded numeric prefixes, and generates rich JSON metadata files.

## Prerequisites

- Python 3.6 or higher

## Installation

1. Clone this repository or download the source code.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   **Using Anaconda:**
   If you are using an Anaconda environment, simply activate your environment before running the pip install command:
   ```bash
   conda activate your_env_name
   pip install -r requirements.txt
   ```

## Configuration

The script requires a JSON configuration file as input. Create a JSON file (e.g., `config.json`) with the following structure:

```json
{
  "data_path": "path/to/your/input.csv",
  "column_index": 0,
  "source_dir": "path/to/source/files",
  "dest_dir": "path/to/destination/files",
  "match_confidence_threshold": 80
}
```

- `data_path`: Path to the CSV file containing the names.
- `column_index`: Integer representing the 0-based index of the column containing the names to process. The script will skip the first row (header).
- `source_dir`: Path to the folder containing the files to search through.
- `dest_dir`: Path to the folder where matched files will be copied.
- `match_confidence_threshold`: (Optional) Integer from 0 to 100 representing the minimum confidence score required for a fuzzy match to be considered successful. Defaults to 80.

## Usage

Run the script from the command line, passing the path to your configuration file:

```bash
python fuzzy_search.py config.json
```

## How It Works

The script follows this process:
1. Validates configuration and loads data.
2. Cleans the strings of both the CSV names and the source file names (removes extensions, converts to lowercase, and removes hyphens, underscores, and dots).
3. **Exact Match Check**: First, checks if there is an exact match between the cleaned strings.
4. **Fuzzy Match Check**: If no exact match is found, uses `rapidfuzz` to calculate a confidence score. If the score is greater than or equal to the `match_confidence_threshold`, it's considered a match.
5. **Copy & Rename**: Any matched files are copied to the `dest_dir`. The newly copied files are renamed to preserve their original name, but a 3-digit padded prefix is added representing the CSV row number of the match (e.g. `002_original_file.zip`).
6. **JSON Metadata Generation**: For every CSV entry that produces a match, a JSON file is created in a subfolder (named after the CSV column header) located in the same directory as the CSV data file. The JSON file contains the platform, original name, matched filenames, and placeholder fields for year, genre, publisher, and description.

## Trustworthiness of `rapidfuzz`

Yes, `rapidfuzz` is highly trustworthy. It is a modern, much faster drop-in replacement for the older `fuzzywuzzy` and `thefuzz` libraries. It is implemented in C++ and provides precompiled binaries for Apple Silicon (M-series Macs), avoiding build errors while providing identical fuzzy matching capabilities.
