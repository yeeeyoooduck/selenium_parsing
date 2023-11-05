import datetime
import time
import schedule

import os.path
import pickle
import sys
import pytz
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from program import get_prices

# Диапазон таблицы
TABLE_RANGE_NAME = 'Парсинг наличия и цены!A2:A'
# URL_ID таблицы
SPREADSHEET_ID = URL_ID
# API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
# Объявление списка с ссылками
raw_links = None


class GoogleSheet:
    service = None

    def __init__(self):
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                print('Ошибка. Google Sheets: flow')
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('sheets', 'v4', credentials=creds)

    def output(self, spreadsheet_id, sample_range_name):
        sheet = self.service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=sample_range_name).execute()
        values = result.get('values', [])
        if not values:
            print(f'Ошибка. Google Sheets. {sample_range_name}: Данные не найдены')
            return []
        return values

    def updateRangeValues(self, range, values):
        data = [{
            'range': range,
            'values': values
        }]
        body = {
            'valueInputOption': 'USER_ENTERED',
            'data': data
        }
        result = self.service.spreadsheets().values().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()

        updated_range = result.get('responses')[0].get('updatedRange')
        total_updated_cells = result.get("totalUpdatedCells")
        print(f"Диапазон: {updated_range}. Обновлены {total_updated_cells} ячейки.")


def timing_decorator(func):
    """
    Декоратор для рассчёта времени выполнения

    func: Функция, которую желаем обернуть
    return: Возвращает обёрнутую функцию
    """
    def wrapper():
        start_time = datetime.datetime.now()
        print(f'{start_time}\nНачало проверки...')
        func()
        end_time = datetime.datetime.now()
        print(f'Конец проверки...')
        execution_time = end_time - start_time
        print(f'Время выполнения: {execution_time}\n')

    return wrapper


def get_values():
    """
    Функция для получения значений из GoogleSheets

    return: Объект базы данных и ячейки с ссылками
    """
    global raw_links

    database = GoogleSheet()
    raw_links = database.output(SPREADSHEET_ID, TABLE_RANGE_NAME)

    return database, raw_links


@timing_decorator
def update_values():
    """
    Обновление наличия и цены в GoogleSheets.
    """

    database, links = get_values()
    for link, counter in zip(links, range(len(links))):
        try:
            result = get_prices(link[0])

            database_range = f'Парсинг наличия и цены!B{counter + 2}:D{counter + 2}'
            values = []

            if result == None:
                values = ['Ошибка', 'Ошибка', 'Ошибка']
                database.updateRangeValues(database_range, [values])
            else:
                if 'Розничная цена' in result:
                    values.append(int(result['Розничная цена']))
                else:
                    values.append(' ')
                if 'Оптовая цена' in result:
                    values.append(int(result['Оптовая цена']))
                else:
                    values.append(' ')
                if 'Наличие' in result:
                    values.append(result['Наличие'])
                else:
                    values.append(' ')

                database.updateRangeValues(database_range, [values])
        except:
            continue


def schedule():
    """
    Планирование выполнения задачи во временном диапазоне 8:00 - 22:00
    """
    try:
        current_time = datetime.datetime.now(moscow_tz).time()
        if current_time >= datetime.datetime.strptime('08:00:00',
                                                      '%H:%M:%S').time() and current_time <= datetime.datetime.strptime(
                '22:00:00', '%H:%M:%S').time():
            update()
        time.sleep(3600)
    except Exception as error:
        print(f'{error} Возникла непредвиденная ошибка. Переподключение...\n')
        time.sleep(10)
        schedule()


if __name__ == '__main__':
    # Устанавливаем часовой пояс Москвы
    moscow_tz = pytz.timezone('Europe/Moscow')

    while True:
        schedule()
