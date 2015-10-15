
# coding: utf-8

# In[15]:

import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from pytz import timezone
import itertools
import os, sys
import json


def date_conv(tbl, cols):
    '''Converts dates to proper format and timezone and creates columns for hour, day, etc

    Parameters
    ----------
    tbl: pandas dataframe
        tbl from the move loot database after being converted to pd.dataframe, where each
        row is a pickup/delivery timestamp
    cols: list
        list of strings containing names of columns in tbl, each of which hold datetime info.
        the first entry in this list must be the name of the "critical date", or the date
        which will be used for future analysis (eg. the "pickup_date" in the submissions table)

    Returns
    -------
    tbl: pandas dataframe
        dataframe where datetimes in cols have been converted to local timezones and
        new columns have been added representing hour, day, dayofweek, etc
    '''

    #set timezone to pacific since data was from san francisco bay area
    local_tz = timezone('US/Pacific')

    #iterate through columns that contain datetimes
    for col in cols:
        date_converted = [pd.to_datetime(dt, utc=True) for dt in tbl[col]]
        date_converted = [date.astimezone(local_tz) for date in date_converted]
        tbl[col] = date_converted

        critical_date = cols[0]
        tbl['hour'] = [date.hour for date in tbl[critical_date]]
        tbl['day'] = [date.day for date in tbl[critical_date]]
        tbl['dayofweek'] = [date.dayofweek for date in tbl[critical_date]]
        tbl['week'] = [date.week for date in tbl[critical_date]]
        tbl['month'] = [date.month for date in tbl[critical_date]]
        tbl['daterange_str'] = [date.strftime('%Y-%m-%d') for date in tbl[critical_date]]

    return tbl


def rep_by_zip(path, cols, outdir, filename):
    '''Load initial files, convert to pd.dataframe, convert dates, and save as pkl and xls

    Parameters
    ----------
    path: string
        refers to location of files containing move loot database output
    cols: list of strings
        list of strings containing names of columns in tbl, each of which hold datetime info.
        the first entry in this list must be the name of the "critical date", or the date
        which will be used for future analysis (eg. the "pickup_date" in the submissions table)
    outdir: string
        place where output files will be stored
    filename: string
        name of files to be saved

    Returns
    -------
    zips: pandas dataframe
        after date conversion. also saves this as xls and pkl format for further analysis
    '''
    dtf = '%Y-%m-%d %H:%M:%S'
    local_tz = timezone('US/Pacific')
    utc = timezone('UTC')

    #load data
    zips = pd.read_json(path)
    #convert dates
    zips = date_conv(zips,cols)
    zips = zips.sort(columns=cols[0])

    #save data
    zips.to_pickle(outdir + filename + '.pkl')
    zips.to_excel(outdir + filename + '.xls', engine='openpyxl')

    return zips


#make date reference table
def dateref_tbl(tbl,keydate='keydate'):
    '''Create reference date table based on minimum and maximum dates in tbl.
    Create columns for month, day, week, etc.

    Parameters
    ----------
    tbl: pandas dataframe
        holds date information in column keydate
    keydate: string
        name of column in tbl holding date information. default "keydate"

    Returns
    -------
    date_frame: pandas DataFrame
        dataframe containing dates broken out in a number of ways for a range given
        by the min and max date in tbl's date column
    rng: list
        list of strings refering to the dates in the given range, used to create
        the index of date_frame
    '''

    dtf = '%Y-%m-%d'

    #extract minimum and maximum dates from tbl
    mindate = tbl.keydate.min()
    maxdate = tbl.keydate.max()

    #create a range of dates
    daterng = pd.date_range(mindate, maxdate, freq='D')
    #convert to strings
    rng = [date.strftime(dtf) for date in daterng]

    #create dataframe
    date_frame = pd.DataFrame(daterng, index=rng, columns=['datetime'])
    date_frame = pd.DataFrame({'daterange_str' : rng,
                              'datetime' : daterng,
                              'dayofmonth' : daterng.day,
                              'month' : daterng.month,
                              'week' : daterng.week,
                              'year' : daterng.year,
                              'dayofweek' : daterng.dayofweek,
                              'dayofyear' : daterng.dayofyear})

    date_frame['date'] = [date.split()[0] for date in date_frame['daterange_str']]

    return date_frame, rng


