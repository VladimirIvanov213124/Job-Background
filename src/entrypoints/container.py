from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import Configuration
from dependency_injector.providers import Factory
from dependency_injector.providers import Singleton

from src.entrypoints.secrets import AppSecret
from src.services.algoritm import AlgorithmService
from src.services.clients import ChatGptClient, BrowserClient, Logger
from src.services.estimation import EstimateService
from src.services.generation import KeyWordGenerationService
from src.services.parser import LinkParseService
from src.tasks.common import AlgorithmTask


class AppContainer(DeclarativeContainer):
    config = Configuration(pydantic_settings=[AppSecret()])
    logger = Singleton(Logger)
    browser = Singleton(BrowserClient, driver_url=config.driver_url)
    chat_gpt_client = Singleton(ChatGptClient, api_key=config.gpt_key)

    link_parse_service = Factory(LinkParseService, driver=browser.provided.driver, logger=logger)
    estimate_service = Factory(EstimateService, chat_gpt_client=chat_gpt_client,
                               driver=browser.provided.driver, logger=logger)
    generation_service = Factory(KeyWordGenerationService, chat_gpt_client=chat_gpt_client, logger=logger)
    algorithm_service = Factory(
        AlgorithmService,
        link_parse_service=link_parse_service,
        estimate_service=estimate_service,
        generation_service=generation_service,
        logger=logger
    )
    task = Factory(AlgorithmTask, algorithm_service)
