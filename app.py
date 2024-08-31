from flask import Flask, request, render_template, redirect, url_for
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_links', methods=['POST'])
def process_links():
    urls = request.form['urls']
    if urls:
        with open('links.txt', 'w') as file:
            for url in urls.splitlines():
                file.write(f"{url.strip()}\n")
        return redirect(url_for('index'))
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
