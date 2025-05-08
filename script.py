import requests
import time
import asyncio
import aiohttp
import ujson

# Retry logic with exponential backoff
def retry_with_backoff(func, max_retries=3):
    def wrapper(*args, **kwargs):
        retries = 0
        backoff = 1  # Initial backoff time
        while retries < max_retries:
            try:
                return func(*args, **kwargs)
            except requests.RequestException as e:
                retries += 1
                print(f"Error occurred: {e}. Retrying in {backoff} seconds...")
                time.sleep(backoff)
                backoff *= 2  # Exponential backoff
        raise Exception(f"Failed after {max_retries} retries.")
    return wrapper

# Function to fetch a page with retry mechanism
@retry_with_backoff
def fetch_page(page):
    url = f"https://akatsuki.gg/api/v1/beatmaps?p={page}&l=50"
    response = requests.get(url, timeout=5)  # Reduced timeout for faster retries
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()  # Raise an error for non-200 responses

# Function to process and extract only the relevant information
def process_beatmaps(beatmaps):
    result = []
    for beatmap in beatmaps:
        beatmap_id = beatmap["beatmap_id"]
        ranked = beatmap["ranked"]
        result.append((beatmap_id, ranked))
    return result

# Function to write the beatmaps incrementally to a file
def write_beatmaps_incrementally(beatmaps, filename):
    with open(filename, 'a') as file:
        for beatmap_id, ranked in beatmaps:
            file.write(f"Beatmap ID: {beatmap_id}, Ranked: {ranked}\n")

# Main function to fetch all pages and process the beatmaps
def fetch_all_beatmaps():
    page = 1
    beatmap_count = 0
    all_beatmaps = []

    # Start timing
    start_time = time.time()

    # Open the output file in append mode to continue writing
    output_filename = "beatmaps.txt"

    while True:
        # Fetch the page data
        page_data = fetch_page(page)
        beatmaps = page_data.get("beatmaps", [])

        # Process the current page's beatmaps
        processed_beatmaps = process_beatmaps(beatmaps)
        all_beatmaps.extend(processed_beatmaps)

        # Write the fetched beatmaps to file incrementally
        write_beatmaps_incrementally(processed_beatmaps, output_filename)

        # Update the total count of beatmaps
        beatmap_count += len(processed_beatmaps)

        # Print how many beatmaps have been fetched so far
        print(f"Fetched {beatmap_count} beatmaps so far...")

        # If the page has fewer than 50 items, we assume it's the last page
        if len(beatmaps) < 50:
            break
        
        # Increment to fetch the next page
        page += 1

    # End timing
    end_time = time.time()
    print(f"Total time taken: {end_time - start_time} seconds")
    
    return all_beatmaps, beatmap_count

# Main execution
if __name__ == "__main__":
    # Fetch beatmaps and count how many were fetched
    all_beatmaps, total_beatmaps_fetched = fetch_all_beatmaps()

    # Final message
    print(f"Total beatmaps fetched: {total_beatmaps_fetched}")
