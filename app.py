from flask import Flask, jsonify, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")  # Ensure `index.html` exists in a `templates/` folder

# Vercel expects a `handler` function for serverless execution
def handler(event, context):
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)  # Ensures correct handling of headers
    return app(event, context)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)