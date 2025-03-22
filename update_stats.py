#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import datetime as dt
import pytz
import utilities as util
import os.path


def push_update_to_sheet(stats, gsheet_id, sheet_name):
    # Setup the Sheets API
    # from https://developers.google.com/sheets/api/quickstart/python
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    credentials_file = 'service_account.json'  # Replace with your actual service account file
    creds = None

    if os.path.exists(credentials_file):
        creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
    else:
        raise FileNotFoundError("Service account JSON file not found. Please ensure it's in the correct location.")

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
        'values': stats#.values.tolist()
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
                                                             body={'values': [[dt.datetime.now(pytz.timezone('America/Edmonton')).strftime('%Y-%m-%d %H:%M:%S')]]})
    responseTime = updateTimestamp.execute()

    return

def update_rosters(gsheet_id, sheet_name='nhl_rosters', savefile=False):
    raw_rosters = util.get_rosters()
    clean_rosters = [{
        'playerId': r.get('id'),
        'lastName': r.get('lastName'),
        'firstName': r.get('firstName'),
        'skaterFullName': f"{r.get('firstName')} {r.get('lastName')}",
        'position': r.get('position'),
        'team': r.get('team'),
        'onRoster': r.get('onRoster'),
        'birthDate': r.get('birthDate'),
        'height': r.get('height'),
        'weight': r.get('weight')
    } for r in raw_rosters]
    rosters = sorted(clean_rosters, key=lambda x: x['skaterFullName'])
    stats_list = [list(r.values()) for r in rosters]
    push_update_to_sheet(stats_list, gsheet_id, sheet_name)
    return

def get_skater_stats(end, type=True):
    skaters = util.get_skater_stats(end, end, type)
    clean_skaters = [{
        'playerId': skater.get('playerId'),
        'skaterFullName': skater.get('skaterFullName'),
        'positionCode': 'D' if skater.get('positionCode') == 'D' else 'F',
        'points': skater.get('points'),
        'gamesPlayed': skater.get('gamesPlayed')
    } for skater in skaters]

    return clean_skaters

def get_goalie_stats(end,type=True):
    goalies = util.get_goalie_stats(end, end, type)

    # Applying custom scoring to goalie stats.
    # Goalie points are saves/9 - goals_against + points + shutouts * 2 + wins
    clean_goalies = []
    for goalie in goalies:
        pts = goalie.get('saves') / 9.0 - goalie.get('goalsAgainst') + goalie.get('goals') + goalie.get('assists') + goalie.get('shutouts') * 2 + goalie.get('wins')
        cleaned = {
            'playerId': goalie.get('playerId'),
            'skaterFullName': goalie.get('goalieFullName'),
            'positionCode': 'G',
            'points': 0 if pts < 0 else round(pts, 0),
            'gamesPlayed': goalie.get('gamesPlayed')
        }
        clean_goalies.append(cleaned)
    return clean_goalies

def update_stats(endYearOfSeason, regularSeason, gsheet_id, sheet_name='nhl_leaders', savefile=False):

    # Get skater and goalie stats, combine them in a dataframe.
    skaters = get_skater_stats(endYearOfSeason, regularSeason)
    goalies = get_goalie_stats(endYearOfSeason, regularSeason)
    all_stats = skaters + goalies
    all_stats = sorted(all_stats, key=lambda x: x['skaterFullName'])
    stats_list = [list(stat.values()) for stat in all_stats]
    push_update_to_sheet(stats_list, gsheet_id, sheet_name)
    return

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        datefmt='%m-%d %H:%M:%S'
    )
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
