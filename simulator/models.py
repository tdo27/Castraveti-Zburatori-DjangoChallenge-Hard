from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


# --------------------------------------------------------------------------
# Easy: unități, lupte și istoricul pas cu pas
# --------------------------------------------------------------------------

class Unit(models.Model):
    MAX_HEALTH = 100

    class UnitType(models.TextChoices):
        INFANTRY = 'Infantry', 'Infantry'
        CANNON = 'Cannon', 'Cannon'
        CAVALRY = 'Cavalry', 'Cavalry'
        KNIGHT = 'Knight', 'Knight'

    class Team(models.TextChoices):
        BLUE = 'Blue', 'Blue'
        RED = 'Red', 'Red'

    name = models.CharField(max_length=100, verbose_name='Name')
    type = models.CharField(max_length=20, choices=UnitType.choices, verbose_name='Type')
    team = models.CharField(max_length=10, choices=Team.choices, default=Team.BLUE, verbose_name='Team')
    health = models.IntegerField(
        default=MAX_HEALTH,
        validators=[MinValueValidator(0), MaxValueValidator(MAX_HEALTH)],
        verbose_name='Health',
    )
    attack_points = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        verbose_name='AttackPoints',
    )
    profile_image_link = models.URLField(max_length=500, blank=True, verbose_name='ProfileImageLink')

    @property
    def is_injured(self):
        return self.health < self.MAX_HEALTH

    def heal(self):
        self.health = self.MAX_HEALTH
        self.save(update_fields=['health'])

    def __str__(self):
        return f"{self.name} ({self.team} - {self.type})"


class Fight(models.Model):
    fighter1 = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='fights_as_fighter1')
    fighter2 = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='fights_as_fighter2')
    winner = models.ForeignKey(
        Unit, on_delete=models.SET_NULL, null=True, blank=True, related_name='fights_won',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Fight #{self.id}: {self.fighter1.name} vs {self.fighter2.name}"


class FightStep(models.Model):
    fight = models.ForeignKey(Fight, on_delete=models.CASCADE, related_name='steps')
    step_number = models.PositiveIntegerField()
    attacker = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='attack_steps')
    defender = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='defense_steps')
    attack_points = models.IntegerField()
    attacker_health = models.IntegerField()
    defender_health = models.IntegerField()

    class Meta:
        ordering = ['step_number']

    def __str__(self):
        return (
            f"Fight #{self.fight_id} Step {self.step_number}: "
            f"{self.attacker.name} -> {self.defender.name} ({self.attack_points} dmg)"
        )


# --------------------------------------------------------------------------
# Hard: persoanele înregistrate și instrucțiunile primite de la server
# --------------------------------------------------------------------------

class Person(models.Model):
    external_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=200)
    age = models.PositiveIntegerField()
    # adăugat prin migrarea 0002, după cum cere etapa de draft
    rank = models.CharField(max_length=100, null=True, blank=True)
    # orice alt câmp venit de la server (ex. "key", "health")
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['external_id']

    def __str__(self):
        return f"{self.name} ({self.age})"


class Instruction(models.Model):
    key = models.CharField(max_length=100, unique=True)
    content = models.JSONField()
    fetched_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key
