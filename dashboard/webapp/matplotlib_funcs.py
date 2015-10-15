
# coding: utf-8

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import os, sys
import json
from sklearn.cross_validation import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error, explained_variance_score
import itertools
import seaborn as sns


def ordersbyhrandday(tbl, zipcode = None, plot=False):
    #pass zipcode and month as a list of floats
    if zipcode != None:
        zipcode = [int(zipcode)]
        tbl = tbl[tbl['zipcode'].isin(zipcode)]
    a = tbl.groupby(['hour','dayofweek']).count()
    a = pd.DataFrame(a['zipcode_tier'])
    a.reset_index(inplace=True)
    b = a.pivot(index='hour',columns='dayofweek',values='zipcode_tier')

    new_index = pd.Index(np.arange(0,24,1), name='hour')
    b = b.reindex(new_index).fillna(0)
    if plot == True:
        b.plot()
    return a,b



def make_heatmap(pickup_deliv, mindate, maxdate, zipcode=None):

    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.dates import DateFormatter
    from io import BytesIO

    if pickup_deliv=='Deliveries':
        tbl = pd.read_pickle('webapp/static/data/orderzips_filt.pkl')
    if pickup_deliv=='Pickups':
        tbl = pd.read_pickle('webapp/static/data/submissionzips_filt.pkl')
    if pickup_deliv=='Pickups and Deliveries':
        tbl = pd.read_pickle('webapp/static/data/subandordzips_filt.pkl')

    daterng = pd.date_range(mindate, maxdate, freq='D')
    rng = [date.strftime('%Y-%m-%d') for date in daterng]

    tbl = tbl[tbl.daterange_str.isin(rng)]

    print(zipcode)
    print(type(zipcode))

    if zipcode == 'all':
        zipcode=None

    a_, tbl = ordersbyhrandday(tbl=tbl, zipcode=zipcode)

    tbl_limits = tbl.ix[7:18]
    tbl_transpose = tbl_limits.transpose()

    m, n = tbl_transpose.shape

    fig, ax = plt.subplots(figsize=(7, 4))

    ax.imshow(tbl_transpose, interpolation='nearest',cmap='Reds').get_axes()
    #add cmap='Reds' to change color scheme
    ax.xaxis.set_ticks(np.arange(0, n, 1))
    ax.set_xticklabels(tbl_transpose.columns)
    ax.set_yticks(np.arange(0, m, 1))
    ax.set_yticklabels(['Mon','Tue','Wed','Thu','Fri','Sat','Sun'])
    ax.grid('off')

    plt.ylabel('Day of week')
    plt.xlabel('Hour of day')

    for i in range(m):
        for j in range(n):
            ax.text(j, i, (int(tbl_transpose.iget_value(i, j))),
                    size='small', ha='center', va='center')

    return fig


def setup_datetable(mindate, futuredate):
    datereange = pd.date_range(mindate,futuredate,freq='D')

    dtf = '%Y-%m-%d'
    rng = [date.strftime(dtf) for date in datereange]

    date_frame = pd.DataFrame({'daterange_str' : rng,
                               'datetime' : datereange,
                               'dayofmonth' : datereange.day,
                               'dayofweek' : datereange.dayofweek,
                               'dayssincestart' : np.arange(0,len(rng),1)})
    return date_frame


def make_regression_features_oct(df):
    '''Create features for regression given a dataframe
    '''

    from pandas.tseries.holiday import USFederalHolidayCalendar

    x_dayssincestart = df.dayssincestart

    x_dayofweek = df.dayofweek
    x_dayofweek = pd.get_dummies(x_dayofweek,prefix='dayofweek')

    x_dayofmonth = df.dayofmonth
    x_dayofmonth = pd.get_dummies(x_dayofmonth, prefix='dayofmonth')

    x_week1 = pd.Series([1 if day < 8 else 0 for day in df.dayofmonth],name='week1')
    x_week2 = pd.Series([1 if (day >= 8 and day < 16) else 0 for day in df.dayofmonth],name='week2')
    x_week3 = pd.Series([1 if (day >= 16 and day < 23) else 0 for day in df.dayofmonth],name='week3')
    x_week4 = pd.Series([1 if day >= 23 else 0 for day in df.dayofmonth],name='week4')

    x_isweekend = pd.Series([1 if (day == 5 or day == 6) else 0 for day in df.dayofweek],name='isweekend')

    x_istueswed = pd.Series([1 if (day == 1 or day == 2) else 0 for day in df.dayofweek],name='istueswed')

    x_isfrisat = pd.Series([1 if (day == 4 or day == 5) else 0 for day in df.dayofweek],name='isfrisat')

    #get holidays
    calendar = USFederalHolidayCalendar()
    holidays = calendar.holidays(start=df.datetime.min(), end=df.datetime.max())
    x_isholiday = pd.Series([1 if day in holidays.tolist() else 0 for day in df.datetime],name='x_isholiday')

    #find 3-day weekends
    x_isholidaywknd = pd.Series(np.zeros(len(x_isholiday)),name='x_isholidaywknd')
    x_weekendandholiday = x_isweekend + x_isholiday
    for i in range(1, len(x_weekendandholiday)-2):
        if x_weekendandholiday[i] == 1:
            if x_weekendandholiday[i+1] == 1 and x_weekendandholiday[i+2] ==1:
                x_isholidaywknd[i] = 1
                x_isholidaywknd[i+1] = 1
                x_isholidaywknd[i+2] = 1

    x_week1tueswed = x_week1 & x_istueswed
    x_week2tueswed = x_week2 & x_istueswed
    x_week3tueswed = x_week3 & x_istueswed
    x_week4tueswed = x_week4 & x_istueswed

    x_week1frisat = x_week1 & x_isfrisat
    x_week2frisat = x_week2 & x_isfrisat
    x_week3frisat = x_week3 & x_isfrisat
    x_week4frisat = x_week4 & x_isfrisat

    x_week1wknd = x_week1 & x_isweekend
    x_week2wknd = x_week2 & x_isweekend
    x_week3wknd = x_week3 & x_isweekend
    x_week4wknd = x_week4 & x_isweekend

    X_vars = pd.concat([x_dayssincestart,x_dayofweek,x_dayofmonth,
                       x_week1,x_week2,x_week3,x_week4,
                       x_isweekend,x_istueswed,x_isfrisat,
                       x_isholiday,x_isholidaywknd,
                       x_week1tueswed,x_week2tueswed,x_week3tueswed,x_week4tueswed,
                       x_week1frisat,x_week2frisat,x_week3frisat,x_week4frisat,
                       x_week1wknd,x_week2wknd,x_week3wknd,x_week4wknd],
                       axis=1)

    return X_vars


