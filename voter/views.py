from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import AnonymousBallot, Election, Position, Candidate, ParticipationLedger
from django.db.models import Count

@login_required
def voter_dashboard(request):
    all_elections = Election.objects.filter(is_active=True).order_by('-start_date')
    voter_profile = request.user.voter
    
    # Change 'VoterParticipation' to 'ParticipationLedger' here
    voted_position_ids = ParticipationLedger.objects.filter(
        voter=voter_profile
    ).values_list('position_id', flat=True)

    return render(request, 'voter/dashboard.html', {
        'elections': all_elections,
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

from django.db import transaction

from django.utils import timezone

@login_required
def vote_confirmation(request, candidate_id):
    # 1. Fetch Candidate and relevant info
    candidate = get_object_or_404(Candidate, id=candidate_id)
    position = candidate.position
    election = position.election
    voter_profile = request.user.voter

    # 2. SECURITY: Check if the election is actually running
    if not election.is_running:
        messages.error(request, f"Voting for {election.title} is currently closed.")
        return redirect('voter:voter_dashboard')

    # 3. SECURITY: Check Participation Ledger
    already_voted = ParticipationLedger.objects.filter(
        voter=voter_profile, 
        position=position
    ).exists()

    # 4. If already voted, redirect immediately (even on GET)
    if already_voted:
        messages.warning(request, f"You have already recorded your selection for {position.title}.")
        return redirect('voter:voter_dashboard')

    # 5. Handle POST (Official Vote Submission)
    if request.method == "POST":
        try:
            with transaction.atomic():
                # ALGORITHM STEP 1: Record Participation (Identity)
                ParticipationLedger.objects.create(
                    voter=voter_profile,
                    position=position
                )

                # ALGORITHM STEP 2: Record Choice (Anonymous)
                # No link to voter_profile here!
                AnonymousBallot.objects.create(
                    election=election,
                    position=position,
                    candidate=candidate
                )
            
            # Show the success receipt
            return render(request, 'voter/vote_success.html', {
                'candidate': candidate,
                'voted_at': timezone.now()
            })

        except Exception as e:
            # If database fails, rollback happens automatically due to atomic()
            messages.error(request, "A technical error occurred. Your vote was not recorded. Please try again.")
            return redirect('voter:voter_dashboard')

    # 6. Handle GET (Render the confirmation page)
    return render(request, 'voter/vote.html', {
        'candidate': candidate,
        'position': position,
        'election': election
    })

@login_required
def results(request):
    # Fetch all elections that are not hidden (Disabled)
    elections = Election.objects.exclude(is_active=False).order_by('-start_date')
    results_data = []

    for election in elections:
        positions_list = []
        for pos in election.positions.all():
            # Aggregate anonymous votes
            candidates = Candidate.objects.filter(position=pos).annotate(
                vote_count=Count('anonymousballot')
            ).order_by('-vote_count')

            # Identify the top candidate
            top_candidate = candidates.first() if candidates.exists() and candidates.first().vote_count > 0 else None
            total_votes = sum(c.vote_count for c in candidates)

            positions_list.append({
                'position': pos,
                'candidates': candidates,
                'total_votes': total_votes,
                'top_candidate': top_candidate,
            })

        results_data.append({
            'election': election,
            'status': election.status.lower(), # 'running' or 'closed'
            'positions': positions_list
        })

    return render(request, 'voter/results.html', {'results_data': results_data})

def landing(request):
    return render(request, 'landing.html')

@login_required
def election_ballot(request, election_id):
    # 1. Fetch the election
    election = get_object_or_404(Election, id=election_id)
    
    # 2. Safety Check: If election is disabled, don't show the ballot
    if election.status == "Disabled":
        messages.error(request, "This election event is currently hidden by the administrator.")
        return redirect('voter:voter_dashboard')

    # 3. Get all voting positions for this specific election
    positions = Position.objects.filter(election=election)
    
    # 4. PRIVACY ALGORITHM CHECK: 
    # Use 'ParticipationLedger' to find which positions this user has already voted for.
    # We follow the 'position__election' relationship to filter by this election.
    voter_profile = request.user.voter
    voted_ids = ParticipationLedger.objects.filter(
        voter=voter_profile, 
        position__election=election
    ).values_list('position_id', flat=True)

    # 5. Render the ballot page
    return render(request, 'voter/ballot.html', {
        'election': election,
        'positions': positions,
        'voted_ids': voted_ids
    })