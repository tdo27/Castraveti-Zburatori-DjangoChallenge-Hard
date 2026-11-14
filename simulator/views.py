import random

from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import UnitForm
from .models import Fight, FightStep, Instruction, Person, Unit
from .tasks import download_batch, register_people


# ==========================================================================
# Easy 1: formularul de adăugare (/unit)
# ==========================================================================

def unit_create_view(request):
    if request.method == 'POST':
        form = UnitForm(request.POST)
        if form.is_valid():
            unit = form.save()
            messages.success(request, f'Unit "{unit.name}" was added to the army!')
            return redirect('unit_create')
        messages.error(request, 'Please fix the errors below.')
    else:
        form = UnitForm()

    return render(request, 'simulator/unit_form.html', {'form': form})


# ==========================================================================
# Easy 2 + 4b: lista de luptători și statisticile (/unit/all)
# ==========================================================================

def unit_list_view(request):
    units = Unit.objects.all().order_by('id')

    team_stats = []
    for team_value, team_label in Unit.Team.choices:
        fights_count = Fight.objects.filter(
            Q(fighter1__team=team_value) | Q(fighter2__team=team_value)
        ).distinct().count()
        damage_caused = (
            FightStep.objects.filter(attacker__team=team_value)
            .aggregate(total=Sum('attack_points'))['total'] or 0
        )
        damage_taken = (
            FightStep.objects.filter(defender__team=team_value)
            .aggregate(total=Sum('attack_points'))['total'] or 0
        )
        team_stats.append({
            'team': team_label,
            'fights_count': fights_count,
            'damage_caused': damage_caused,
            'damage_taken': damage_taken,
        })

    return render(request, 'simulator/unit_list.html', {
        'units': units,
        'team_stats': team_stats,
    })


@require_POST
def unit_heal_view(request, unit_id):
    unit = get_object_or_404(Unit, pk=unit_id)
    unit.heal()
    messages.success(request, f'{unit.name} has been healed to {Unit.MAX_HEALTH} HP!')
    if request.POST.get('next') == 'unit_detail':
        return redirect('unit_detail', unit_id=unit.id)
    return redirect('unit_list')


# ==========================================================================
# Easy 3: simularea luptei
# ==========================================================================

@require_POST
def fight_simulate_view(request):
    selected_ids = request.POST.getlist('selected_units')

    if len(selected_ids) != 2:
        messages.error(request, 'Please select exactly two fighters to simulate a fight.')
        return redirect('unit_list')

    fighters = list(Unit.objects.filter(id__in=selected_ids).order_by('id'))
    if len(fighters) != 2:
        messages.error(request, 'One or more selected fighters could not be found.')
        return redirect('unit_list')

    fighter1, fighter2 = fighters

    if fighter1.team == fighter2.team:
        messages.error(request, 'Selected fighters must belong to different teams (Blue vs Red).')
        return redirect('unit_list')

    if fighter1.health <= 0 or fighter2.health <= 0:
        messages.error(request, 'Both fighters must have health above 0. Heal injured units first!')
        return redirect('unit_list')

    if fighter1.attack_points == 0 and fighter2.attack_points == 0:
        messages.error(request, 'At least one fighter must have AttackPoints > 0 so the fight can end.')
        return redirect('unit_list')

    with transaction.atomic():
        fight = Fight.objects.create(fighter1=fighter1, fighter2=fighter2)
        order = [fighter1, fighter2]
        steps = []
        step_number = 1

        while fighter1.health > 0 and fighter2.health > 0:
            attacker = order[(step_number - 1) % 2]
            defender = order[step_number % 2]

            damage = random.randint(0, attacker.attack_points)
            defender.health = max(0, defender.health - damage)

            steps.append(FightStep(
                fight=fight,
                step_number=step_number,
                attacker=attacker,
                defender=defender,
                attack_points=damage,
                attacker_health=attacker.health,
                defender_health=defender.health,
            ))
            step_number += 1

        FightStep.objects.bulk_create(steps)
        fighter1.save(update_fields=['health'])
        fighter2.save(update_fields=['health'])

        winner = fighter1 if fighter1.health > 0 else fighter2
        loser = fighter2 if winner == fighter1 else fighter1
        fight.winner = winner
        fight.save(update_fields=['winner'])

    messages.success(
        request,
        f'Fight complete! {winner.name} ({winner.team}) defeated {loser.name} in {len(steps)} steps.'
    )
    return redirect('unit_list')


# ==========================================================================
# Easy 2 + 4a: detaliile unei unități și istoricul luptelor (/unit/<id>)
# ==========================================================================

def unit_detail_view(request, unit_id):
    unit = get_object_or_404(Unit, pk=unit_id)
    fights = (
        Fight.objects.filter(Q(fighter1=unit) | Q(fighter2=unit))
        .select_related('fighter1', 'fighter2', 'winner')
        .prefetch_related('steps__attacker', 'steps__defender')
        .order_by('-created_at', '-id')
    )
    return render(request, 'simulator/unit_detail.html', {'unit': unit, 'fights': fights})


# ==========================================================================
# Hard: înregistrarea persoanelor și draftul, în background (/people)
# ==========================================================================

def people_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'register':
            register_people.delay()
            messages.success(request, 'Registration started in the background.')
        elif action == 'draft':
            download_batch.delay(0)
            messages.success(request, 'Drafting started in the background (one task per batch).')
        return redirect('people')

    people = Person.objects.all()
    return render(request, 'simulator/people.html', {
        'people': people,
        'total': people.count(),
        'ranked': people.exclude(rank__isnull=True).count(),
        'rank_counts': people.exclude(rank__isnull=True).values('rank').annotate(n=Count('id')).order_by('rank'),
        'instructions': Instruction.objects.order_by('fetched_at'),
    })
