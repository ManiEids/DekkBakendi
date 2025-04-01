# DekkBakendi - Icelandic Tire Aggregator

A web application that scrapes tire data from multiple Icelandic retailers, combines it into a unified database, and provides a simple dashboard for data visualization and management.

## Features

- Web scraping of major Icelandic tire retailers (Klettur, Dekkjahollin, Mitra, N1, Nesdekk, Dekkjasalan)
- Data normalization and merging into a unified format
- PostgreSQL database integration with Neon
- Web dashboard for running scrapers and viewing data
- API endpoints for accessing tire data
- Automated background scraping via scheduled tasks

## Architecture

This application consists of:

1. **Scrapy Spiders**: Individual scrapers for each tire retailer
2. **Flask Web App**: Dashboard UI and API endpoints
3. **Database Integration**: PostgreSQL database on Neon
4. **Background Job**: Daily scheduled scraper updates

## Development Setup

1. Clone the repository:
   ```
   git clone https://github.com/ManiEids/DekkBakendi.git
   cd DekkBakendi
   ```

2. Create a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   pip install -e .
   ```

4. Set environment variables:
   ```
   cp .env.example .env
   # Edit .env with your database credentials
   ```

5. Run the development server:
   ```
   python app.py
   ```

## Deployment

This application is configured for deployment on Render.com:

1. Push your code to GitHub
2. Connect your GitHub repository to Render
3. Create a new Web Service with the following settings:
   - Build Command: `pip install -r requirements.txt && python deploy_setup.py && pip install -e .`
   - Start Command: `python copy_spiders.py && gunicorn app:app --timeout 600 --workers 1`
   - Environment Variables: Set DATABASE_URL to your Neon PostgreSQL connection string

## Database Setup

1. Create a new PostgreSQL database on Neon.tech
2. Set the DATABASE_URL environment variable
3. On first run, the application will create the necessary tables
4. Run the scrapers to populate the database

## API Endpoints

- `/`: Dashboard UI
- `/data/<filename>`: Access JSON data files
- `/run-scrapers`: Run all scrapers
- `/run-spider/<spider_name>`: Run a specific spider
- `/update-database`: Update the database from scraped JSON files
- `/logs`: Stream scraper logs
- `/healthz`: Health check endpoint

## License

MIT

## Authors

- Mani Eids
