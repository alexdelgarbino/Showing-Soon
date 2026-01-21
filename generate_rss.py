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
        date_str = target_date.strftime('%B %d (Friday)').replace(' 0', ' ')  # "January 23 (Friday)"
        movies = []
        
        # Get all text content
        page_text = soup.get_text()
        
        # Look for the date section
        if date_str in page_text:
            # Split by the date to find movies listed after it
            parts = page_text.split(date_str)
            if len(parts) > 1:
                # Get the section after the date, but stop at the next date header
                section = parts[1]
                
                # Stop at the next date (look for patterns like "January 25" or "January 30")
                for stop_pattern in ['\nJanuary ', '\nFebruary ', '\nMarch ', '\nApril ', '\nMay ', '\nJune ', 
                                     '\nJuly ', '\nAugust ', '\nSeptember ', '\nOctober ', '\nNovember ', '\nDecember ']:
                    if stop_pattern in section:
                        section = section.split(stop_pattern)[0]
                        break
                
                # Split into lines
                lines = section.split('\n')
                
                # Extract movie titles with their tags
                for line in lines:
                    line = line.strip()
                    
                    # Skip empty lines and non-movie entries
                    if not line or len(line) < 2:
                        continue
                    
                    # Keep the full title with tags like (Expands), (+ IMAX), etc.
                    # But remove platform-only tags like (Theaters), (Netflix), etc.
                    title = line
                    
                    # Remove platform-only suffixes but keep descriptive ones
                    for suffix in [' (Theaters)', ' (Netflix)', ' (HBO Max)', 
                                   ' (Prime Video)', ' (Hulu)', ' (VOD)', ' (Theaters + VOD)', 
                                   ' (Re-Release)', ' (Fathom)']:
                        if suffix in title:
                            title = title.replace(suffix, '')
                    
                    # Only add if it looks like a valid movie title
                    if title and len(title) > 1 and not title[0].isdigit():
                        movies.append(title)
        
        print(f"Found {len(movies)} movies for {date_str}: {movies}")
        return movies
        
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

def create_movie_description(movie_data, release_date):
    """Create HTML description for RSS item"""
    # Use backdrop image instead of poster
    backdrop = movie_data.get('backdrop_path')
    backdrop_url = f"{TMDB_IMAGE_BASE}{backdrop}" if backdrop else ""
    
    overview = html.escape(movie_data.get('overview', 'No synopsis available.'))
    runtime_minutes = movie_data.get('runtime')
    runtime = format_runtime(runtime_minutes) if runtime_minutes else None
    
    # Get certification (rating like PG-13, R, etc.)
    certification = None
    release_dates = movie_data.get('release_dates', {}).get('results', [])
    for country in release_dates:
        if country.get('iso_3166_1') == 'US':
            certs = country.get('release_dates', [])
            if certs and certs[0].get('certification'):
                certification = certs[0].get('certification')
                break
    
    genres = ', '.join([g['name'] for g in movie_data.get('genres', [])])
    
    # Build badges HTML only for known values
    badges_html = ""
    # Always show release date
    badges_html += f"<div style='display: inline-block; background: #f5f5f5; padding: 6px 12px; border-radius: 4px; margin-right: 8px; margin-bottom: 8px; font-size: 14px;'><strong>Release:</strong> {release_date}</div>"
    if certification:
        badges_html += f"<div style='display: inline-block; background: #f5f5f5; padding: 6px 12px; border-radius: 4px; margin-right: 8px; margin-bottom: 8px; font-size: 14px;'><strong>Rating:</strong> {certification}</div>"
    if runtime:
        badges_html += f"<div style='display: inline-block; background: #f5f5f5; padding: 6px 12px; border-radius: 4px; margin-right: 8px; margin-bottom: 8px; font-size: 14px;'><strong>Runtime:</strong> {runtime}</div>"
    if genres:
        badges_html += f"<div style='display: inline-block; background: #f5f5f5; padding: 6px 12px; border-radius: 4px; margin-bottom: 8px; font-size: 14px;'><strong>Genre:</strong> {genres}</div>"
    
    description = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 700px; line-height: 1.6; color: #333;">
        {"<div style='margin-bottom: 20px;'><img src='" + backdrop_url + "' alt='Movie Backdrop' style='max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);' /></div>" if backdrop_url else ""}
        {f"<div style='margin-bottom: 24px;'>{badges_html}</div>" if badges_html else ""}
        <div style="margin-top: 24px; font-size: 15px; line-height: 1.7;">
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
    for title_with_tags in movie_titles:
        # Extract clean title for TMDB search (remove tags like "(Expands)", "(+ IMAX)")
        clean_title = title_with_tags.split('(')[0].strip() if '(' in title_with_tags else title_with_tags
        
        print(f"Fetching details for: {clean_title}")
        movie_data = search_movie_tmdb(clean_title, year)
        
        if movie_data:
            item = SubElement(channel, 'item')
            movie_title = movie_data.get('title', clean_title)
            
            # Add back the tags to the title if they exist
            if '(' in title_with_tags:
                tags = title_with_tags[title_with_tags.index('('):]
                display_title = f"{movie_title} {tags}"
            else:
                display_title = movie_title
            
            SubElement(item, 'title').text = display_title
            SubElement(item, 'link').text = f"https://www.themoviedb.org/movie/{movie_data['id']}"
            SubElement(item, 'description').text = create_movie_description(movie_data, date_str)
            SubElement(item, 'pubDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
            SubElement(item, 'guid').text = f"firstshowing-{movie_data['id']}-{next_friday.strftime('%Y%m%d')}"
            
            # Add backdrop as enclosure
            backdrop = movie_data.get('backdrop_path')
            if backdrop:
                backdrop_url = f"{TMDB_IMAGE_BASE}{backdrop}"
                SubElement(item, 'enclosure', url=backdrop_url, type='image/jpeg')
    
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
