import logging

from chalktalk.settings.aws import CHALKTALK_LOGFILE_PATH


logger = logging.getLogger(__name__)

handler = logging.FileHandler(CHALKTALK_LOGFILE_PATH)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(filename)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

logging.getLogger('boto3').setLevel(logging.WARNING)
logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('nose').setLevel(logging.WARNING)
logging.getLogger('s3transfer').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
