import multiprocessing
from flask import Blueprint, request, render_template, redirect, url_for
from pymongo import MongoClient, ASCENDING, DESCENDING
import os
import requests
import logging

scraping_bp = Blueprint('scraping', __name__)

client = MongoClient('mongodb://mongo:27017/projekt')
db = client['projekt']
collection = db['televisions']

ITEMS_PER_PAGE = 10

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@scraping_bp.route('/', methods=['GET'])
def home():
    products = list(collection.find())
    message = ""
    if not products:
        message = "Twoja baza jest pusta. Uruchom skrapowanie."
    else:
        message = "Twoja baza ma dane."

    return render_template('index.html', products=products, message=message)

def get_scrapers():
    scrapers = []
    for file in os.listdir('/app/scrapers'):
        if file.startswith('scrape_') and file.endswith('.py'):
            scrapers.append(file[:-3])
    return scrapers

def run_scraper(script_name):
    url = 'http://scraper:5001/run_scraper'
    response = requests.post(url, json={'script_name': script_name})
    if response.status_code == 200:
        logger.info(f'Successfully started {script_name}')
    else:
        logger.error(f'Error starting {script_name}: {response.json()}')

@scraping_bp.route('/start_scraping', methods=['POST'])
def start_scraping():
    scrapers = get_scrapers()
    processes = []

    collection.delete_many({})

    for scraper in scrapers:
        p = multiprocessing.Process(target=run_scraper, args=(scraper,))
        processes.append(p)
        p.start()

    for process in processes:
        process.join()

    return redirect(url_for('scraping.home'))

@scraping_bp.route('/results', methods=['GET'])
def results():
    if collection.count_documents({}) == 0:
        return redirect(url_for('scraping.home'))

    search_term = request.args.get('search_term', '')
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')
    page = int(request.args.get('page', 1))

    sort_parameter = [(sort_by, ASCENDING if sort_order == 'asc' else DESCENDING)]

    query = {"name": {"$regex": f"{search_term}", "$options": 'i'}}

    total_products = collection.count_documents(query)
    products = list(collection.find(query).sort(sort_parameter).skip((page - 1) * ITEMS_PER_PAGE).limit(ITEMS_PER_PAGE))
    total_pages = (total_products + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    return render_template('results.html', products=products, products_count=total_products, page=page, total_pages=total_pages, search_term=search_term, sort_by=sort_by, sort_order=sort_order)