def count_stops(tbl,keydate,zipcode=None):
    '''Count the number of truck events at each zipcode over time

    Parameters
    ----------
    tbl: pandas dataframe
    keydate: string
        name of column containing the date
    zipcode: string
        string refering to a entry in the tbl column 'zipcode'. if passed, events
        will only be counted for rows that match that zipcode. if none, all events
        will be counted
    '''
    if zipcode != None:
        tbl = tbl[tbl['zipcode'] == zipcode]
    groupby_date = tbl.groupby(by='daterange_str')
    count = groupby_date.count()
    counted = pd.DataFrame(count[keydate])
    counted.rename(columns={keydate:zipcode},inplace=True)
    counted.reset_index(inplace=True)

    return counted


def summarize_by_zip(tbl,keydate='keydate'):
    '''Given a dataframe of truck event timestamps, convert to a table where each
    row is a day and each column is a zipcode with the number of events per time

    Parameters
    ----------
    tbl: pandas dataframe
    keydate: string
        name of column in tbl holding date information. default "keydate"

    Returns
    -------
    tbl_allcounts: pandas dataframe
        tbl where each row is a day and each column is a zipcode and tbl values are counts
    tbl_counted: pandas dataframe
        don't use this one for anything
    zipcdoes: list
        list of unique zipcodes in the zipcode column of tbl
    date_frame: pandas dataframe
        dataframe holding date information for the same range of dates indictaed in tbl
    '''
    date_frame, rng = dateref_tbl(tbl,keydate)

    dtf = '%Y-%m-%d'

    #make simplified date_str
    tbl['daterange_str'] = [date.strftime(dtf) for date in tbl[keydate]]
    tbl.reset_index(inplace=True, drop=True)

    zipcodes = list(set(tbl.zipcode))

    tbl_allcounts = pd.DataFrame({'daterange_str' : rng})

    for zipcode in zipcodes:
        tbl_counted = count_stops(tbl,keydate,zipcode=zipcode)
        tbl_allcounts = tbl_allcounts.merge(tbl_counted,on='daterange_str',how='outer')

    tbl_allcounts.fillna(value=0, inplace=True)

    return tbl_allcounts, tbl_counted, zipcodes, date_frame


def time_by_zip(ordtbl, subtbl, outdir):
    '''Converts zipcodes to strings and creates individual tables for orders, submissions,
    and both where each row is a day and each column in a zipcode

    Parameters
    ----------
    ordtbl: pandas dataframe
        dataframe following import with rep_by_zip. holds orders
    subtbl: pandas dataframe
        dataframe following import with rep_by_zip. holds submissions
    outdir: string
        place where output files will be stored

    Returns
    -------
    di_submissions_allcounts: pandas dataframe
        submissions. tbl where each row is a day and each column is a zipcode and tbl values are counts
    di_orders_allcounts: pandas dataframe
        orders. tbl where each row is a day and each column is a zipcode and tbl values are counts
    di_subandord_allcounts: pandas dataframe
        submissions and orders. tbl where each row is a day and each column is a zipcode and tbl values are counts
    date_frame: pandas dataframe
        dataframe containing dates broken out in a number of ways for a range given
        by the min and max date in tbl's date column
    '''
    keydate = 'keydate'

    #standardize column names, convert zipcodes to strings
    ordtbl.rename(columns={'delivery_date':keydate},inplace=True)
    ordtbl = ordtbl[[keydate,'zipcode']]
    ordtbl['zipcode'] = [str(zipcode) for zipcode in ordtbl['zipcode']]

    subtbl.rename(columns={'pickup_date':keydate},inplace=True)
    subtbl = subtbl[[keydate,'zipcode']]
    subtbl['zipcode'] = [str(zipcode) for zipcode in subtbl['zipcode']]

    #combine orders and submssions into single table
    tbl_subandord = pd.concat([subtbl, ordtbl],ignore_index=True)

    dtf = '%Y-%m-%d'
    #create count tables
    orders_allcounts, _, ordzips, date_frame_ord = summarize_by_zip(ordtbl)
    submissions_allcounts, _, subzips, date_frame_sub = summarize_by_zip(subtbl)
    subandord_allcounts, _, subandordzips, date_frame_subandord = summarize_by_zip(tbl_subandord)

    #set the date as index
    di_submissions_allcounts = submissions_allcounts.set_index('daterange_str')
    di_orders_allcounts = orders_allcounts.set_index('daterange_str')
    di_subandord_allcounts = subandord_allcounts.set_index('daterange_str')

    #create list of "approved" dates for modeling
    mindate = '1/1/2015'
    maxdate = '7/31/2015'

    daterng = pd.date_range(mindate, maxdate, freq='D')
    rng = [date.strftime(dtf) for date in daterng]

    date_frame = pd.DataFrame(daterng, index=rng, columns=['datetime'])

    date_frame = pd.DataFrame({'daterange_str' : rng,
                              'datetime' : daterng,
                              'dayofmonth' : daterng.day,
                              'month' : daterng.month,
                              'week' : daterng.week,
                              'year' : daterng.year,
                              'dayofweek' : daterng.dayofweek,
                              'dayofyear' : daterng.dayofyear})

    #filter tables by date range of interest
    di_submissions_allcounts = di_submissions_allcounts.loc[rng]
    di_orders_allcounts = di_orders_allcounts.loc[rng]
    di_subandord_allcounts = di_subandord_allcounts.loc[rng]

    di_submissions_allcounts.to_pickle(outdir + 'di_submissions_allcounts.pkl')
    di_orders_allcounts.to_pickle(outdir + 'di_orders_allcounts.pkl')
    di_subandord_allcounts.to_pickle(outdir + 'di_subandord_allcounts.pkl')
    date_frame.to_pickle(outdir + 'date_frame.pkl')

    return di_submissions_allcounts, di_orders_allcounts, di_subandord_allcounts, date_frame


