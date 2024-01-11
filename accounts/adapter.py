from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings


class CustomAccountAdapter(DefaultAccountAdapter):
    def send_mail(self, template_prefix, email, context):
        if 'password_reset_url' in context:
            pass_reset_keys = context['password_reset_url'].split('/')
            context['password_reset_url'] = \
                f'{settings.REDIRECT_URL}/reset-password/{pass_reset_keys[-3]}/{pass_reset_keys[-2]}'
        msg = self.render_mail(template_prefix, email, context)
        msg.send()
