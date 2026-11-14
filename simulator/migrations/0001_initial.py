import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('type', models.CharField(choices=[('Infantry', 'Infantry'), ('Cannon', 'Cannon'), ('Cavalry', 'Cavalry'), ('Knight', 'Knight')], max_length=20, verbose_name='Type')),
                ('team', models.CharField(choices=[('Blue', 'Blue'), ('Red', 'Red')], default='Blue', max_length=10, verbose_name='Team')),
                ('health', models.IntegerField(default=100, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='Health')),
                ('attack_points', models.IntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(50)], verbose_name='AttackPoints')),
                ('profile_image_link', models.URLField(blank=True, max_length=500, verbose_name='ProfileImageLink')),
            ],
        ),
        migrations.CreateModel(
            name='Fight',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('fighter1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fights_as_fighter1', to='simulator.unit')),
                ('fighter2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fights_as_fighter2', to='simulator.unit')),
                ('winner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='fights_won', to='simulator.unit')),
            ],
        ),
        migrations.CreateModel(
            name='FightStep',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('step_number', models.PositiveIntegerField()),
                ('attack_points', models.IntegerField()),
                ('attacker_health', models.IntegerField()),
                ('defender_health', models.IntegerField()),
                ('attacker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attack_steps', to='simulator.unit')),
                ('defender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='defense_steps', to='simulator.unit')),
                ('fight', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='steps', to='simulator.fight')),
            ],
            options={
                'ordering': ['step_number'],
            },
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('external_id', models.IntegerField(unique=True)),
                ('name', models.CharField(max_length=200)),
                ('age', models.PositiveIntegerField()),
                ('extra', models.JSONField(blank=True, default=dict)),
            ],
            options={
                'ordering': ['external_id'],
            },
        ),
        migrations.CreateModel(
            name='Instruction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=100, unique=True)),
                ('content', models.JSONField()),
                ('fetched_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
