# Full code for fashion platform prototype (small brands, AR try-on, custom kits).
# Run with: python app.py (visit localhost:5000 or fashion-platform.til232.github.io later).
# Notes: Uses SQLite3 (built-in) for clothes database. AR sim as text (upgrade to GlamAR API). Rename placeholder later.
# Fixed venv issue for Python 3.14.0 on Mac.

from flask import Flask, request, render_template, send_from_directory, redirect, url_for
import os
import sqlite3
import pandas as pd
import requests

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database setup (SQLite3 for clothes from small brands).
conn = sqlite3.connect('fashion_db.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS clothes
                  (id INTEGER PRIMARY KEY, name TEXT, price REAL, color TEXT, sizes TEXT, image_url TEXT, affiliate_link TEXT, brand_story TEXT)''')
conn.commit()

# Sample data for small brands (replace with uploads).
sample_data = [
    ('Eco Tee - Brand A (15k followers)', 29.99, 'Black', 'S,M,L', '/uploads/tee.jpg', 'https://flexoffers.com/tee?tag=yourid', 'Brand A: Sustainable cotton from upcycled fabrics, launched by a 20k IG creator.'),
    ('Vintage Jacket - Brand B (50k followers)', 59.99, 'Blue', 'M,L', '/uploads/jacket.jpg', 'https://flexoffers.com/jacket?tag=yourid', 'Brand B: Retro vibes from a 60k TikTok designer, eco-conscious production.'),
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

# Home/Questionnaire page.
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if 'size' in request.form:  # User shopping
            size = request.form.get('size', 'M')
            preferences = request.form.get('preferences', 'plain black, no print, shorts, no shoes, no hat, use photo hat')
            file = request.files.get('photo')
            user_photo = '/uploads/default_avatar.jpg'
            if file:
                filename = file.filename
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                user_photo = f'/uploads/{filename}'
            
            # Algorithm: Filter database based on preferences.
            cursor.execute('SELECT * FROM clothes')
            df = pd.DataFrame(cursor.fetchall(), columns=['id', 'name', 'price', 'color', 'sizes', 'image_url', 'affiliate_link', 'brand_story'])
            filtered = df.copy()
            pref_list = [p.strip().lower() for p in preferences.split(',')]
            if 'plain' in pref_list or 'black' in pref_list:
                filtered = filtered[filtered['color'].str.lower().str.contains('black', na=False)]
            if 'no print' in pref_list:
                filtered = filtered[~filtered['name'].str.lower().str.contains('print', na=False)]
            if 'no shoes' in pref_list:
                filtered = filtered[~filtered['name'].str.lower().str.contains('shoes', na=False)]
            if 'shorts' in pref_list:
                filtered = filtered[filtered['name'].str.lower().str.contains('shorts', na=False)]
            if 'use photo hat' in pref_list:
                filtered = filtered[filtered['name'].str.lower().str.contains('hat', na=False)]  # Adjust logic for hat from photo
            
            kit = []
            total_price = 0.0
            for _, item in filtered.iterrows():
                if total_price + item['price'] <= 150:  # Cap budget
                    try_on = simulate_try_on(item['name'], item['color'], item['image_url'], user_photo)
                    kit.append({
                        'name': item['name'],
                        'price': item['price'],
                        'sizes': item['sizes'].split(','),
                        'color': item['color'],
                        'image_url': item['image_url'],
                        'link': item['affiliate_link'],
                        'brand_story': item['brand_story'],
                        'try_on': try_on
                    })
                    total_price += item['price']
            
            return render_template('index.html', kit=kit, total_price=total_price, user_photo=user_photo)
        
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

    return render_template('index.html')

# Serve uploaded files.
@app.route('/uploads/<filename>')
def uploads(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)