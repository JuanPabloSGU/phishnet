import requests;
import time;

def get_html_content(url, timeout=5, retries=2):
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            print(f"Attempt {attempt + 1} failed with error: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    print(f"Failed to fetch {url} after {retries} attempts.")
    return None

def main():
    url = 'https://www.google123.com/'
    html_content = get_html_content(url)
    if html_content:
        print("HTML content retrieved successfully.")
        with open('test.html', 'wb') as f:
            f.write(html_content)
    else:
        print("Failed to retrieve HTML content.")


if __name__ == "__main__":
    main()