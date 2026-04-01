from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Election, Position, Candidate, Vote
from django.db.models import Count

@login_required
def voter_dashboard(request):
    reg_no = request.user.username 
    # Fetch elections where this student is on the authorized list
    authorized_elections = Election.objects.filter(
        authorized_list__registration_number=reg_no,
        is_active=True
    ).prefetch_related('positions').distinct().order_by('-start_date')

    # Get IDs of positions the user already voted for
    voter_profile = request.user.voter
    voted_position_ids = Vote.objects.filter(voter=voter_profile).values_list('position_id', flat=True)

    return render(request, 'voter/dashboard.html', {
        'elections': authorized_elections,
        'voted_position_ids': voted_position_ids
    })

@login_required
def candidates(request, position_id):
    position = get_object_or_404(Position, id=position_id)
    candidates_list = Candidate.objects.filter(position=position, is_active=True)
    
    return render(request, 'voter/candidates.html', {
        'position': position,
        'candidates': candidates_list
    })

@login_required
def candidate_detail(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    return render(request, 'voter/candidate_detail.html', {'candidate': candidate})


@login_required
def vote_confirmation(request, candidate_id):
    # 1. Fetch data
    candidate = get_object_or_404(Candidate, id=candidate_id)
    position = candidate.position
    election = position.election
    
    # 2. Authorization Check (Ensure user is a registered Voter)
    try:
        voter_profile = request.user.voter
    except AttributeError:
        messages.error(request, "You do not have a voter profile. Please contact the administrator.")
        return redirect('voter:landing')

    # 3. Time Check (Using the Election model fields)
    if not election.is_running:
        messages.error(request, f"Voting for '{election.title}' is currently closed.")
        return redirect('voter:voter_dashboard')

    # 4. Anti-Fraud Check (Prevent double voting)
    already_voted = Vote.objects.filter(
        voter=voter_profile,
        election=election,
        position=position
    ).exists()

    # 5. Handle Post (The actual Voting process)
    if request.method == "POST":
        if already_voted:
            messages.error(request, "Security Alert: You have already cast your vote for this position.")
            return redirect('voter:voter_dashboard')

        try:
            # Use atomic to ensure the vote is saved perfectly or not at all
            with transaction.atomic():
                Vote.objects.create(
                    voter=voter_profile,
                    election=election,
                    position=position,
                    candidate=candidate,
                    ip_address=request.META.get('REMOTE_ADDR') # Log IP for security auditing
                )
            
            # Show the success page
            return render(request, 'voter/vote_success.html', {
                'candidate': candidate,
                'voted_at': timezone.now()
            })

        except Exception as e:
            messages.error(request, f"An error occurred while casting your vote: {e}")
            return redirect('voter:voter_dashboard')

    # 6. Handle GET (The confirmation page UI)
    return render(request, 'voter/vote.html', {
        'candidate': candidate,
        'position': position,
        'already_voted': already_voted
    })

@login_required
def results(request):
    election = Election.objects.filter(is_active=True).first()
    positions = Position.objects.filter(election=election)
    
    # PRIVACY ALGORITHM: Aggregate counts only
    results_data = []
    for pos in positions:
        candidates = Candidate.objects.filter(position=pos).annotate(
            vote_count=Count('vote')
        ).order_by('-vote_count')
        results_data.append({'position': pos, 'candidates': candidates})

    return render(request, 'voter/results.html', {
        'election': election,
        'results_data': results_data
    })

def landing(request):
    return render(request, 'landing.html')

@login_required
def election_ballot(request, election_id):
    # This page shows the Positions (President, VP) for the selected Election
    election = get_object_or_404(Election, id=election_id)
    positions = Position.objects.filter(election=election)
    
    # Check what they already voted for in THIS election
    voted_ids = Vote.objects.filter(voter=request.user.voter, election=election).values_list('position_id', flat=True)

    return render(request, 'voter/ballot.html', {
        'election': election,
        'positions': positions,
        'voted_ids': voted_ids
    })