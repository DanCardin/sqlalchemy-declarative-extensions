import base64
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from snowflake.sqlalchemy import URL as SnowflakeURL
from sqlalchemy import create_engine

p_key = serialization.load_pem_private_key(
    base64.b64decode(os.environ["SNOWFLAKE_PRIVATE_KEY"]),
    password=os.environ["SNOWFLAKE_PRIVATE_KEY_PASSWORD"].encode(),
    backend=default_backend(),
)

private_key_bytes = p_key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)

url = SnowflakeURL(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    user=os.environ["SNOWFLAKE_USERNAME"],
    database=os.environ["SNOWFLAKE_DATABASE"],
    role=os.environ["SNOWFLAKE_ROLE"],
    warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
)
engine = create_engine(url, connect_args={"private_key": private_key_bytes})