def latslngs_fromGoogle(zipcodes, GOOGLE_API_KEY):
    '''Queries the google API to get the latitudes and longitudes for a list of zipcodes

    Parameters
    ----------
    zipcdoes: list of strings
        list of zipcodes of interest
    GOOGLE_API_KEY: string
        your google developer API key

    Returns
    -------
    lats_google, lngs_google: lists representing latitute and longitude for each zipcode
    '''
    lats_google = []
    lngs_google = []

    for zipcode in zipcodes:
        query_url = 'https://maps.googleapis.com/maps/api/geocode/json?address=%s&key=%s' % (str(zipcode),
                                                                                            GOOGLE_API_KEY)
        r = requests.get(query_url)
        temp = r.json()
        lat = temp['results'][0]['geometry']['location']['lat']
        lng = temp['results'][0]['geometry']['location']['lng']
        lats_google.append(lat)
        lngs_google.append(lng)

    return lats_google, lngs_google


def get_google_pt2pt_list(origin_address, destination_addresses):
    '''Queries the google API to get the latitudes and longitudes for a list of zipcodes

    Parameters
    ----------
    origin_address: string
    destination_addresses: list of strings
        list of addresses for which to get distance from origin_address

    Returns
    -------
    dist_google, dura_google: lists
        lists of distances and durations from the origin_address for each destination_addresses

    '''
    dist_google = []
    dura_google = []

    for dest_address in destination_addresses:

        base_url = 'https://maps.googleapis.com/maps/api/distancematrix/'
        query_url = '%sjson?origins=%s&destinations=%s&units=imperial' %(base_url,
                                                                         str(origin_address),
                                                                         str(dest_address))

        r = requests.get(query_url)
        temp = r.json()
        distance = temp['rows'][0]['elements'][0]['distance']['text']
        duration = temp['rows'][0]['elements'][0]['duration']['text']

        dist_google.append(distance)
        dura_google.append(duration)

    return dist_google, dura_google

