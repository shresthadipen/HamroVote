from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Count
from django.utils import timezone
import hashlib 

from .models import AnonymousBallot, Election, Position, Candidate, ParticipationLedger

# ALGORITHM: This processes the identity into a non-reversible string
def generate_voter_hash(user_id, position_id):
    # Salt adds extra security so hashes can't be guessed
    hash_input = f"{user_id}-{position_id}-secret-salt-2024"
    return hashlib.sha256(hash_input.encode()).hexdigest()

@login_required
def voter_dashboard(request):
    all_elections = Election.objects.filter(is_active=True).order_by('-start_date')
    
    # We need to find which positions the user has voted in.
    # Because of the Privacy Algorithm, we check the HASH for every position.
    voted_position_ids = []
    all_positions = Position.objects.filter(election__is_active=True)
    
    for pos in all_positions:
        # Generate the unique hash for this user + this position
        hash_input = f"{request.user.id}-{pos.id}-secret-salt-2024"
        v_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        # Check if this hash exists in the Participation Ledger
        if ParticipationLedger.objects.filter(voter_hash=v_hash).exists():
            voted_position_ids.append(pos.id)

    return render(request, 'voter/dashboard.html', {
        'elections': all_elections,
        'voted_position_ids': voted_position_ids
    })

@login_required
def election_ballot(request, election_id):
    election = get_object_or_404(Election, id=election_id)
    
    if election.status == "Disabled":
        messages.error(request, "This election event is hidden.")
        return redirect('voter:voter_dashboard')

    positions = Position.objects.filter(election=election)
    
    # FIX: Generating hashes to find which IDs the user has already cast
    voted_ids = []
    for pos in positions:
        # THE ALGORITHM: Re-create the hash to check participation
        hash_input = f"{request.user.id}-{pos.id}-secret-salt-2024"
        v_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        if ParticipationLedger.objects.filter(voter_hash=v_hash).exists():
            voted_ids.append(pos.id)

    return render(request, 'voter/ballot.html', {
        'election': election,
        'positions': positions,
        'voted_ids': voted_ids
    })

@login_required
def vote_confirmation(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    position = candidate.position
    election = position.election

    # --- THE ALGORITHM STEPS ---
    # 1. Create a dynamic input: Voter ID + Position ID
    # This ensures the hash is unique for every category a student votes in
    hash_input = f"{request.user.id}-{position.id}-secret-salt-2024"
    
    # 2. Generate SHA-256 Hash
    voter_hash = hashlib.sha256(hash_input.encode()).hexdigest()

    # 3. Check for hash in database
    already_voted = ParticipationLedger.objects.filter(voter_hash=voter_hash).exists()

    if request.method == "POST":
        if already_voted:
            messages.error(request, "Selection already recorded.")
            return redirect('voter:voter_dashboard')

        try:
            with transaction.atomic():
                # Store the HASH in the Ledger (Identity is now a secret code)
                ParticipationLedger.objects.create(voter_hash=voter_hash, position=position)
                
                # Drop choice in the Box (Completely unlinked)
                AnonymousBallot.objects.create(election=election, position=position, candidate=candidate)
            
            return render(request, 'voter/vote_success.html', {'candidate': candidate})
        except Exception:
            messages.error(request, "Database error.")
    
    return render(request, 'voter/vote.html', {'candidate': candidate})

@login_required
def results(request):
    elections = Election.objects.exclude(is_active=False).order_by('-start_date')
    results_data = []

    for election in elections:
        pos_list = []
        for pos in election.positions.all():
            candidates = Candidate.objects.filter(position=pos).annotate(
                vote_count=Count('anonymousballot')
            ).order_by('-vote_count')
            
            top_candidate = candidates.first() if candidates.exists() and candidates.first().vote_count > 0 else None
            total_votes = sum(c.vote_count for c in candidates)
            
            pos_list.append({
                'position': pos,
                'candidates': candidates,
                'total_votes': total_votes,
                'top_candidate': top_candidate,
            })

        results_data.append({
            'election': election,
            'status': election.status.lower(),
            'positions': pos_list
        })
    return render(request, 'voter/results.html', {'results_data': results_data})

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

def landing(request):
    return render(request, 'landing.html')