import uuid
from dataclasses import dataclass
from typing import Iterable, Optional

import configs


@dataclass
class Lecture:
    name: str

    url: str = None
    order: int = 0
    id: str = str(uuid.uuid4())


class LecturesRepository:
    def __init__(self, dynamodb, client):
        self.dynamodb = dynamodb
        self.client = client
        self.lectures_table = self.dynamodb.Table(configs.lectures_table_name)

    def find_all_lectures(self) -> Iterable[Lecture]:
        return sorted(self._find_all_lectures(), key=lambda x: x.order)

    def find_lecture(self, lecture_id: str) -> Optional[Lecture]:
        item = self.lectures_table.get_item(Key={'id': lecture_id})

        if 'Item' not in item:
            return None

        lecture = Lecture(**item['Item'])
        lecture.order = int(lecture.order)
        return lecture

    def _find_all_lectures(self) -> Iterable[Lecture]:
        def any_key(some_dict: dict):
            if some_dict is None:
                return None

            return list(some_dict.values())[0]

        paginator = self.client.get_paginator('scan')
        iterator = paginator.paginate(TableName=configs.lectures_table_name)

        for page in iterator:
            for item in page['Items']:
                yield Lecture(
                    id=any_key(item.get('id')),
                    order=int(any_key(item.get('order'))),
                    name=any_key(item.get('name')),
                    url=any_key(item.get('url')))

    def create_table(self):
        self.dynamodb.create_table(
            TableName=configs.lectures_table_name,
            KeySchema=[
                {
                    "AttributeName": "id",
                    "KeyType": "HASH"
                }
            ],
            AttributeDefinitions=[
                {
                    "AttributeName": "id",
                    "AttributeType": "S"
                }
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 5,
                "WriteCapacityUnits": 5
            }
        )
        print(f"Table {configs.lectures_table_name} created")
