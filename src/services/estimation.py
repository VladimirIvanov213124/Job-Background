import re
import time
from typing import List

from bs4 import BeautifulSoup
from selenium.webdriver import Remote

from src.dto import EstimateServiceResponse, LinkParseResponse
from src.services.clients import ChatGptClient, Logger, BrowserClientFactory


class EstimateService:

    def __init__(self, chat_gpt_client: ChatGptClient, factory_driver: BrowserClientFactory, logger: Logger):
        self._chat_gpt = chat_gpt_client
        self._driver = factory_driver.build_driver()
        self._logger = logger

    def _get_text_from_link_(self, link: str) -> str:
        try:
            self._driver.get(link)
            time.sleep(5)
            page_content = self._driver.page_source
            soup = BeautifulSoup(page_content, 'html.parser')
            return soup.text
        except Exception as e:
            self._logger.log_error(f'Estimation parse job link "{link}": {str(e)}')

    @staticmethod
    def _build_text_request_(html_text: str, user_comment: str) -> str:
        text = f'''
            Rate from 1 to 4 the relevance of matching job description: {html_text} and user description: {user_comment}
            Return a digit.
        '''
        return text

    @staticmethod
    def _preproc_string_(string: str) -> int:
        elements = re.findall(r'\d+', string)
        elements = [int(el) for el in elements if el.isdigit()]
        if not elements:
            return 1
        return elements[0]

    def _execute_one_(self, link: str, user_comment: str) -> int:
        try:
            html_text = self._get_text_from_link_(link)
            msg = self._build_text_request_(html_text, user_comment)
            response = self._chat_gpt.send_request(msg)
            score = self._preproc_string_(response)
            return score
        except Exception as e:
            self._logger.log_error(f'Exception Estimation: {str(e)}')
            return 1

    @staticmethod
    def _filter_jobs_(data: List[EstimateServiceResponse]) -> List[EstimateServiceResponse]:
        return [elem for elem in data if elem.score > 1]

    def execute(self, links: List[LinkParseResponse], job_description: str) -> List[EstimateServiceResponse]:
        results = []
        for link in links:
            score = self._execute_one_(link.job_url, job_description)
            results.append(EstimateServiceResponse(score=score, job_name=link.job_name, job_url=link.job_url))
        # results = self._filter_jobs_(results)
        return results
