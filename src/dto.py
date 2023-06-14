from typing import NamedTuple


class EstimateServiceResponse(NamedTuple):
    score: int
    job_name: str
    job_url: str


class JobData(NamedTuple):
    url: str = ''
    name: str = ''


class LinkParseResponse(NamedTuple):
    url: str
    job_name: str
    job_url: str
