from django.contrib import admin

from .models import Fight, FightStep, Instruction, Person, Unit


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type', 'team', 'health', 'attack_points')
    list_filter = ('team', 'type')


class FightStepInline(admin.TabularInline):
    model = FightStep
    extra = 0


@admin.register(Fight)
class FightAdmin(admin.ModelAdmin):
    list_display = ('id', 'fighter1', 'fighter2', 'winner', 'created_at')
    inlines = [FightStepInline]


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('external_id', 'name', 'age', 'rank')
    list_filter = ('rank',)
    search_fields = ('name',)


@admin.register(Instruction)
class InstructionAdmin(admin.ModelAdmin):
    list_display = ('key', 'fetched_at')
