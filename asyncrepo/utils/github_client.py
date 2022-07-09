"""
Welcome to Hackville! Okay, so let me explain what's going on here.

1. We're superclassing the GH client to override some methods we use with async versions.
    We do this by overriding the default requester for the client with a new one that
    refuses to actually process any requests, but instead raises an exception with the request's
    arguments and kwargs which can then be used to make an async request.

    Once the async request is ready, we'll add in the response object to the session object and
    then call the original method again. This is safe in terms of async/await, but it's not
    thread-safe since it assumes that the response added to the session will only be accessed
    by the subsequent call to the original method. Because of this, a threading lock is added
    to that critical section of code (not that this is really intended to be used in a threaded
    environment, but we might as well strive for thread-safety right?).

2. We're also patching the PaginatedList and GithubOject classes to add some async methods we use.

    The PaginatedList class has a get_page method that returns a PaginatedList object. An async version
    of this, get_page_async, is monkey-patched to handle this asynchronously. The PaginatedList class also has
    a totalCount property which we monkey-patch in an async equivalent method `total_count_async` to handle.

    The GithubObject class has a raw_data property that returns a dict. But, it also needs to make
    HTTP requests to get the data. An async version of this, raw_data_async, is monkey-patched to
    handle this asynchronously.

Obviously this is API abuse, but this entire project is at the mercy of external APIs anyway so... Chào!
"""

import threading

from github import Github
from github.PaginatedList import PaginatedList
from github.GithubObject import GithubObject
from github.Requester import Requester, HTTPRequestsConnectionClass, HTTPSRequestsConnectionClass
from requests import Session

from asyncrepo.utils.http_client import HttpClient

DEFAULT_BASE_URL = "https://api.github.com"
DEFAULT_TIMEOUT = 15
DEFAULT_PER_PAGE = 30


class GithubClient(Github):
    def __init__(self,
                 login_or_token=None,
                 password=None,
                 jwt=None,
                 base_url=DEFAULT_BASE_URL,
                 timeout=DEFAULT_TIMEOUT,
                 user_agent="PyGithub/Python (asyncrepo)",
                 per_page=DEFAULT_PER_PAGE,
                 verify=True,
                 retry=None,
                 pool_size=None):
        kwargs = dict(login_or_token=login_or_token,
                      password=password,
                      jwt=jwt,
                      base_url=base_url,
                      timeout=timeout,
                      user_agent=user_agent,
                      per_page=per_page,
                      verify=verify,
                      retry=retry,
                      pool_size=pool_size)
        super().__init__(**kwargs)
        self._Github__requester = GithubRequester(**kwargs)
        patch_paginated_list()
        patch_github_object()

    async def get_user(self, *args, **kwargs):
        return await _async_github_request(super().get_user, *args, **kwargs)

    async def get_repo(self, *args, **kwargs):
        return await _async_github_request(super().get_repo, *args, **kwargs)

    async def get_organization(self, *args, **kwargs):
        return await _async_github_request(super().get_organization, *args, **kwargs)


async def _async_github_request(sync_method, *args, **kwargs):
    """
    Creates an async version of the sync method by catching the requests being
    made and performing them with non-blocking aiohttp requests, then calling
    the sync method again which will then get the response from the session.

    Assumes that only one request will be made from the sync method. If that
    assumption fails, this will throw an IOBoundRequestError. This could be
    fixed by attempting multiple calls to the sync method up to some maximum
    number of times, but that doesn't seem necessary for now.
    """
    try:
        r = sync_method(*args, **kwargs)
    except IOBoundRequestError as e:
        http_args, http_kwargs = e.args, e.kwargs
        async with HttpClient(add_ssl_context=e.session.add_ssl_context) as session:
            http_kwargs.pop('verify', None)
            async with session.request(*http_args, **http_kwargs) as response:
                setattr(response, "status_code", response.status)
                setattr(response, "text", await response.text())
                with e.session.async_response_lock:
                    try:
                        e.session.async_response = response
                        r = sync_method(*args, **kwargs)
                    finally:
                        e.session.async_response = None
    return r


class FakeHTTPSRequestsConnectionClass(HTTPSRequestsConnectionClass):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = FakeSession(True)


class FakeHTTPRequestsConnectionClass(HTTPRequestsConnectionClass):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = FakeSession(False)


class IOBoundRequestError(Exception):
    def __init__(self, args, kwargs, session):
        self.args = args
        self.kwargs = kwargs
        self.session = session


class FakeSession(Session):
    def __init__(self, add_ssl_context: bool, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.async_response = None
        self.async_response_lock = threading.Lock()
        self.add_ssl_context = add_ssl_context

    def request(self, *args, **kwargs):
        if self.async_response:
            return self.async_response
        raise IOBoundRequestError(args, kwargs, self)


class GithubRequester(Requester):
    _Requester__httpsConnectionClass = FakeHTTPSRequestsConnectionClass
    _Requester__httpConnectionClass = FakeHTTPRequestsConnectionClass


def patch_paginated_list():
    setattr(PaginatedList, "get_page_async", get_page_async)
    setattr(PaginatedList, "total_count_async", total_count_async)


def patch_github_object():
    setattr(GithubObject, "raw_data_async", raw_data_async)


async def get_page_async(self, *args, **kwargs):
    return await _async_github_request(self.get_page, *args, **kwargs)


async def total_count_async(self, *args, **kwargs):
    return await _async_github_request(lambda: self.totalCount, *args, **kwargs)


async def raw_data_async(self, *args, **kwargs):
    return await _async_github_request(lambda: self.raw_data, *args, **kwargs)
