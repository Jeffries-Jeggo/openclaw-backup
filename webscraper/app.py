import requests
from bs4 import BeautifulSoup

def main():
    url = input("Enter URL to scrape: ")
    
    try:
        # Fetch the page
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get page title
        title = soup.title.string if soup.title else "No title found"
        print(f"\nPage Title: {title}")
        
        # Get all links
        print("\nLinks found on page:")
        for link in soup.find_all('a', href=True):
            print(link['href'])
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")

if __name__ == "__main__":
    main()