def summarize_by_zip_dataframe(submissionzips, orderzips, date_frame, di_orders_allcounts, di_submissions_allcounts, di_subandord_allcounts, zip_summary_path, outdir):
    '''make summary dataframe where each row is a zipcode and columns contain information about
    that zipcode

    Parameters
    ----------
    submissionzips, orderzips: pandas dataframes
        dataframes where each row is a day
    date_frame: pandas dataframe
        dataframe containing dates for a given range
    di_orders_allcounts, di_submissions_allcounts, di_subandord_allcounts: pandas dataframes
        dataframes where each row is a day and each column is a zipcode and the values are counts
    zip_summary_path: string
        path to the zip_summary file that contains cluster information for each zipcode
    outdir: string
        place where output files will be stored
    '''

    #make list of dates to include in analysis
    approved_dates = date_frame.daterange_str.tolist()

    #filter submissionzips and orderzips so they only contain dates in the approved range
    submissionzips = submissionzips[submissionzips.daterange_str.isin(approved_dates)]
    orderzips = orderzips[orderzips.daterange_str.isin(approved_dates)]

    submissionzips['zipcode'] = [str(zipcode) for zipcode in submissionzips['zipcode']]
    orderzips['zipcode'] = [str(zipcode) for zipcode in orderzips['zipcode']]

    submissionzips['total_submission_value_cents'] = submissionzips.total_submission_value_cents / 100
    orderzips['total_cents'] = orderzips.total_cents / 100

    zip_summary = pd.read_pickle(zip_summary_path)

    #total number of delivery and pickup events
    pickups_total = pd.DataFrame({'pickups_total':di_submissions_allcounts.sum(axis=0)})
    deliveries_total = pd.DataFrame({'deliveries_total':di_orders_allcounts.sum(axis=0)})
    visits_total = pd.DataFrame({'visits_total':di_subandord_allcounts.sum(axis=0)})

    #number of delivery and pickup events in the last month
    pickups_lastmonth = pd.DataFrame({'pickups_lastmonth':di_submissions_allcounts[-28:].sum(axis=0)})
    deliveries_lastmonth = pd.DataFrame({'deliveries_lastmonth':di_orders_allcounts[-28:].sum(axis=0)})
    visits_lastmonth = pd.DataFrame({'visits_lastmonth':di_subandord_allcounts[-28:].sum(axis=0)})

    #total price of pickups and deliveries in approved date range
    pickups_money_total = pd.DataFrame({'pickups_money_total':submissionzips.groupby('zipcode').sum().total_submission_value_cents})
    deliveries_money_total = pd.DataFrame({'deliveries_money_total':orderzips.groupby('zipcode').sum().total_cents})

    #list of dates in the last month
    lastmonth_dates = date_frame.daterange_str[-28:].tolist()

    #price of pickups and deliveries in the last month
    submissionzips_lastmonth = submissionzips[submissionzips.daterange_str.isin(lastmonth_dates)]
    orderzips_lastmonth = orderzips[orderzips.daterange_str.isin(lastmonth_dates)]

    pickups_money_lastmonth = pd.DataFrame({'pickups_money_lastmonth':submissionzips_lastmonth.groupby('zipcode').sum().total_submission_value_cents})
    deliveries_money_lastmonth = pd.DataFrame({'deliveries_money_lastmonth':orderzips_lastmonth.groupby('zipcode').sum().total_cents})

    zip_summary = zip_summary.merge(pickups_total, left_on='zipcodes', right_index=True, how='left')
    zip_summary = zip_summary.merge(deliveries_total, left_on='zipcodes', right_index=True, how='left')
    zip_summary = zip_summary.merge(visits_total, left_on='zipcodes', right_index=True, how='left')

    zip_summary = zip_summary.merge(pickups_lastmonth, left_on='zipcodes', right_index=True, how='left')
    zip_summary = zip_summary.merge(deliveries_lastmonth, left_on='zipcodes', right_index=True, how='left')
    zip_summary = zip_summary.merge(visits_lastmonth, left_on='zipcodes', right_index=True, how='left')

    zip_summary = zip_summary.merge(pickups_money_total, left_on='zipcodes', right_index=True, how='left')
    zip_summary = zip_summary.merge(deliveries_money_total, left_on='zipcodes', right_index=True, how='left')

    zip_summary = zip_summary.merge(pickups_money_lastmonth, left_on='zipcodes', right_index=True, how='left')
    zip_summary = zip_summary.merge(deliveries_money_lastmonth, left_on='zipcodes', right_index=True, how='left')

    #number of weeks in the approved date range
    number_of_weeks = round(len(date_frame)/7,2)

    zip_summary['visits_money_total'] = np.nansum([zip_summary.pickups_money_total,zip_summary.deliveries_money_total],axis=0)
    zip_summary['visits_money_lastmonth'] = np.nansum([zip_summary.pickups_money_lastmonth,zip_summary.deliveries_money_lastmonth],axis=0)

    zip_summary['visits_moneypervisit_total'] = zip_summary.visits_money_total / zip_summary.visits_total
    zip_summary['visits_moneypervisit_lastmonth'] = zip_summary.visits_money_lastmonth / zip_summary.visits_lastmonth

    zip_summary['visits_perweek_total'] = zip_summary.visits_total / number_of_weeks
    zip_summary['visits_money_perweek_total'] = zip_summary.visits_money_total / number_of_weeks

    zip_summary['visits_perweek_lastmonth'] = zip_summary.visits_lastmonth / 4
    zip_summary['visits_money_perweek_lastmonth'] = zip_summary.visits_money_lastmonth / 4

    zip_summary.to_pickle(outdir + 'zip_summary_2.pkl')

    return zip_summary
