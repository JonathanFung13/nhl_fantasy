#!/usr/bin/env python
# -*- coding: utf-8 -*-

from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import pandas as pd
import datetime as dt
import get_NHL_stats as gs

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
    value_input_option = 'USER_ENTERED'

    # Prepare the sheet for stats to be updated by clearing it and adding new header row
    clear = service.spreadsheets().values().clear(spreadsheetId=SPREADSHEET_ID, range=sheetName + '!A2:I',
                                                    body={})
    response = clear.execute()
    #pprint(response)

    # Now update the stats
    RANGE_NAME = sheetName + '!A2'

    value_range_body = {
        'values': stats.values.tolist()
    }

    request = service.spreadsheets().values().update(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME,
                                                     valueInputOption=value_input_option,
                                                     body=value_range_body)
    response = request.execute()
    # pprint(response)

    # Put update timestamp in sheet
    updateTimestamp = service.spreadsheets().values().update(spreadsheetId=SPREADSHEET_ID,
                                                             range=sheetName + '!J1',
                                                             valueInputOption=value_input_option,
                                                             body={'values': [[str(dt.datetime.now())]]})
    responseTime = updateTimestamp.execute()

    return

def update_rosters(googleSheetID, sheet_name='nhl_rosters'):
    rosters = gs.get_rosters()
    pushUpdatetoSheet(rosters, googleSheetID, sheet_name)
    return

def get_skater_stats(end, type=True):
    skaters = gs.get_skater_stats(end, end, type)
    skaters = skaters[['playerId', 'playerName', 'playerPositionCode', 'points', 'gamesPlayed',
                       'playerBirthDate', 'playerHeight', 'playerWeight']]
    maskForwards = skaters['playerPositionCode'] != 'D'
    skaters.loc[maskForwards, 'playerPositionCode'] = 'F'

    return skaters

def get_goalie_stats(end,type=True):
    goalies = gs.get_goalie_stats(end, end, type)
    goalies['points'] = goalies['saves'] / 9.0 - goalies['goalsAgainst']
    goalies['points'] += goalies['goals'] + goalies['assists'] + goalies['shutouts']
    goalies['points'] = goalies['points'].round(0)
    maskNegatives = goalies['points'] < 0
    goalies.loc[maskNegatives, 'points'] = 0

    goalies = goalies[['playerId', 'playerName', 'playerPositionCode', 'points', 'gamesPlayed',
                       'playerBirthDate', 'playerHeight', 'playerWeight']]
    return goalies

def update_stats(endYearOfSeason, regularSeason, SPREADSHEET_ID, sheet_name='nhl_leaders'):

    # Get skater and goalie stats, combine them in a dataframe.
    skaters = get_skater_stats(endYearOfSeason, regularSeason)
    goalies = get_goalie_stats(endYearOfSeason, regularSeason)
    all_stats = pd.concat([skaters, goalies], axis=0)
    all_stats = all_stats.sort_values('playerName')
    all_stats.fillna(0, inplace=True)

    pushUpdatetoSheet(all_stats, SPREADSHEET_ID, sheet_name)

if __name__ == "__main__":

    endYearOfSeason = 2019
    regularSeason = True
    googleSheetID = '1CEz-fbuBqrCl2EzEQlUBtsfRSMGDgxKikKB1cNqubPQ'
    roster_sheetName = 'nhl_rosters'
    leader_sheetName = 'nhl_leaders'

    #update_rosters(googleSheetID, roster_sheetName)
    update_stats(endYearOfSeason, regularSeason, googleSheetID)
