from flask import Flask, request, render_template, redirect, url_for
import os
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_links', methods=['POST'])
def process_links():
    urls = request.form['urls']
    if urls:
        mode = 'a' if os.path.exists('data/links.txt') else 'w'
        with open('data/links.txt', mode) as file:
            for url in urls.splitlines():
                file.write(f"{url.strip()}\n")
        return redirect(url_for('track_prices'))
    return redirect(url_for('index'))

@app.route('/track_prices')
def track_prices():
    subprocess.run(["python", "trackers/tracker.py"])
    return redirect(url_for('index'))
    
@app.route('/start_tracking')
def start_tracking():
    # Launch the tracker script as a subprocess
    Popen(['python', 'tracker.py'], cwd=os.path.join(os.getcwd(), 'src/trackers'))
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
