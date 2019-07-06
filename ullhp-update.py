#!/usr/bin/env python
# -*- coding: utf-8 -*-

from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import pandas as pd
import datetime as dt
import get_NHL_stats as gs
import argparse

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

def update_rosters(googleSheetID, sheet_name='nhl_rosters', savefile=False):
    rosters = gs.get_rosters()

    if savefile:
        rosters.to_csv(sheet_name + ".csv", index=False)
    else:
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

def update_stats(endYearOfSeason, regularSeason, googleSheetID, sheet_name='nhl_leaders', savefile=False):

    # Get skater and goalie stats, combine them in a dataframe.
    skaters = get_skater_stats(endYearOfSeason, regularSeason)
    goalies = get_goalie_stats(endYearOfSeason, regularSeason)
    all_stats = pd.concat([skaters, goalies], axis=0)
    all_stats = all_stats.sort_values('playerName')
    all_stats.fillna(0, inplace=True)

    if savefile:
        all_stats.to_csv(sheet_name + '.csv', index=False)
    else:
        pushUpdatetoSheet(all_stats, googleSheetID, sheet_name)

def main():
    parser = argparse.ArgumentParser(description='NHL Fantasy Stats')
    parser.add_argument('-o', '--output', help='Save to file with True, save to Google Sheet with False.',
                        default=False, dest='output_type')
    parser.add_argument('-r', '--roster', help='Filename or sheet name to save rosters to.', default='nhl_rosters',
                        dest='roster_sheetName')
    parser.add_argument('-s', '--stats', help='Filename or sheet name to save stats to.', default='nhl_leaders',
                        dest='leader_sheetName')
    parser.add_argument('-y', '--year', help='The ending year of the season to get.', type=int, default=2019,
                        dest='endYearOfSeason')
    parser.add_argument('-t', '--type', help='Save regular season stats with True, playoffs with False', default=True,
                        type=bool, dest='regularSeason')
    parser.add_argument('-g', '--gsheet_id', help='Google Sheet ID to push updates to', dest='googleSheetID')
    parser.add_argument('-u', '--update_type', help='Update rosters (1), update stats (2) or both (3)', type=int,
                        default=3, choices=[1,2,3], dest='update_type')
    args = parser.parse_args()

    if not args.output_type and args.googleSheetID is None:
        raise Exception("A Google Sheet ID must be supplied unless you want to save to a file.")

    if args.update_type != 2:
        update_rosters(args.googleSheetID, args.roster_sheetName, args.output_type)
    if args.update_type > 1:
        update_stats(args.endYearOfSeason, args.regularSeason, args.googleSheetID, args.leader_sheetName, args.output_type)

if __name__ == "__main__":
    main()

