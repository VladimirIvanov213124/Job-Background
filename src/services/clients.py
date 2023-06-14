import logging
import logging.handlers
from datetime import datetime

import openai
from selenium.webdriver import FirefoxOptions
from selenium.webdriver import Remote


class ChatGptClient:
    def __init__(self, api_key: str):
        openai.api_key = api_key

    @staticmethod
    def send_request(raw_request: str) -> str:
        msg = [
            {
                'role': 'user',
                'content': raw_request,
            }
        ]
        chat = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=msg
        )
        reply = chat.choices[0].message.content
        return reply


class BrowserClient:
    @staticmethod
    def _build_driver_(driver_url: str):
        firefox_options = FirefoxOptions()
        firefox_options.set_capability('browserName', 'firefox')
        firefox_options.set_capability('browserVersion', '113.0')
        firefox_options.set_capability('selenoid:options', {
            "enableVideo": False,
            # 'timeout': '3m',
            'screenResolution': '1920x1080',
        })
        firefox_options.add_argument(
            'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/113.0'
        )

        driver = Remote(
            command_executor=driver_url,
            options=firefox_options,
        )
        # driver.set_page_load_timeout(180)
        return driver

    def __init__(self, driver_url: str):
        self.driver = self._build_driver_(driver_url)


class Logger:
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel('DEBUG')
        self._file_handler = logging.handlers.RotatingFileHandler(
            filename=f'loging_{datetime.now().strftime("%d-%m-%Y")}.log',
            mode='w',
            maxBytes=2000000,
            backupCount=10,
            encoding='utf-8'
        )
        self._formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
        self._file_handler.setFormatter(self._formatter)
        self._logger.addHandler(self._file_handler)

    def log_error(self, message: str):
        self._logger.error(message)

    def log_info(self, message: str):
        self._logger.info(message)
