
import json
from app.scrapers.pytorch_kr import PyTorchKRScraper

def test_parsing():
    scraper = PyTorchKRScraper()
    # Read the fetched content
    with open('/home/ejpark/.gemini/antigravity/brain/966dd294-0aa9-4b51-86cb-6aab1a880e51/.system_generated/steps/50/content.md', 'r') as f:
        content = f.read()
    
    # Extract the JSON part (it starts after the header)
    json_start = content.find('{"users"')
    json_str = content[json_start:]
    
    # Mock the fetch method to avoid network calls during parsing test
    scraper.fetch = lambda url: "<html><body><div class='post' itemprop='text'>Test Content</div><title>Test Title</title></body></html>"
    
    items = scraper.parse(json_str)
    print(f"Parsed {len(items)} items")
    for item in items:
        print(f"Title: {item.title}, URL: {item.url}")

if __name__ == "__main__":
    test_parsing()
