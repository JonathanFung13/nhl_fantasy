This repository contains two python 3.7 scripts and a utility file that contains some helper functions.  The first is 
create-draft-viz-data.py and is used to generate data for my 'hockey-draft-viz' repo.  The second is update-stats.py and
it is for downloading the current NHL rosters and player stats from the NHL website.

### Using update-stats.py
Before running this script install all required packages.
`pip3 install -r requirements.txt`

This script allows you to either download the stats on to your machine as csv files or push the updates to a 
Google Sheet.
If you go with the Google Sheet option, perform these 4 actions:

1. Visit this [page](https://developers.google.com/sheets/api/quickstart/python)
1. Click the "Enable the Google Sheets API" button
1. On the pop-up, click "Download client configuration"
1. Save credentials.json to the root directory of this repo

When running the script from your terminal, there are a few keyword arguments that will change the way it runs.
* `-u` followed by `1`, `2`, or `3` selects one of 3 update types.  `1` downloads the latest rosters only.
`2` downloads the player stats only.  `3` downloads both the rosters and player stats, this is the default
* `-r` followed by a filename selects the filename to use with a roster download.  The default is "nhl_rosters.csv".
* `-s` followed by a filename selects the filename to use with a player stats download.  Default is "nhl_leaders.csv".
* `-y` followed by a year selects which season of player stats to download, the default is 2019 which will use the 
2018-19 stats.
* `-p` will download the playoff stats for the above year, rather than regular season stats.
* `-g` will push the rosters and/or player stats to a Google Sheet, and use their filenames as tab names.
* `-gid` followed by your an alphanumeric Google Sheet ID is required to push updates to a sheet. 

#### Pushing updates to a Google Sheet
Prior to running the script, create a Google Sheet with your Google account, and make note of its ID.  In the sheet, 
create one tab for roster updates called "nhl_rosters" and a second tab called "nhl_leaders".

Run the script in your terminal.  
`python3 update-stats.py -g -gid YOUR-GOOGLE-SHEET-ID`

The first time you run the application, you will be prompted to click on a link to open a browser and grant permission 
to the application.  Log in to your account and accept.
