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
    return json.loads(resp_json)

def get_skater_stats(start,end,type=2):
    req = 'http://www.nhl.com/stats/rest/skaters?isAggregate=true&reportType=basic&isGame=false' + \
            '&reportName=skatersummary&sort=[{"property":"points","direction":"DESC"}]&cayenneExp=gameTypeId=' + \
            str(type) + 'and seasonId%3E=' + start + 'and seasonId%3C=' + end
    skaters = pd.DataFrame(data=request_json(req)['data'])

    skaters = skaters[['playerId', 'playerName', 'playerPositionCode', 'points', 'gamesPlayed']]
    maskForwards = skaters['playerPositionCode'] != 'D'
    skaters.loc[maskForwards, 'playerPositionCode'] = 'F'

    return skaters

def get_goalie_stats(start,end,type=2):
    req = 'http://www.nhl.com/stats/rest/goalies?isAggregate=true&reportType=goalie_basic&isGame=false' +\
          '&reportName=goaliesummary&sort=[{"property":"saves","direction":"DESC"}]&cayenneExp=gameTypeId=' + \
            str(type) + 'and seasonId%3E=' + start + 'and seasonId%3C=' + end
    goalies = pd.DataFrame(data=request_json(req)['data'])

    goalies['points'] = goalies['saves'] / 9.0 - goalies['goalsAgainst']
    goalies['points'] = goalies['points'].round(2)
    maskNegatives = goalies['points'] < 0
    goalies.loc[maskNegatives, 'points'] = 0
    goalies['points'] += goalies['goals'] + goalies['assists'] + goalies['shutouts']
    goalies['points'] = goalies['points'] #.astype(int)

    goalies = goalies[['playerId', 'playerName', 'playerPositionCode', 'points', 'gamesPlayed']]
    return goalies

def update_rosters(googleSheetID):
    req = 'https://statsapi.web.nhl.com/api/v1/teams?expand=team.roster'
    team = []
    position = []
    player = []

    roster_bundle = request_json(req)['teams']
    for teams in roster_bundle:
        for players in teams['roster']['roster']:
            team.append(teams['abbreviation'])
            position.append(players['position']['abbreviation'])
            player.append(players['person']['fullName'])
    rosters = pd.DataFrame(data={'Player': player,
                                 'Position': position,
                                 'Team': team})
    rosters = rosters.sort_values('Player')
    pushUpdatetoSheet(rosters, googleSheetID, 'nhl_rosters')

    return

def pushUpdatetoSheet(stats, SPREADSHEET_ID, sheetName):
    # Setup the Sheets API
    SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
    store = file.Storage('credentials.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('sheets', 'v4', http=creds.authorize(Http()))

    # Call the Sheets API

    # How the input data should be interpreted.
    value_input_option = 'USER_ENTERED'  # TODO: Update placeholder value.

    # Prepare the sheet for stats to be updated by clearing it and adding new header row
    clear = service.spreadsheets().values().clear(spreadsheetId=SPREADSHEET_ID, range=sheetName + '!A2:E',
                                                    body={})
    response = clear.execute()
    pprint(response)

    # Now update the stats
    RANGE_NAME = sheetName + '!A2'

    value_range_body = {
        # TODO: Add desired entries to the request body. All existing entries
        # will be replaced.
        'values': stats.as_matrix().tolist()
    }

    request = service.spreadsheets().values().update(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME,
                                                     valueInputOption=value_input_option,
                                                     body=value_range_body)
    response = request.execute()

    # TODO: Change code below to process the `response` dict:
    pprint(response)

    # Put update timestamp in sheet
    updateTimestamp = service.spreadsheets().values().update(spreadsheetId=SPREADSHEET_ID,
                                                             range=sheetName + '!F1',
                                                             valueInputOption=value_input_option,
                                                             body={'values': [[str(dt.datetime.now())]]})
    responseTime = updateTimestamp.execute()

    return

def update_stats(endYearOfSeason, regularSeason, SPREADSHEET_ID):

    # Get skater and goalie stats, combine them in a dataframe.
    startSeason = get_string_season(endYearOfSeason)
    endSeason = get_string_season(endYearOfSeason)
    if regularSeason: # regular season =2, playoffs = 3
        gametype = 2
    else:
        gametype = 3
    skaters = get_skater_stats(startSeason, endSeason, gametype)
    goalies = get_goalie_stats(startSeason, endSeason, gametype)
    all_stats = pd.concat([skaters, goalies], axis=0)
    all_stats = all_stats.sort_values('playerName')

    pushUpdatetoSheet(all_stats, SPREADSHEET_ID, 'nhl_leaders')

if __name__ == "__main__":

    endYearOfSeason = 2019
    regularSeason = True
    googleSheetID = '1CEz-fbuBqrCl2EzEQlUBtsfRSMGDgxKikKB1cNqubPQ'
    sheetName = 'nhl_leaders'

    update_rosters(googleSheetID)
    update_stats(endYearOfSeason, regularSeason, googleSheetID)
