import json
import logging
from datetime import datetime
import boto3
from src.infrastructure.config.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AWS(object):
    def __init__(self) -> None:
        config = Config()
        self.aws_config = {
            "bucket_name": config.bucket_name,
            "access_key": config.access_key,
            "secret_key": config.secret_key,
            "beta_bucket": config.beta_bucket,
            "prod_bucket": config.prod_bucket,
        }

    def get_aws_session(self) -> object:
        """Creates a new AWS session."""
        try:
            return boto3.Session(
                aws_access_key_id=self.aws_config["access_key"],
                aws_secret_access_key=self.aws_config["secret_key"],
            )
        except Exception as e:
            logger.error(f"Failed to create AWS session: {e}")
            raise

    def get_s3_bucket(self) -> object:
        """Gets the S3 bucket resource."""
        session = self.get_aws_session()
        return session.resource("s3")

    def send_items_to_s3_bucket(
        self, items, file_name, sub_folder, folder="beta"
    ) -> None:
        """Sends items to an S3 bucket."""
        today = datetime.today()
        year, week_num, _ = today.isocalendar()
        try:
            s3 = self.get_s3_bucket()
            json_string = json.dumps(items, default=str)

            # Construct the S3 key
            s3_key = f"{folder}/{sub_folder}/{year}/{week_num}/{file_name}"

            # Put the object into the S3 bucket
            s3.meta.client.put_object(
                Bucket=self.aws_config["bucket_name"],
                Key=s3_key,
                Body=json_string,
            )
            logger.info(f"Successfully uploaded to S3: {s3_key}")
        except Exception as e:
            logger.error(f"Failed to send items to S3: {e}")
