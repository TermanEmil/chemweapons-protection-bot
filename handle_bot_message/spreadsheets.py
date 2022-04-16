import base64
import os
from datetime import datetime

import gspread
import pytz

from BotSession import BotSession
from Lecture import Lecture


def build_gspread_client() -> gspread.Client:
    base64_private_key = os.getenv('GSPREAD_PRIVATE_KEY').encode('utf-8')
    private_key = base64.decodebytes(base64_private_key).decode('utf-8')

    credentials = {
        "type": "service_account",
        "project_id": "psychologist-finder-bot",
        "private_key_id": os.getenv('GSPREAD_PRIVATE_KEY_ID'),
        "private_key": private_key,
        "client_email": os.getenv('GSPREAD_CLIENT_EMAIL'),
        "client_id": os.getenv('GSPREAD_CLIENT_ID'),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.getenv('GSPREAD_CLIENT_X509_CERT_URL')
    }

    return gspread.service_account_from_dict(credentials)


_client = build_gspread_client()


def add_to_spreadsheet(session: BotSession, lecture: Lecture):
    print(f"Adding to spreadsheets for chat_id: {session.chat_id}")
    submissions = _client.open_by_key(os.environ.get('GSPREAD_SPREADSHEET_ID')).sheet1
    submissions.append_row(_build_row(session, lecture))
    print(f"Added to spreadsheets for chat_id: {session.chat_id}")


def _build_row(session: BotSession, lecture: Lecture):
    return [
        f"{lecture.order}. {lecture.name}",
        session.user_name,
        session.contact_means,
        session.contact,
        datetime.now().astimezone(pytz.timezone('Europe/Kiev')).strftime('%H:%M:%S, %d/%m/%Y'),
        session.question
    ]
