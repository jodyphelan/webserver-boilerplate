import json
import os
import uuid
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from flask import current_app as app
from .worker import run_task

bp = Blueprint('home', __name__)


@bp.route('/',methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        error=None
        if "fastq_submit" in request.form:
            run_id = str(uuid.uuid4())
            if request.files['file1'].filename=="":
                error = "No file found for read 1, please try again!"
            if error==None:
                run_fastq_pipeline(request.files['file1'],request.files['file2'], run_id)
                return redirect(url_for('home.result', run_id=run_id))
        if "result_id" in request.form:
                return redirect(url_for('home.result', run_id=request.form['result_id']))
        if error:
            flash(error)
    return render_template('pages/index.html')


def run_fastq_pipeline(f1, f2, run_id):
    filename1 = secure_filename(f1.filename)
    filename2 = secure_filename(f2.filename) if f2.filename!="" else None
    f1.save(os.path.join(app.config["UPLOAD_FOLDER"], filename1))
    if filename2:
        f2.save(os.path.join(app.config["UPLOAD_FOLDER"], filename2))
    fpath1 = "/%s/%s" % (app.config["UPLOAD_FOLDER"],filename1)
    fpath2 = "/%s/%s" % (app.config["UPLOAD_FOLDER"],filename2) if filename2 else None
    with open("%s/%s.log" % (app.config["RESULTS_DIR"],run_id),"w") as O:
        O.write("Starting job: %s\n")
        O.write("F1: %s\n" % fpath1)
        O.write("F1: %s\n" % fpath2)
    run_task.delay(fpath1,fpath2,run_id,app.config["RESULTS_DIR"])


@bp.route('/result/<uuid:run_id>')
def result(run_id):
    log_file = "%s/%s.log" % (app.config["RESULTS_DIR"],run_id)
    if not os.path.isfile(log_file):
        flash("Error! Result with ID:%s doesn't exist" % run_id)
        return redirect(url_for('home.index'))
    result_file = "%s/%s.results.txt" % (app.config["RESULTS_DIR"],run_id)
    results = open(result_file).read()
    return render_template('pages/result.html',run_id=run_id,results = results)

@bp.route('/igv')
def igv():
    return render_template('pages/igv.html')
