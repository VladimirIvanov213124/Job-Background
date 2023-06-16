import random
import re
import time
from typing import List
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from selenium.webdriver import Remote
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from src.dto import LinkParseResponse, JobData
from src.services.clients import Logger, BrowserClientFactory


class LinkParseService:

    def __init__(self, factory_driver: BrowserClientFactory, logger: Logger):
        self._factory_driver = factory_driver
        self._logger = logger

    @staticmethod
    def _extract_domain_name_(url: str) -> str:
        res = urlparse(url)
        domain_url = f'{res.scheme}://{res.netloc}'
        return domain_url

    def _build_bs_from_link(self, link: str, driver: Remote) -> BeautifulSoup | None:
        wait = WebDriverWait(driver, 10)
        try:
            driver.get(link)
            time.sleep(2)
            try:
                wait.until(
                    EC.element_to_be_clickable((By.LINK_TEXT, 'Accept'))
                ).click()
            except Exception as e:
                self._logger.log_error(f'Cookie button click: {str(e)}')
                pass
            time.sleep(3)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)
            page_content = driver.page_source
            soup = BeautifulSoup(page_content.lower(), 'html.parser')
            self._logger.log_info(f'LinkParseService get page content from: {link}')
            return soup
        except Exception as e:
            self._logger.log_error(f'Driver get link: {link}: {str(e)}')

    @staticmethod
    def _extract_data_from_job_url_(domain_url: str, html: BeautifulSoup, job_name: str) -> JobData | None:
        try:
            tag_list = html.find_all(string=re.compile(job_name))
            for tag in tag_list:
                tag_parents = tag.parents
                for parent in tag_parents:
                    a_tag = parent.find('a')
                    if not a_tag:
                        continue
                    search_result = re.search(job_name.lower(), a_tag.text.lower())
                    if not search_result:
                        continue
                    job_href = a_tag.get('href')
                    if not job_href:
                        continue
                    job_url = domain_url + job_href
                    return JobData(url=job_url, name=tag)
        except Exception as e:
            return None

    def _parse_src_link_(self, src_link: str, key_word_list: List[str], driver: Remote) -> List[LinkParseResponse]:
        html = self._build_bs_from_link(src_link, driver)
        if not html:
            self._logger.log_error('HTML is None')
            return []
        domain_url = self._extract_domain_name_(src_link)
        out_data = []
        for key_word in key_word_list:
            job_data = self._extract_data_from_job_url_(domain_url, html, key_word)
            if not job_data:
                continue
            out_data.append(
                LinkParseResponse(
                    url=src_link,
                    job_name=job_data.name,
                    job_url=job_data.url
                )
            )
        return out_data

    def execute(self, src_link_list: List[str], key_word_list: List[str]) -> List[LinkParseResponse]:
        outputs = []
        driver = self._factory_driver.build_driver()
        with driver:
            for src_link in src_link_list:
                tmp_data = self._parse_src_link_(src_link, key_word_list, driver)
                outputs += tmp_data
                time.sleep(random.uniform(1, 3))
            self._logger.log_info(f"Parsed links: {outputs}")
            return outputs