def divide_by_dates(date_frame, X_vars, startdate, enddate, features):

    startdate_ix = date_frame.loc[date_frame['datetime'] == startdate].index.tolist()
    enddate_ix = date_frame.loc[date_frame['datetime'] == enddate].index.tolist()

    X_vars_cur = X_vars.loc[startdate_ix[0]:enddate_ix[0]]
    X_vars_cur = X_vars_cur[features]

    #reformat for sklearn
    X = X_vars_cur.values

    return X_vars_cur, X


def linear_regression_lassocoefs(stop_type, zip_of_interest, date_to_predict):

    #start getting data!
    outdir = ''

    if stop_type == 'Pickups and Deliveries':
        tbl = pd.read_pickle(outdir + 'di_subandord_allcounts.pkl')
        features = pd.read_pickle(outdir + 'lasso_coefs_subandords.pkl')
    if stop_type == 'Deliveries':
        tbl = pd.read_pickle(outdir + 'di_orders_allcounts.pkl')
        features = pd.read_pickle(outdir + 'lasso_coefs_ords.pkl')
    if stop_type == 'Pickups':
        tbl = pd.read_pickle(outdir + 'di_submissions_allcounts.pkl')
        features = pd.read_pickle(outdir + 'lasso_coefs_subs.pkl')

    #get rid of zero value on july 4th
    tbl.loc['2015-07-04'][:] = np.nan
    tbl.interpolate(inplace=True)

    #change zipcodes to strings
    zips_to_str = {zip_fl:str(zip_fl) for zip_fl in tbl.columns}
    tbl = tbl.rename(columns=zips_to_str)

    #extract just zipcodes of interest
    if zip_of_interest == 'all':
        y = tbl[list(zips_to_str.values())].sum(axis=1)
    else:
        zip_input_list = zip_of_interest.split(",")

        if len(zip_input_list) > 1:
            try:
                y = tbl[zip_input_list].sum(axis=1)
            except:
                raise ValueError('Zip not found in table')
        else:
            y = tbl[zip_input_list]

    y.name = 'y'

    mindate = tbl.index.min()
    maxdate = tbl.index.max()
    futuredate = '2015-12-31'

    date_frame = setup_datetable(mindate, futuredate)

    X_vars_all = make_regression_features_oct(date_frame)

    #make list of features to include in model
    feature_list = features['var'].tolist()

    X_vars,X = divide_by_dates(date_frame, X_vars_all, mindate, maxdate, feature_list)
    X_vars_future,X_future = divide_by_dates(date_frame, X_vars_all, maxdate, pd.to_datetime(futuredate), feature_list)

    lr = LinearRegression()
    lr_fit = lr.fit(X,y)
    y_pred = lr_fit.predict(X)

    y_pred_future = lr_fit.predict(X_future)

    #find requested datestring in predicted values
    date_to_predict_ix = date_frame[date_frame.daterange_str == date_to_predict].index.tolist()
    X_vars_future.reset_index(inplace=True, drop=True)

    date_to_predict_ix_y = (X_vars_future[X_vars_future['dayssincestart'] == date_to_predict_ix].index.tolist())

    date_to_predict_x = float(date_to_predict_ix[0])
    date_to_predict_y = float(y_pred_future[date_to_predict_ix_y])

    #plot figure
    fig = plt.figure(figsize=(7,4))
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(y)
    ax.plot(y_pred,'r')
    ax.plot(X_vars_future.dayssincestart,y_pred_future)
    ax.plot(date_to_predict_x,date_to_predict_y, 'ro', markersize=10)
    plt.xlabel('Days')
    plt.ylabel('Number of %s' %stop_type)
    plt.xticks()

    return fig, date_to_predict_y, lr_fit, X_vars
