#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pandas as pd
import datetime as dt
import utilities as util
from pprint import pprint
import pickle
import os.path


def push_update_to_sheet(stats, gsheet_id, sheet_name):
    # Setup the Sheets API
    # from https://developers.google.com/sheets/api/quickstart/python
    SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)


    # Call the Sheets API

    # How the input data should be interpreted.
    value_input_option = 'USER_ENTERED'

    # Prepare the sheet for stats to be updated by clearing it and adding new header row
    clear = service.spreadsheets().values().clear(spreadsheetId=gsheet_id, range=sheet_name + '!A2:I', body={})
    response = clear.execute()
    # pprint(response)

    # Now update the stats
    value_range_body = {
        'values': stats.values.tolist()
    }

    request = service.spreadsheets().values().update(spreadsheetId=gsheet_id, range=sheet_name + '!A2',
                                                     valueInputOption=value_input_option,
                                                     body=value_range_body)
    response = request.execute()
    # pprint(response)

    # Put update timestamp in sheet
    updateTimestamp = service.spreadsheets().values().update(spreadsheetId=gsheet_id,
                                                             range=sheet_name + '!J1',
                                                             valueInputOption=value_input_option,
                                                             body={'values': [[str(dt.datetime.now())]]})
    responseTime = updateTimestamp.execute()

    return

def update_rosters(gsheet_id, sheet_name='nhl_rosters', savefile=False):
    rosters = util.get_rosters()

    if savefile:
        util.save_csv(sheet_name + '.csv', rosters)
    else:
        push_update_to_sheet(rosters, gsheet_id, sheet_name)
    return

def get_skater_stats(end, type=True):
    skaters = util.get_skater_stats(end, end, type)
    skaters = skaters[['playerId', 'playerName', 'playerPositionCode', 'points', 'gamesPlayed',
                       'playerBirthDate', 'playerHeight', 'playerWeight']]
    maskForwards = skaters['playerPositionCode'] != 'D'
    skaters.loc[maskForwards, 'playerPositionCode'] = 'F'

    return skaters

def get_goalie_stats(end,type=True):
    goalies = util.get_goalie_stats(end, end, type)

    # Applying custom scoring to goalie stats.
    # Goalie points are saves/9 - goals_against + points + shutouts
    goalies['points'] = goalies['saves'] / 9.0 - goalies['goalsAgainst']
    goalies['points'] += goalies['goals'] + goalies['assists'] + goalies['shutouts']
    goalies['points'] = goalies['points'].round(0)
    maskNegatives = goalies['points'] < 0
    goalies.loc[maskNegatives, 'points'] = 0

    goalies = goalies[['playerId', 'playerName', 'playerPositionCode', 'points', 'gamesPlayed',
                       'playerBirthDate', 'playerHeight', 'playerWeight']]
    return goalies

def update_stats(endYearOfSeason, regularSeason, gsheet_id, sheet_name='nhl_leaders', savefile=False):

    # Get skater and goalie stats, combine them in a dataframe.
    skaters = get_skater_stats(endYearOfSeason, regularSeason)
    goalies = get_goalie_stats(endYearOfSeason, regularSeason)
    all_stats = pd.concat([skaters, goalies], axis=0)
    all_stats = all_stats.sort_values('playerName')
    all_stats.fillna(0, inplace=True)

    if savefile:
        util.save_csv(sheet_name + '.csv', all_stats)
    else:
        push_update_to_sheet(all_stats, gsheet_id, sheet_name)

def main():
    parser = argparse.ArgumentParser(description='NHL Fantasy Stats')
    parser.add_argument('-g', '--gsheet', help='Push update to a Google Sheet instead of saving to a file.',
                        action='store_false', dest='save_file')
    parser.add_argument('-gid', '--gsheet_id', help='Google Sheet ID to push updates to', dest='gsheet_id')
    parser.add_argument('-r', '--roster', help='Filename or sheet name to save rosters to.', default='nhl_rosters',
                        dest='roster_sheet_name')
    parser.add_argument('-s', '--stats', help='Filename or sheet name to save stats to.', default='nhl_leaders',
                        dest='leader_sheet_name')
    parser.add_argument('-y', '--year', help='The ending year of the season to get.', type=int, default=2019,
                        dest='endYearOfSeason')
    parser.add_argument('-p', '--playoffs', help='Save playoff stats instead of regular season',
                        action='store_false', dest='regularSeason')
    parser.add_argument('-u', '--update_type', help='Update rosters (1), update stats (2) or update both (3)', type=int,
                        default=3, choices=[1,2,3], dest='update_type')
    args = parser.parse_args()

    if not args.save_file and args.gsheet_id is None:
        raise Exception("A Google Sheet ID must be supplied unless you want to save to a file.")

    if args.update_type != 2:
        update_rosters(args.gsheet_id, args.roster_sheet_name, args.save_file)
    if args.update_type > 1:
        update_stats(args.endYearOfSeason, args.regularSeason, args.gsheet_id, args.leader_sheet_name, args.save_file)

if __name__ == "__main__":
    main()

