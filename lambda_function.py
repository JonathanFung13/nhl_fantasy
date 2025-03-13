import json
import logging
from update_stats import update_stats, update_rosters

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
    datefmt='%m-%d %H:%M:%S'
)
def lambda_handler (event, context):

    update_type = event.get('update_type')
    season = event.get('season')
    gsheet_id = event.get('gsheet_id')

    if update_type != 2:
        update_rosters(gsheet_id, savefile=False)
    if update_type > 1:
        update_stats(season, True, gsheet_id, savefile=False)

    return {
        'statusCode': 200,
        'body': json.dumps(f'Job completed successfully {update_type} {season}')
    }

if __name__ == "__main__":
    logging.info('Do nothing')
