#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import requests
#import lxml.html
from pprint import pprint
#from sys import exit
import json
#import csv
import pandas as pd

def get_string_season(season):
    return str(season - 1) + str(season)

def request_json(url):
    resp_json = requests.get(url).text
    return json.loads(resp_json)['data']

def get_skater_stats(season):
    req = 'http://www.nhl.com/stats/rest/skaters?isAggregate=false&reportType=basic&isGame=false' + \
            '&reportName=skatersummary&sort=[{"property":"points","direction":"DESC"}]&cayenneExp=gameTypeId=2' + \
            'and seasonId%3E=' + season + 'and seasonId%3C=' + season
    skaters = pd.DataFrame(data=request_json(req))

    skaters = skaters[['playerId', 'playerPositionCode', 'playerName', 'points']]
    maskForwards = skaters['playerPositionCode'] != 'D'
    skaters.loc[maskForwards, 'playerPositionCode'] = 'F'

    return skaters

def get_goalie_stats(season):
    req = 'http://www.nhl.com/stats/rest/goalies?isAggregate=false&reportType=goalie_basic&isGame=false' +\
          '&reportName=goaliesummary&sort=[{"property":"saves","direction":"DESC"}]&cayenneExp=gameTypeId=2' +\
          ' and seasonId%3E=' + season + 'and seasonId%3C=' + season
    goalies = pd.DataFrame(data=request_json(req))

    goalies['points'] = goalies['saves'] / 9.0 - goalies['goalsAgainst']
    goalies['points'] = goalies['points'].round()
    maskNegatives = goalies['points'] < 0
    goalies.loc[maskNegatives, 'points'] = 0
    goalies['points'] += goalies['goals'] + goalies['assists'] + goalies['shutouts']
    goalies['points'] = goalies['points'].astype(int)

    goalies = goalies[['playerId', 'playerPositionCode', 'playerName', 'points']]
    return goalies

if __name__ == '__main__':
    stringSeason = get_string_season(2018)
    skaters = get_skater_stats(stringSeason)
    goalies = get_goalie_stats(stringSeason)

    all_stats = pd.concat([skaters, goalies], axis=0)
    all_stats = all_stats.sort_values('playerName')

    # Setup the Sheets API
    SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
    store = file.Storage('credentials.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('sheets', 'v4', http=creds.authorize(Http()))

    # Call the Sheets API
    SPREADSHEET_ID = '1l6_ivIATcLNeZyPn0297MVr2ZiJlqIW2P8NXSAWF_nc'
    RANGE_NAME = 'nhl_leaders!A1'
    #result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,
    #                                             range=RANGE_NAME).execute()
    # How the input data should be interpreted.
    value_input_option = 'USER_ENTERED'  # TODO: Update placeholder value.

    for i, j in enumerate(all_stats):
        print(i, j)


    value_range_body = {
        # TODO: Add desired entries to the request body. All existing entries
        # will be replaced.
        'values': [[row for row in all_stats.itertuples()]]
    }
    print(value_range_body)

    request = service.spreadsheets().values().update(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME,
                                                     valueInputOption=value_input_option,
                                                     body=value_range_body)
    response = request.execute()

    # TODO: Change code below to process the `response` dict:
    pprint(response)
