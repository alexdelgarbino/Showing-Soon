#!/usr/bin/env python3
"""
Generate RSS feed for FirstShowing schedule with TMDB movie details
Posts every Monday at 9am for the upcoming Friday
"""
from datetime import datetime, timedelta
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import requests
from bs4 import BeautifulSoup
import html

TMDB_API_KEY = 'b5d2f69cf0491ce4441c4d04c4befc3d'
TMDB_BASE_URL = 'https://api.themoviedb.org/3'
TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/w500'

def get_next_friday():
    """Get the date of the upcoming Friday"""
    today = datetime.now()
    days_ahead = 4 - today.weekday()  # Friday is 4
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return today + timedelta(days_ahead)

def search_movie_tmdb(title, year):
    """Search for a movie on TMDB and return details"""
    try:
        search_url = f'{TMDB_BASE_URL}/search/movie'
        params = {
            'api_key': TMDB_API_KEY,
            'query': title,
            'year': year
        }
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        results = response.json().get('results', [])
        
        if not results:
            # Try without year
            params.pop('year')
            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            results = response.json().get('results', [])
        
        if results:
            movie_id = results[0]['id']
            # Get full movie details
            details_url = f'{TMDB_BASE_URL}/movie/{movie_id}'
            params = {'api_key': TMDB_API_KEY}
            response = requests.get(details_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Error fetching TMDB data for '{title}': {e}")
    return None

def scrape_firstshowing_schedule(year, target_date):
    """Scrape movie titles from FirstShowing schedule page"""
    try:
        url = f'https://www.firstshowing.net/schedule{year}/'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the date section for the target Friday
        date_str = target_date.strftime('%B %d').replace(' 0', ' ')  # "January 23"
        movies = []
        
        # Find all text content
        page_text = soup.get_text()
        
        # Look for the date section
        if date_str in page_text:
            # Split by the date to find movies listed after it
            parts = page_text.split(date_str)
            if len(parts) > 1:
                # Get the section after the date
                section = parts[1].split('\n')
                
                # Extract movie titles (they're usually on their own lines)
                for line in section[:30]:  # Check first 30 lines after date
                    line = line.strip()
                    # Skip empty lines, dates, and common non-movie text
                    if (line and 
                        len(line) > 2 and 
                        not line.startswith('(') and
                        'Friday' not in line and
                        'Theaters' not in line and
                        'IMAX' not in line and
                        'Expands' not in line and
                        'HBO' not in line and
                        'Netflix' not in line and
                        'Amazon' not in line):
                        # Clean up the title
                        title = line.split('(')[0].strip()  # Remove anything in parentheses
                        if title and len(title) > 2:
                            movies.append(title)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_movies = []
        for movie in movies:
            if movie not in seen:
                seen.add(movie)
                unique_movies.append(movie)
        
        return unique_movies[:15]  # Return up to 15 movies
    except Exception as e:
        print(f"Error scraping FirstShowing: {e}")
        return []

def format_runtime(minutes):
    """Convert runtime in minutes to readable format"""
    if not minutes:
        return "Runtime unknown"
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"

def create_movie_description(movie_data):
    """Create HTML description for RSS item"""
    poster = movie_data.get('poster_path')
    poster_url = f"{TMDB_IMAGE_BASE}{poster}" if poster else ""
    
    overview = html.escape(movie_data.get('overview', 'No synopsis available.'))
    runtime = format_runtime(movie_data.get('runtime'))
    
    # Get certification (rating like PG-13, R, etc.)
    certification = "Not Rated"
    release_dates = movie_data.get('release_dates', {}).get('results', [])
    for country in release_dates:
        if country.get('iso_3166_1') == 'US':
            certs = country.get('release_dates', [])
            if certs:
                certification = certs[0].get('certification', 'Not Rated')
                break
    
    genres = ', '.join([g['name'] for g in movie_data.get('genres', [])])
    
    description = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 700px; line-height: 1.6; color: #333;">
        {"<div style='margin-bottom: 20px;'><img src='" + poster_url + "' alt='Movie Poster' style='max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);' /></div>" if poster_url else ""}
        <div style="margin-bottom: 20px;">
            <div style="display: inline-block; background: #f5f5f5; padding: 6px 12px; border-radius: 4px; margin-right: 8px; margin-bottom: 8px; font-size: 14px;">
                <strong>Rating:</strong> {certification}
            </div>
            <div style="display: inline-block; background: #f5f5f5; padding: 6px 12px; border-radius: 4px; margin-right: 8px; margin-bottom: 8px; font-size: 14px;">
                <strong>Runtime:</strong> {runtime}
            </div>
            {f"<div style='display: inline-block; background: #f5f5f5; padding: 6px 12px; border-radius: 4px; margin-bottom: 8px; font-size: 14px;'><strong>Genre:</strong> {genres}</div>" if genres else ""}
        </div>
        <div style="margin-top: 16px; font-size: 15px; line-height: 1.7;">
            {overview}
        </div>
    </div>
    """
    return description.strip()

def generate_rss():
    """Generate RSS feed with upcoming Friday's schedule and movie details"""
    next_friday = get_next_friday()
    year = next_friday.year
    date_str = next_friday.strftime("%B %d, %Y")
    
    print(f"Generating RSS feed for {date_str}")
    print(f"Scraping FirstShowing schedule...")
    
    # Get movie titles from FirstShowing
    movie_titles = scrape_firstshowing_schedule(year, next_friday)
    
    # Create RSS structure
    rss = Element('rss', version='2.0')
    channel = SubElement(rss, 'channel')
    
    SubElement(channel, 'title').text = 'FirstShowing Weekly Movie Releases'
    SubElement(channel, 'link').text = f'https://www.firstshowing.net/schedule{year}/'
    SubElement(channel, 'description').text = f'Detailed movie releases for {date_str}'
    SubElement(channel, 'language').text = 'en-us'
    SubElement(channel, 'lastBuildDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    # Fetch details for each movie
    for title in movie_titles:
        print(f"Fetching details for: {title}")
        movie_data = search_movie_tmdb(title, year)
        
        if movie_data:
            item = SubElement(channel, 'item')
            movie_title = movie_data.get('title', title)
            SubElement(item, 'title').text = f"{movie_title} - Releases {date_str}"
            SubElement(item, 'link').text = f"https://www.themoviedb.org/movie/{movie_data['id']}"
            SubElement(item, 'description').text = create_movie_description(movie_data)
            SubElement(item, 'pubDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
            SubElement(item, 'guid').text = f"firstshowing-{movie_data['id']}-{next_friday.strftime('%Y%m%d')}"
            
            # Add poster as enclosure
            poster = movie_data.get('poster_path')
            if poster:
                poster_url = f"{TMDB_IMAGE_BASE}{poster}"
                SubElement(item, 'enclosure', url=poster_url, type='image/jpeg')
    
    # Pretty print XML
    xml_str = minidom.parseString(tostring(rss)).toprettyxml(indent='  ')
    
    # Write to file
    with open('feed.xml', 'w', encoding='utf-8') as f:
        f.write(xml_str)
    
    print(f"\nRSS feed generated successfully!")
    print(f"Found {len(movie_titles)} movies for {date_str}")
    print(f"Output: feed.xml")

if __name__ == '__main__':
    generate_rss()
