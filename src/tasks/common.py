from typing import List

from celery import Task

from src.dto import EstimateServiceResponse
from src.services.algoritm import AlgorithmService


class AlgorithmTask(Task):
    name = 'AlgorithmTask'

    def __init__(self, algorithm_service: AlgorithmService):
        self.algorithm_service = algorithm_service

    def run(self, user_job_description: str, links: List[str]) -> List[EstimateServiceResponse]:
        out = self.algorithm_service.execute(user_job_description, links)
        return out
