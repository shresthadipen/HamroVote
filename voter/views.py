from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Election, Position, Candidate, Vote
from django.db.models import Count

@login_required
def voter_dashboard(request):
    # Get the active election
    election = Election.objects.filter(is_active=True).first()
    positions = Position.objects.filter(election=election) if election else []
    
    # Check which positions this voter has already voted for
    # Privacy: We only check if a record exists in the Vote table for this voter
    voter_profile = request.user.voter
    voted_position_ids = Vote.objects.filter(
        voter=voter_profile, 
        election=election
    ).values_list('position_id', flat=True)

    context = {
        'election': election,
        'positions': positions,
        'voted_position_ids': voted_position_ids,
        'voted_count': len(voted_position_ids),
        'total_positions': positions.count()
    }
    return render(request, 'voter/dashboard.html', context)

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
    candidate = get_object_or_404(Candidate, id=candidate_id)
    voter_profile = request.user.voter
    
    # Check if they already voted for this position
    already_voted = Vote.objects.filter(
        voter=voter_profile, 
        position=candidate.position
    ).exists()

    if request.method == "POST":
        if already_voted:
            messages.error(request, "Security Alert: You have already cast your vote for this position.")
            return redirect('voter:voter_dashboard')

        # PRIVACY ALGORITHM: Create the vote
        # This links the voter to the vote for integrity (prevent double voting)
        # But we never show this link in the Results page
        Vote.objects.create(
            voter=voter_profile,
            election=candidate.position.election,
            position=candidate.position,
            candidate=candidate,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        return render(request, 'voter/vote_success.html', {'candidate': candidate})

    return render(request, 'voter/vote.html', {
        'candidate': candidate,
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
