import csv
import requests
from dotenv import load_dotenv
import os
import xml.etree.ElementTree as ET  # Import XML parser

def get_google_books_data(book_title):
    formatted_title = book_title.replace(' ', '+')
    url = f"https://www.googleapis.com/books/v1/volumes?q={formatted_title}&maxResults=1"
    
    response = requests.get(url)
    data = response.json()

    if data['totalItems'] == 0:
        return book_title, 'N/A', 'N/A', 'N/A', 'N/A'

    book_info = data['items'][0]['volumeInfo']
    title = book_info.get('title', 'N/A')
    authors = ', '.join(book_info.get('authors', ['N/A']))
    average_rating = book_info.get('averageRating', 'N/A')
    ratings_count = book_info.get('ratingsCount', 'N/A')

    isbn_13 = 'N/A'
    for identifier in book_info.get('industryIdentifiers', []):
        if identifier['type'] == 'ISBN_13':
            isbn_13 = identifier['identifier']
            break

    return title, authors, average_rating, ratings_count, isbn_13

def fetch_nyt_best_sellers_list(api_key, list_name='hardcover-fiction'):
    url = f"https://api.nytimes.com/svc/books/v3/lists/current/{list_name}.json?api-key={api_key}"
    response = requests.get(url)
    return response.json()['results']['books'] if response.status_code == 200 else []

def get_book_nyt_rank(title, nyt_books):
    for book in nyt_books:
        if book['title'].lower() == title.lower():
            return book['rank']
    return 'N/A' 

def fetch_nyt_reviews(api_key, title):
    url = f"https://api.nytimes.com/svc/books/v3/reviews.json?title={title}&api-key={api_key}"
    response = requests.get(url)
    return response.json()['results'] if response.status_code == 200 else []

def fetch_librarything_reviews(api_key, title):
    url = f"http://www.librarything.com/services/rest/1.1/?method=librarything.ck.getwork&title={title}&apikey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        root = ET.fromstring(response.content)
        rating_element = root.find('.//rating')
        if rating_element is not None:
            return rating_element.text
    return 'N/A'

def update_csv(csv_file_path, book_data):
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Title', 'Author', 'Google Books Average Rating', 'Google Books Ratings Count', 'ISBN', 'NYT Best Seller Rank', 'NYT Review Count', 'LibraryThing Average Rating'])
        for data in book_data:
            writer.writerow(data)

def process_books(csv_file_path, nyt_api_key, librarything_api_key):
    book_titles = []
    with open(csv_file_path, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        book_titles = [row[0] for row in reader]

    nyt_books = fetch_nyt_best_sellers_list(nyt_api_key)
    book_data = []

    for title in book_titles:
        title, authors, google_avg_rating, google_ratings_count, isbn = get_google_books_data(title)
        nyt_rank = get_book_nyt_rank(title, nyt_books)
        nyt_review_count = len(fetch_nyt_reviews(nyt_api_key, title))
        librarything_avg_rating = fetch_librarything_reviews(librarything_api_key, title)
        book_data.append([title, authors, google_avg_rating, google_ratings_count, isbn, nyt_rank, nyt_review_count, librarything_avg_rating])

    update_csv(csv_file_path, book_data)

load_dotenv()  # Load environment variables from .env file
nyt_api_key = os.getenv('NYT_API_KEY')
librarything_api_key = os.getenv('LIBRARYTHING_API_KEY')

csv_file_path = 'books.csv'

process_books(csv_file_path, nyt_api_key, librarything_api_key)
