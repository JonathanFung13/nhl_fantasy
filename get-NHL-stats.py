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
import datetime as dt

def get_string_season(season):
    return str(season - 1) + str(season)

def request_json(url):
    resp_json = requests.get(url).text
    return json.loads(resp_json)['data']

def get_skater_stats(start,end,type=2):
    req = 'http://www.nhl.com/stats/rest/skaters?isAggregate=true&reportType=basic&isGame=false' + \
            '&reportName=skatersummary&sort=[{"property":"points","direction":"DESC"}]&cayenneExp=gameTypeId=' + \
            str(type) + 'and seasonId%3E=' + start + 'and seasonId%3C=' + end
    skaters = pd.DataFrame(data=request_json(req))

    skaters = skaters[['playerId', 'playerName', 'playerPositionCode', 'points', 'gamesPlayed']]
    maskForwards = skaters['playerPositionCode'] != 'D'
    skaters.loc[maskForwards, 'playerPositionCode'] = 'F'

    return skaters

def get_goalie_stats(start,end,type=2):
    req = 'http://www.nhl.com/stats/rest/goalies?isAggregate=true&reportType=goalie_basic&isGame=false' +\
          '&reportName=goaliesummary&sort=[{"property":"saves","direction":"DESC"}]&cayenneExp=gameTypeId=' + \
            str(type) + 'and seasonId%3E=' + start + 'and seasonId%3C=' + end
    goalies = pd.DataFrame(data=request_json(req))

    goalies['points'] = goalies['saves'] / 9.0 - goalies['goalsAgainst']
    goalies['points'] = goalies['points'].round(2)
    maskNegatives = goalies['points'] < 0
    goalies.loc[maskNegatives, 'points'] = 0
    goalies['points'] += goalies['goals'] + goalies['assists'] + goalies['shutouts']
    goalies['points'] = goalies['points'] #.astype(int)

    goalies = goalies[['playerId', 'playerName', 'playerPositionCode', 'points', 'gamesPlayed']]
    return goalies

if __name__ == '__main__':
    startSeason = get_string_season(2018)
    endSeason = get_string_season(2018)
    gametype = 3 # regular season =2, playoffs = 3
    skaters = get_skater_stats(startSeason, endSeason, gametype)
    goalies = get_goalie_stats(startSeason, endSeason, gametype)

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
    #SPREADSHEET_ID = '1CEz-fbuBqrCl2EzEQlUBtsfRSMGDgxKikKB1cNqubPQ' # ULLHP page
    SPREADSHEET_ID = '1UOM45jvuMb3lo_LpGU-b8Afr0MEf-K8aNNyQrOEFdQU' #test page for summer

    # How the input data should be interpreted.
    value_input_option = 'USER_ENTERED'  # TODO: Update placeholder value.

    # Prepare the sheet for stats to be updated by clearing it and adding new header row
    clear = service.spreadsheets().values().clear(spreadsheetId=SPREADSHEET_ID, range='nhl_leaders!A2:E',
                                                    body={})
    response = clear.execute()
    pprint(response)

    # Now update the stats
    RANGE_NAME = 'nhl_leaders!A2'

    value_range_body = {
        # TODO: Add desired entries to the request body. All existing entries
        # will be replaced.
        'values': all_stats.as_matrix().tolist()
    }

    request = service.spreadsheets().values().update(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME,
                                                     valueInputOption=value_input_option,
                                                     body=value_range_body)
    response = request.execute()

    # TODO: Change code below to process the `response` dict:
    pprint(response)

    # Put update timestamp in sheet
    updateTimestamp = service.spreadsheets().values().update(spreadsheetId=SPREADSHEET_ID,
                                                             range='nhl_leaders!F1',
                                                             valueInputOption=value_input_option,
                                                             body={'values': [[str(dt.datetime.now())]]})
    responseTime = updateTimestamp.execute()
