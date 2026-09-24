from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jugadores', '0008_alter_estadisticajuego_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='jugador',
            name='foto',
            field=models.ImageField(blank=True, null=True, upload_to='jugadores/fotos/%Y/'),
        ),
    ]
