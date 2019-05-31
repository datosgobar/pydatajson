from ckanapi import RemoteCKAN

from pydatajson.constants import REQUESTS_TIMEOUT


class CustomRemoteCKAN(RemoteCKAN):

    def __init__(self, address, apikey=None, user_agent=None, get_only=False,
                 verify_ssl=False, requests_timeout=REQUESTS_TIMEOUT):
        self.verify_ssl = verify_ssl
        self.requests_timeout = requests_timeout
        super(CustomRemoteCKAN, self).__init__(address, apikey,
                                               user_agent, get_only)

    def call_action(self, action, data_dict=None, context=None, apikey=None,
                    files=None, requests_kwargs=None):
        requests_kwargs = requests_kwargs or {}
        requests_kwargs.setdefault('verify', self.verify_ssl)
        requests_kwargs.setdefault('timeout', self.requests_timeout)
        return super(CustomRemoteCKAN, self).call_action(
            action, data_dict, context, apikey, files, requests_kwargs)
