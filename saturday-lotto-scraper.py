import sys
import re
import time
import random

try:
    import requests
    from bs4 import BeautifulSoup
    import pandas as pd
except ImportError as e:
    print("Missing or unresolved Python dependencies:", e)
    print()
    print("To fix: create and activate a virtual environment, then install requirements:")
    print("  python3 -m venv .venv")
    print("  source .venv/bin/activate")
    print("  pip install -r requirements.txt")
    print()
    print("Or install directly:")
    print("  pip install requests beautifulsoup4 pandas")
    sys.exit(1)

BASE_URL = "https://australia.national-lottery.com/saturday-lotto/results-archive-{}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()

def extract_numbers(text):
    nums = re.findall(r"\b\d+\b", text)
    return nums

def scrape_saturday_lotto_year(year):
    url = BASE_URL.format(year)
    print(f"Fetching: {url}")

    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    page_text = soup.get_text("\n", strip=True)

    # Try to locate rows in HTML tables first
    tables = soup.find_all("table")
    results = []

    for table in tables:
        rows = table.find_all("tr")
        for row in rows[1:]:
            cols = row.find_all(["td", "th"])
            if len(cols) < 3:
                continue

            col1 = clean_text(cols[0].get_text(" ", strip=True))
            col2 = clean_text(cols[1].get_text(" ", strip=True))
            col3 = clean_text(cols[2].get_text(" ", strip=True))

            draw_match = re.search(r"Draw\s+(\d+)", col1, re.IGNORECASE)
            date_match = re.search(r"(\d{1,2}\s+\w+,\s+\d{4})", col1)

            if draw_match:
                draw_no = draw_match.group(1)
                draw_date = date_match.group(1) if date_match else None

                numbers = extract_numbers(col2)
                total_winners = col3

                results.append({
                    "year": year,
                    "draw_no": draw_no,
                    "draw_date": draw_date,
                    "winning_numbers_raw": col2,
                    "numbers_extracted": ", ".join(numbers),
                    "total_winners": total_winners,
                    "source_url": url
                })

    # Fallback: if table parsing fails, inspect page text pattern
    if not results:
        lines = [clean_text(line) for line in page_text.splitlines() if clean_text(line)]

        current_draw = None
        current_date = None

        for i, line in enumerate(lines):
            draw_match = re.search(r"Draw\s+(\d+)", line, re.IGNORECASE)
            date_match = re.search(r"(\d{1,2}\s+\w+,\s+\d{4})", line)

            if draw_match:
                current_draw = draw_match.group(1)
                current_date = date_match.group(1) if date_match else None

                next_lines = " ".join(lines[i+1:i+5])
                nums = extract_numbers(next_lines)

                results.append({
                    "year": year,
                    "draw_no": current_draw,
                    "draw_date": current_date,
                    "winning_numbers_raw": next_lines,
                    "numbers_extracted": ", ".join(nums),
                    "total_winners": None,
                    "source_url": url
                })

    df = pd.DataFrame(results)

    if df.empty:
        print("No results found. The site structure may have changed.")
    else:
        print(f"Found {len(df)} rows for {year}")

    return df

def parse_numbers_from_url(url):
    url = url.strip()
    if not re.match(r"https?://", url):
        url = "http://" + url

    print(f"Fetching: {url}")
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    page_text = soup.get_text("\n", strip=True)

    # Find groups of consecutive numbers (at least 2 numbers together)
    group_pattern = re.compile(r"\b\d+\b(?:[ ,;/\-]+\b\d+\b){1,}")
    groups = group_pattern.findall(page_text)

    rows = []
    for g in groups:
        nums = re.findall(r"\b\d+\b", g)
        rows.append({
            "url": url,
            "snippet": (g[:200] + "...") if len(g) > 200 else g,
            "numbers_extracted": ", ".join(nums),
            "group_length": len(nums)
        })

    # If no multi-number groups, fall back to all standalone numbers
    if not rows:
        all_nums = re.findall(r"\b\d+\b", page_text)
        if all_nums:
            rows.append({
                "url": url,
                "snippet": (page_text[:200] + "...") if len(page_text) > 200 else page_text,
                "numbers_extracted": ", ".join(all_nums),
                "group_length": len(all_nums)
            })

    df = pd.DataFrame(rows)
    return df


def main():
    user_input = input("Enter year(s) (e.g. 2022,2023) or URL(s) (comma-separated): ").strip()
    tokens = [t.strip() for t in user_input.split(",") if t.strip()]

    urls = [t for t in tokens if re.match(r"https?://", t) or t.startswith("www.") or "." in t]
    years = [t for t in tokens if t.isdigit()]

    frames = []

    # Process URLs first
    for url in urls:
        try:
            df = parse_numbers_from_url(url)
            if not df.empty:
                frames.append(df)
        except Exception as e:
            print(f"Failed to parse {url}: {e}")
        time.sleep(random.uniform(1, 2.0))

    # Process years using existing lotto scraper
    for year in years:
        try:
            df = scrape_saturday_lotto_year(year)
            if not df.empty:
                frames.append(df)
        except Exception as e:
            print(f"Failed for {year}: {e}")
        time.sleep(random.uniform(1, 2.5))

    if frames:
        final_df = pd.concat(frames, ignore_index=True, sort=False)
        file_name = f"parsed_results_{int(time.time())}.csv"
        final_df.to_csv(file_name, index=False, encoding="utf-8-sig")
        print(f"Saved to {file_name}")
        print(final_df.head(10))
    else:
        print("No results found for provided inputs.")


if __name__ == "__main__":
    main()
