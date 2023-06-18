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

from src.dto import FoundJobFromHtml
from src.services.clients import Logger, BrowserClientFactory


class LinkParseService:

    def __init__(self, factory_driver: BrowserClientFactory, logger: Logger, max_level: int = 1):
        self._factory_driver = factory_driver
        self._logger = logger
        self._visited_links = []
        self._added_links = set()
        self._max_level = max_level

    @staticmethod
    def _extract_domain_name_(url: str) -> str:
        res = urlparse(url)
        domain_url = f'{res.scheme}://{res.netloc}'
        return domain_url

    def _add_link_to_visited(self, link: str):
        self._visited_links.append(link)
        self._added_links.add(link)
        self._logger.log_info(f'New visited link: {link}')

    @staticmethod
    def _click_on_cookie_button_(driver: Remote):
        try:
            wait = WebDriverWait(driver, 3)
            wait.until(
                EC.element_to_be_clickable((By.LINK_TEXT, 'Accept'))
            ).click()
        except Exception as e:
            pass

    @staticmethod
    def _scroll_to_end_of_page_(driver: Remote):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

    def _build_html_(self, driver: Remote, link: str) -> BeautifulSoup | None:
        try:
            driver.get(link)
            self._click_on_cookie_button_(driver)
            self._scroll_to_end_of_page_(driver)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            return soup
        except Exception as e:
            self._logger.log_error(f'Build HTML for {link}: {str(e)}')
            return None

    @staticmethod
    def _preproc_link_(link: str, domain: str) -> str | None:
        out_link = ''
        result = urlparse(link)
        if not result.netloc and not result.path.startswith('/'):
            return None

        elif not result.netloc and result.path.startswith('/'):
            out_link = domain + link

        elif result.netloc:
            out_link = link

        if not out_link.startswith(domain):
            return None

        return out_link

    def _extract_unvisited_links_(self, soup: BeautifulSoup, domain_url: str) -> List[str]:
        a_tags = soup.find_all('a')
        all_links = list(set(a.get('href') for a in a_tags if a.get('href')))
        all_links = [self._preproc_link_(link, domain_url) for link in all_links]
        all_links = [link for link in all_links if link]
        unvisited_links = [link for link in all_links if link not in self._added_links]
        for unvisited_link in unvisited_links:
            self._added_links.add(unvisited_link)
        return unvisited_links

    def _extract_jobs_from_html_(self, soup: BeautifulSoup,
                                 job_name_list: List[str], domain: str) -> List[FoundJobFromHtml]:
        found_jobs = set()
        for job_name in job_name_list:
            pattern = re.compile(job_name, re.IGNORECASE)
            tags = soup.find_all('a')
            tags = [tag for tag in tags if (tag.get('href') and tag.text)]
            tags = [tag for tag in tags if re.search(pattern, tag.text)]
            for tag in tags:
                tmp = FoundJobFromHtml(name=tag.text, link=self._preproc_link_(tag.get('href'), domain))
                found_jobs.add(tmp)
        found_jobs = list(found_jobs)
        self._logger.log_info(f'Job Extracted: {found_jobs}')
        return found_jobs

    def _parse_link_(self, driver: Remote, link: str, job_name_list: List[str], domain_url: str, level: int):
        job_data = []
        soup = self._build_html_(driver, link)
        if soup is None:
            return job_data
        self._add_link_to_visited(link)
        job_data += self._extract_jobs_from_html_(soup, job_name_list, domain_url)
        unvisited_links = self._extract_unvisited_links_(soup, domain_url)

        if level < self._max_level:
            for unvisited_link in unvisited_links:
                job_data += self._parse_link_(driver, unvisited_link, job_name_list, domain_url, level + 1)

        return job_data

    def _execute_for_platform_(self, platform_link: str, job_name_list: List[str]) -> List:
        domain_url = self._extract_domain_name_(platform_link)
        driver = self._factory_driver.build_driver()
        with driver:
            job_data = self._parse_link_(driver, platform_link, job_name_list, domain_url, level=1)
            return job_data

    def execute(self, platform_link_list: List[str], job_name_list: List[str]) -> List[FoundJobFromHtml]:
        outputs = []
        for platform_list in platform_link_list:
            outputs += self._execute_for_platform_(platform_list, job_name_list)
            time.sleep(random.uniform(1, 3))
        return outputs
