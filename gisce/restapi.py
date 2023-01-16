from .base import RequestsClient, Model, ApiException


class RestApiModel(Model):
    def _call(self, method, *args, **kwargs):
        result = self.api.post(
            '{}/{}'.format(self.camelcase, method),
            json={'args': args, 'kwargs': kwargs}
        )
        if result.status_code == 200:
            return result.json()['res']
        else:
            raise ApiException('\n'.join(result.json().get('errors', [])))


class RestApiClient(RequestsClient):
    model_class = RestApiModel


