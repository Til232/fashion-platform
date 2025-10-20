# Full code for Fashion Platform prototype (small brands, AR try-on, custom filtering).
# Run with: python app.py or python3 app.py (visit localhost:5000 or fashion-platform.til232.github.io later).
# Notes: Uses SQLite for clothes database. AI filter via keyword match. AR sim as text (upgrade to GlamAR API).
# Modern design with avatar on right, clothes on left, "Try On" button.

from flask import Flask, request, render_template, send_from_directory, redirect, url_for
import os
import sqlite3
import pandas as pd
import requests

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database setup (SQLite for clothes from small brands).
conn = sqlite3.connect('fashion_db.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS clothes
                  (id INTEGER PRIMARY KEY, name TEXT, price REAL, color TEXT, sizes TEXT, image_url TEXT, affiliate_link TEXT, brand_story TEXT)''')
conn.commit()

# Sample data for small brands (replace with uploads).
sample_data = [
    ('Eco Tee - Brand A (15k followers)', 29.99, 'Black', 'S,M,L', '/uploads/tee.jpg', 'https://flexoffers.com/tee?tag=yourid', 'Brand A: Sustainable cotton from upcycled fabrics, launched by a 20k IG creator.'),
    ('Vintage Jacket - Brand B (50k followers)', 59.99, 'Blue', 'M,L', '/uploads/jacket.jpg', 'https://flexoffers.com/jacket?tag=yourid', 'Brand B: Retro vibes from a 60k TikTok designer, eco-conscious production.'),
    ('Casual Shorts - Brand C (30k followers)', 34.99, 'Black', 'S,M', '/uploads/shorts.jpg', 'https://flexoffers.com/shorts?tag=yourid', 'Brand C: Comfortable designs from a 30k IG artisan.'),
]
for data in sample_data:
    cursor.execute('''INSERT OR IGNORE INTO clothes (name, price, color, sizes, image_url, affiliate_link, brand_story) VALUES (?, ?, ?, ?, ?, ?, ?)''', data)
conn.commit()

# Simulated AR try-on (text; replace with real GlamAR API).
def simulate_try_on(item_name, color, image_url, user_photo):
    try_on_desc = f"AR Try-On: {item_name} in {color} fits your avatar perfectly! (Image: {image_url})"
    # Real AR: Uncomment (get key from glamar.ai).
    # response = requests.post('https://api.glamar.io/tryon', json={'item_image': image_url, 'user_photo': user_photo, 'key': 'YOUR_GLAMAR_KEY'})
    # if response.status_code == 200:
    #     return response.json()['try_on_image_url']
    return try_on_desc

# Home page with filtering and try-on.
@app.route('/', methods=['GET', 'POST'])
def home():
    user_photo = '/uploads/default_avatar.jpg'
    if request.method == 'POST':
        if 'photo' in request.files:  # Photo upload
            file = request.files.get('photo')
            if file:
                filename = file.filename
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                user_photo = f'/uploads/{filename}'
        elif 'brand_name' in request.form:  # Brand upload
            brand_name = request.form.get('brand_name')
            price = float(request.form.get('price', 0))
            color = request.form.get('color', 'Unknown')
            sizes = request.form.get('sizes', 'S,M,L')
            file = request.files.get('image')
            affiliate_link = request.form.get('affiliate_link', 'https://flexoffers.com/default?tag=yourid')
            brand_story = request.form.get('brand_story', 'Brand story not provided')
            image_url = '/uploads/default.jpg'
            if file:
                filename = file.filename
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                image_url = f'/uploads/{filename}'
            
            cursor.execute('''INSERT INTO clothes (name, price, color, sizes, image_url, affiliate_link, brand_story)
                           VALUES (?, ?, ?, ?, ?, ?, ?)''', (brand_name, price, color, sizes, image_url, affiliate_link, brand_story))
            conn.commit()
            return redirect(url_for('home'))

    # Fetch all clothes for display.
    cursor.execute('SELECT * FROM clothes')
    clothes = pd.DataFrame(cursor.fetchall(), columns=['id', 'name', 'price', 'color', 'sizes', 'image_url', 'affiliate_link', 'brand_story']).to_dict('records')

    # AI filter (simple keyword match from free text).
    filter_text = request.args.get('filter', '').lower()
    if filter_text:
        clothes = [item for item in clothes if any(keyword in item['name'].lower() or item['color'].lower() for keyword in filter_text.split())]

    return render_template('index.html', clothes=clothes, user_photo=user_photo)

# Serve uploaded files.
@app.route('/uploads/<filename>')
def uploads(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# Try-on route for individual items.
@app.route('/try_on/<int:item_id>', methods=['GET'])
def try_on(item_id):
    cursor.execute('SELECT * FROM clothes WHERE id = ?', (item_id,))
    item = cursor.fetchone()
    if item:
        item = dict(zip(['id', 'name', 'price', 'color', 'sizes', 'image_url', 'affiliate_link', 'brand_story'], item))
        user_photo = request.args.get('user_photo', '/uploads/default_avatar.jpg')
        try_on_desc = simulate_try_on(item['name'], item['color'], item['image_url'], user_photo)
        return render_template('try_on.html', item=item, try_on_desc=try_on_desc, user_photo=user_photo)
    return "Item not found", 404

if __name__ == "__main__":
    app.run(debug=True)