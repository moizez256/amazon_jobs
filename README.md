# Amazon Jobs Scraper

A Scrapy spider with Playwright integration to scrape job listings from Amazon's careers website.

## Features

- Scrapes job listings from [Amazon.jobs](https://www.amazon.jobs)
- Uses Playwright for JavaScript rendering and interaction
- Handles pagination automatically
- Extracts comprehensive job details including:
  - Job ID
  - title and URL
  - Location and posting date
  - Short and full descriptions
  - Basic and preferred qualifications

## Technologies

- Python 3.8+
- Scrapy
- Playwright
- Scrapy-Playwright (https://github.com/scrapy-plugins/scrapy-playwright)

## Installation

1. Clone the repository:
  ```bash
  git clone https://github.com/yourusername/amazon-jobs-scraper.git
  cd amazon-jobs-scraper
  ```
2. Create and activate a virtual environment:
  ```bash
  python -m venv venv
  source venv/bin/activate  # On Windows use `venv\Scripts\activate`
  ```
3. Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```
4. Install Playwright Chormium:
  ```bash
  python3 -m playwright install chromium
  ```
5. Install Chormium dependencies:
  ```bash
  python3 -m playwright install-deps chromium
  ```

## Usage
### Running the Spider
  ```bash
  scrapy crawl amazon_jobs -O output.json
  ```

### Configuration Options
Set these in settings.py or as command line arguments:

```python
CONCURRENT_REQUESTS: 4 #Number of concurrent requests

DOWNLOAD_DELAY: 2 #Delay between requests

PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT: 60000 #Page load timeout
```

### Output Formats
Supported output formats:

- JSON (-O output.json)
- CSV (-O output.csv)
- JSON Lines (-O output.jl)

### Testing
Run tests with pytest:
  ```bash
  pytest tests/ -v
  ```

## License
Distributed under the MIT License. See LICENSE for more information.

## Contact
José Monroy - jmonroym@outlook.cl

Project Link: https://github.com/moizez256/amazon-jobs
