# Etapa de draft adaugă un rang fiecărei persoane, deci baza de date e migrată.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simulator', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='rank',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
