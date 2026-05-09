# Saturday Lotto Scraper

A small Python scraper that can:

- fetch Saturday Lotto archive pages by year
- fetch any webpage URL and extract number groups from its text
- save the results to a timestamped CSV file

## Requirements

- Python 3.10+ recommended
- Internet access
- The Python packages listed in `requirements.txt`

## Install

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

Start the scraper with:

```bash
python saturday-lotto-scraper.py
```

The program will prompt for input. You can enter:

- one or more years, for example `2024` or `2022,2023,2024`
- one or more URLs, for example `https://example.com`
- a mix of years and URLs separated by commas

## What It Does

### Year mode

When you enter a year, the scraper visits this archive format:

```text
https://australia.national-lottery.com/saturday-lotto/results-archive-YYYY
```

It tries to extract:

- draw number
- draw date
- winning numbers
- total winners
- source URL

### URL mode

When you enter a URL, the script downloads the page, scans the text, and extracts groups of numbers that appear together. If it does not find grouped numbers, it falls back to all standalone numbers on the page.

## Output

Results are written to a CSV file named like this:

```text
parsed_results_<timestamp>.csv
```

## Notes

- If dependencies are missing, the script prints install instructions and exits.
- The site structure may change, which can affect how much data is extracted.
- The script pauses briefly between requests to be polite to the server.

## Files

- `saturday-lotto-scraper.py` - main scraper script
- `requirements.txt` - Python dependencies
