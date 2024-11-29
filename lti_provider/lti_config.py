# lti_provider/utils.py

from pylti1p3.registration import Registration
from pylti1p3.tool_config import ToolConfAbstract

from .models import ToolConsumerModel


class DjangoToolConf(ToolConfAbstract):
    def __init__(self, model: type[ToolConsumerModel]):
        self.model = model

    def _get_registration_instance(
        self, iss: str, client_id: str = None
    ) -> Registration | None:
        """Find a registration instance by issuer and optional client id"""

        registration = Registration()
        try:
            if client_id:
                tool_consumer = self.model.objects.get(issuer=iss, client_id=client_id)
            else:
                tool_consumer = self.model.objects.get(issuer=iss)
            registration.set_issuer(tool_consumer.issuer).set_client_id(
                tool_consumer.client_id
            ).set_key_set_url(tool_consumer.key_set_url).set_auth_token_url(
                tool_consumer.auth_token_url
            ).set_auth_login_url(
                tool_consumer.auth_login_url
            ).set_tool_private_key(
                tool_consumer.private_key
            ).set_tool_public_key(
                tool_consumer.public_key
            )

            return registration

        except self.model.DoesNotExist:
            return None

    def find_registration_by_issuer(self, iss: str, *args, **kwargs) -> Registration:
        """Find a registration when the issuer has only one client ID."""
        registration_data = self._get_registration_instance(iss)
        if not registration_data:
            raise ValueError(f"No registration found for issuer: {iss}")
        return registration_data

    # def find_registration_by_params(
    #     self, iss: str, client_id: str, *args, **kwargs
    # ) -> None:
    #     """Will not implement this because we dont need it right now"""
    #     pass
    #
    # def find_deployment(self, iss: str, deployment_id: str) -> None:
    #     """Will not implement this because we dont need it right now"""
    #     pass
    #
    # def find_deployment_by_params(
    #     self, iss: str, deployment_id: str, client_id: str, *args, **kwargs
    # ) -> None:
    #     """Will not implement this because we dont need it right now"""
    #     pass
