import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Crea (o actualiza la contraseña de) un superusuario a partir de variables "
        "de entorno, para poder usarlo en el build de producción sin terminal interactiva. "
        "No hace nada si las variables no están definidas."
    )

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')

        if not username or not password:
            self.stdout.write('DJANGO_SUPERUSER_USERNAME/PASSWORD no definidas, se omite.')
            return

        user, creado = User.objects.get_or_create(
            username=username, defaults={'email': email, 'is_staff': True, 'is_superuser': True},
        )
        user.is_staff = True
        user.is_superuser = True
        user.email = email or user.email
        user.set_password(password)
        user.save()

        if creado:
            self.stdout.write(self.style.SUCCESS(f'Superusuario "{username}" creado.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Superusuario "{username}" ya existía — contraseña actualizada.'))
