from flask import Flask, jsonify, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")  # Ensure `index.html` exists in a `templates/` folder



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=12345)