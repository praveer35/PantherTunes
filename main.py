from flask import Flask, render_template, request, redirect
import json
import datetime

app = Flask(__name__)
@app.route("/")

def home():
  return render_template("home.html")

@app.route("/about")
def about():
  return render_template("about.html")

@app.route("/contact")
def contact():
  return render_template("contact.html")

@app.route("/sign-in")
def sign_in():
  return render_template("sign-in.html")

@app.route("/sign-up")
def sign_up():
  return render_template("sign-up.html")

if __name__ == "__main__":
  app.run(port=1601, debug=True)