from flask import render_template, make_response
from flask import send_file
from webapp import app
from flask import request
from webapp.matplotlib_funcs import make_heatmap, linear_regression_lassocoefs
import pandas as pd
import folium
import urllib
from jinja2 import Template


@app.route('/heatmap/')
def heatmap():

    from io import BytesIO
    import random
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

    try:
        # use this to get the values of user input from the form
        startdate = request.args.get('startdate')
        enddate = request.args.get('enddate')
        zipcode = request.args.get('zipcode')
        pickup_deliv = request.args.get('pickup_deliv')
    except ValueError:
        startdate = '1/5/2015'
        enddate = '7/1/2015'
        zipcode = 'all'
        pickup_deliv = 'Pickups and Deliveries'

    fig = make_heatmap(pickup_deliv, startdate, enddate, zipcode=zipcode)

    imgIO = BytesIO()
    fig.savefig(imgIO, bbox_inches='tight')
    imgIO.seek(0)

    return send_file(imgIO, mimetype='image/png')


@app.route('/predict')
def predict_future():

    from io import BytesIO

    try:
        # use this to get the values of user input from the form
        date_to_predict = request.args.get('date_to_predict')
        zipcode_to_predict = request.args.get('zipcode_to_predict')
        pickup_deliv_predict = request.args.get('pickup_deliv_predict')
    except ValueError:
        date_to_predict = '2015-11-11'
        zipcode_to_predict = 'all'
        pickup_deliv_predict = 'Pickups and Deliveries'

    fig, date_to_predict_y, _, _ = linear_regression_lassocoefs(pickup_deliv_predict, zipcode_to_predict, date_to_predict)

    print(date_to_predict_y)

    imgIO = BytesIO()
    fig.savefig(imgIO, bbox_inches='tight')
    imgIO.seek(0)

    return send_file(imgIO, mimetype='image/png')


@app.route('/')
@app.route('/index')
def index():

    return render_template('index.html', map_travelcost="map_travelcost.html", map_totalstops="map_totalstops.html")



@app.route('/hourly_volume', methods=['GET', 'POST'])
def hourly_volume():

    # set the default values
    startdate, enddate, zipcode, pickup_deliv = '1/5/2015', '7/2/2015', 'all', 'Pickups and Deliveries'
    # handle whenever user make a form POST (click the Plot button)
    if request.method == 'POST':
        try:
            # use this to get the values of user input from the form
            print('method is POST')
            startdate = request.form.get('startdate')
            enddate = request.form.get('enddate')
            zipcode = request.form.get('zipcode')
            pickup_deliv = request.form.get('pickup_deliv')
        except ValueError:
            print('ValueError!')
            pass

    return render_template("hourly_volume.html", startdate=startdate, enddate=enddate, pickup_deliv=pickup_deliv, zipcode=zipcode)



@app.route('/prediction', methods=['GET', 'POST'])
def prediction():

    # set the default values
    date_to_predict, zipcode_to_predict, pickup_deliv_predict = '2015-11-11', 'all', 'Pickups and Deliveries'
    # handle whenever user make a form POST (click the Plot button)
    if request.method == 'POST':
        try:
            # use this to get the values of user input from the form
            print('method is POST')
            date_to_predict = request.form.get('date_to_predict')
            zipcode_to_predict = request.form.get('zipcode_to_predict')
            pickup_deliv_predict = request.form.get('pickup_deliv_predict')
        except ValueError:
            print('ValueError!')
            pass

    _, date_to_predict_y, _, _ = linear_regression_lassocoefs(pickup_deliv_predict, zipcode_to_predict, date_to_predict)
    date_to_predict_y = round(date_to_predict_y,1)

    return render_template("prediction.html", date_to_predict=date_to_predict, zipcode_to_predict=zipcode_to_predict, pickup_deliv_predict=pickup_deliv_predict, date_to_predict_y=date_to_predict_y)



@app.route('/map_totalstops')
def map_totalstops():
    return render_template("map_totalstops_shapes.html")



@app.route('/map_travelcost')
def map_travelcost():
    return render_template("map_travelcost_shapes.html")
