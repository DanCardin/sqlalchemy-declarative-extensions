from sqlalchemy import MetaData
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.model import Models
from sqlalchemy_declarative_extensions.model.compare import compare_models


def model_query(models: Models):
    def receive_after_create(metadata: MetaData, connection: Connection, **_):
        results = compare_models(connection, metadata, models)
        for result in results:
            query = result.render(metadata)
            connection.execute(query)

    return receive_after_create
