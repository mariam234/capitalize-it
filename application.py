from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, url_for, send_from_directory, session
from flask_session import Session
from tempfile import mkdtemp
import os
import sqlalchemy
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.utils import secure_filename
from random import randint
import capitalizeIt
import urlparse
import psycopg2

urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["DATABASE_URL"])
conn = psycopg2.connect(
 database=url.path[1:],
 user=url.username,
 password=url.password,
 host=url.hostname,
 port=url.port
)

ALLOWED_EXTENSIONS = set(["txt"])
UPLOAD_FOLDER = "./uploads"

# Configure application
app = Flask(__name__)
app.secret_key = "dsfgsdHUIg97btb8632FD"
# Max file upload size
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
# Path for uploaded files to be temporarily saved
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure CS50 Library to use SQLite database
db = SQL(os.environ["DATABASE_URL"])

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/", methods=["GET", "POST"])
def index():
    """Home"""
    if request.method == "POST":
        # user requested to capitalize text
        if request.form.get("submit") == "capitalize" and request.form.get("text"):

            # on the first request, ask user to rate
            if "id" not in session:
                flash("Please take a moment to rate the accuracy of your request below.", "primary")
                session["id"]=randint(0,1000000)
            return render_template("capitalized.html", new_text=capitalizeIt.cap(request.form.get("text")),
                                       old_text=request.form.get("text"))

        # user requested to upload file
        elif request.form.get("submit") == "upload":
            return redirect("/uploader")

        # user submitted rating
        elif request.form.get("rating"):
            db.execute("INSERT INTO ratings (rating) VALUES (:rating)", rating=request.form.get("rating"))
            flash("Thanks for rating!", "primary")
            return render_template("capitalized.html", new_text=capitalizeIt.cap(request.form.get("text")),
                                       old_text=request.form.get("text"))
    return render_template("index.html")

# function for checking if file is allowed format (from Flask documentation)
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/uploader", methods=["GET", "POST"])
def uploader():
    """Uplading and reading files"""
    if request.method == "POST":
        # check if the post request has the file part
        if "file" not in request.files:
            flash("No file part", "danger")
            return redirect(request.url)
        file = request.files["file"]

        # check that user selected file
        if not file.filename:
            flash("No selected file", "danger")
            return redirect(request.url)

        if file:
            # check that user submitted valid file format
            if not allowed_file(file.filename):
                flash("Invalid file format", "danger")
                return redirect(request.url)

            # save file with secure_filename to sanitize user input and attach random number to avoid file name duplications, then read file contents
            filename = secure_filename(file.filename).split(".")[0] + str(randint(0,1000000)) + ".txt"
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            fileObj = open(os.path.join(app.config["UPLOAD_FOLDER"], filename), "r")
            text = fileObj.read()

            # close and delete file
            fileObj.close()
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], filename))

            # capitalize file contents and on the first request, ask user to rate
            if "id" not in session:
                flash("Please take a moment to rate the accuracy of your request below.", "primary")
                session["id"]=randint(0,1000000)
            return render_template("capitalized.html", new_text=capitalizeIt.cap(text),
                                   old_text=text)

    return render_template("uploader.html")

def errorhandler(e):
    """Show error"""
    return render_template("error.html", eName=e.name, eCode=e.code)

# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

class SQL(object):
    def __init__(self, url):
        try:
            self.engine = sqlalchemy.create_engine(url)
        except Exception as e:
            raise RuntimeError(e)
    def execute(self, text, *multiparams, **params):
        try:
            statement = sqlalchemy.text(text).bindparams(*multiparams, **params)
            result = self.engine.execute(str(statement.compile(compile_kwargs={"literal_binds": True})))
            # SELECT
            if result.returns_rows:
                rows = result.fetchall()
                return [dict(row) for row in rows]
            # INSERT
            elif result.lastrowid is not None:
                return result.lastrowid
            # DELETE, UPDATE
            else:
                return result.rowcount
        except sqlalchemy.exc.IntegrityError:
            return None
        except Exception as e:
            raise RuntimeError(e)

if __name__ == "__main__":
 app.debug = True
 port = int(os.environ.get("PORT", 5000))
 app.run(host='0.0.0.0', port=port)