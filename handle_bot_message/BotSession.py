from dataclasses import dataclass, asdict
from datetime import datetime

import pytz

import configs


@dataclass
class BotSession:
    chat_id: int
    form_step: str

    lecture_id_for_question: str = None
    user_name: str = None
    contact: str = None
    contact_means: str = None
    question: str = None
    last_updated: str = datetime.now(tz=pytz.UTC).isoformat()


class BotSessionsRepository:
    def __init__(self, dynamodb):
        self.dynamodb = dynamodb
        self.bot_sessions_table = self.dynamodb.Table(configs.bot_sessions_table_name)

    def get_session(self, chat_id: int) -> BotSession:
        item = self.bot_sessions_table.get_item(Key={'chat_id': chat_id})

        if 'Item' not in item:
            return BotSession(chat_id, form_step='RequestToStart')

        session = BotSession(**item['Item'])
        session.chat_id = int(session.chat_id)
        return session

    def update_session(self, session: BotSession):
        session.last_updated = datetime.now(tz=pytz.UTC).isoformat()
        self.bot_sessions_table.put_item(Item=asdict(session))

    def create_table(self):
        self.dynamodb.create_table(
            TableName=configs.bot_sessions_table_name,
            KeySchema=[
                {
                    "AttributeName": "chat_id",
                    "KeyType": "HASH"
                }
            ],
            AttributeDefinitions=[
                {
                    "AttributeName": "chat_id",
                    "AttributeType": "N"
                }
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 5,
                "WriteCapacityUnits": 5
            }
        )
        print(f"Table {configs.bot_sessions_table_name} created")
