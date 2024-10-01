from flask import Flask, render_template, request, redirect, url_for
import sqlite3

# Initialize Flask app
app = Flask(__name__)

# Database setup
DATABASE = 'cloud_service.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS providers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        user_hash TEXT NOT NULL,
                        cpu_cores INTEGER NOT NULL,
                        ram INTEGER NOT NULL,
                        storage INTEGER NOT NULL,
                        price_per_core REAL NOT NULL,
                        price_per_gb_ram REAL NOT NULL,
                        price_per_gb_storage REAL NOT NULL
                      )''')
    conn.commit()
    conn.close()

init_db()

# Route for home page
@app.route('/')
def home():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM providers")
    providers = cursor.fetchall()
    conn.close()
    return render_template('home.html', providers=providers)

# Route for adding a new provider
@app.route('/add_provider', methods=['GET', 'POST'])
def add_provider():
    if request.method == 'POST':
        name = request.form['name']
        user_hash = request.form['user_hash']
        cpu_cores = int(request.form['cpu_cores'])
        ram = int(request.form['ram'])
        storage = int(request.form['storage'])
        price_per_core = float(request.form['price_per_core'])
        price_per_gb_ram = float(request.form['price_per_gb_ram'])
        price_per_gb_storage = float(request.form['price_per_gb_storage'])

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO providers (name, user_hash, cpu_cores, ram, storage, price_per_core, price_per_gb_ram, price_per_gb_storage)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                          (name, user_hash, cpu_cores, ram, storage, price_per_core, price_per_gb_ram, price_per_gb_storage))
        conn.commit()
        conn.close()

        return redirect(url_for('home'))
    
    return render_template('add_provider.html')

# Initialize the database and run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
