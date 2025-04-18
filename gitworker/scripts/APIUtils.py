from functools import wraps
import logging
from pywaclient.exceptions import (
        ConnectionException,
        UnexpectedStatusException,
        InternalServerException,
        UnauthorizedRequest,
        AccessForbidden,
        ResourceNotFound,
        UnprocessableDataProvided,
        FailedRequest
        )

class WorldAnvilUtils(object):
    def endpoint_exceptions_wrapper(func):
        @wraps(func)
        def inner(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except ConnectionException as connection_exception:
                logging.warning(f"Unable to connect to WorldAnvil API. {connection_exception}")
                raise Exception(f"{connection_exception}")
            except InternalServerException as internal_server_exception:
                logging.warning(f"WorldAnvil server unable to process request. {internal_server_exception}")
                raise Exception(f"{internal_server_exception}")
            except UnauthorizedRequest as unauthorized_request:
                logging.warning(f"User unauthorized to process this request. {unauthorized_request}")
                raise Exception(f"{unauthorized_request}")
            except AccessForbidden as access_forbidden:
                logging.warning(f"Invalid permissions to view requested resource. {access_forbidden}")
                raise Exception(f"{access_forbidden}")
            except ResourceNotFound as resource_not_found:
                logging.warning(f"Requested resource not found. {resource_not_found}")
                raise Exception(f"{resource_not_found}")
            except UnprocessableDataProvided as unprocessable_data_provided:
                logging.error(f"Request could not be processed. {unprocessable_data_provided}")
                raise Exception(f"{unprocessable_data_provided}")
            except FailedRequest as failed_request:
                logging.error(f"Request failed. {failed_request}")
            except Exception as e:
                logging.warning(f"Could not fetch user identity")
                raise Exception(f"{e}")
        
        return inner
