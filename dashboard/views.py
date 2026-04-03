import csv, io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone
from accounts.models import Student_list, Voter
from voter.models import Election, Position, Candidate, ParticipationLedger, AnonymousBallot
from .forms import StudentManualForm, ElectionForm, CandidateForm 


# ================= 1. ANALYTICS (Home) =================
@staff_member_required
def admin_dashboard(request):
    # Analytics Stats
    total_students = Student_list.objects.count()
    registered_voters = Voter.objects.count()
    total_votes = AnonymousBallot.objects.count() 
    
    # Calculate Turnout %
    turnout = round((total_votes / registered_voters * 100), 1) if registered_voters > 0 else 0

    # Privacy Algorithm: Get vote counts per position without voter names
    positions = Position.objects.annotate(v_count=Count('anonymousballot'))
    pos_labels = [p.title for p in positions]
    pos_data = [p.v_count for p in positions]

    context = {
        'total_students': total_students,
        'registered_voters': registered_voters,
        'total_votes': total_votes,
        'turnout': turnout,
        'pos_labels': pos_labels,
        'pos_data': pos_data,
    }
    return render(request, 'admin_dashboard.html', context)


# ================= 2. STUDENT MANAGEMENT =================

@staff_member_required
def manage_students(request):
    # 1. Fetch ALL students from the global list
    students = Student_list.objects.all().order_by('-id')

    if request.method == "POST":
        # Handle Manual Add
        if 'manual_add' in request.POST:
            reg_no = request.POST.get('registration_number').strip()
            name = request.POST.get('full_name').strip()
            
            # Save to the global Student_list
            Student_list.objects.get_or_create(
                registration_number=reg_no,
                defaults={'full_name': name}
            )
            messages.success(request, f"Student {name} added to authorized list.")
            
        # Handle Bulk CSV Upload
        elif 'bulk_upload' in request.POST:
            csv_file = request.FILES.get('file')
            if csv_file and csv_file.name.endswith('.csv'):
                data_set = csv_file.read().decode('UTF-8')
                io_string = io.StringIO(data_set)
                next(io_string) # Skip header
                for row in csv.reader(io_string):
                    if len(row) >= 2:
                        Student_list.objects.get_or_create(
                            registration_number=row[0].strip(),
                            defaults={'full_name': row[1].strip()}
                        )
                messages.success(request, "Bulk students imported successfully.")
        
        return redirect('dashboard:manage_students')

    # Pass the 'students' list to the template
    return render(request, 'manage_students.html', {'voters': students})


# ================= 3. POSITION MANAGEMENT =================
@staff_member_required
def manage_positions(request):
    # Fetch all elections so we can choose one
    elections = Election.objects.all().order_by('-created_at')
    positions = Position.objects.all().order_by('-id')

    if request.method == "POST" and 'add_position' in request.POST:
        title = request.POST.get('title')
        description = request.POST.get('description')
        election_id = request.POST.get('election_id')

        election = get_object_or_404(Election, id=election_id)

        Position.objects.create(
            election=election,
            title=title,
            description=description
        )
        messages.success(request, f"Position '{title}' added to {election.title}.")
        return redirect('dashboard:manage_positions')

    return render(request, 'manage_positions.html', {
        'positions': positions,
        'elections': elections
    })

# ================= 4. CANDIDATE MANAGEMENT =================
@staff_member_required
def manage_candidates(request):
    elections = Election.objects.all().order_by('-start_date')
    
    if request.method == "POST" and 'add_candidate' in request.POST:
        pos_id = request.POST.get('position')
        name = request.POST.get('name')
        bio = request.POST.get('bio')
        manifesto = request.POST.get('manifesto')
        photo = request.FILES.get('photo')

        position = get_object_or_404(Position, id=pos_id)
        
        Candidate.objects.create(
            position=position,
            name=name,
            bio=bio,
            manifesto=manifesto,
            photo=photo
        )
        messages.success(request, f"Candidate {name} registered successfully.")
        return redirect('dashboard:manage_candidates')

    return render(request, 'manage_candidates.html', {'elections': elections})

# ================= 5. DELETE ACTIONS =================
@staff_member_required
def delete_candidate(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    candidate.delete()
    messages.warning(request, "Candidate removed.")
    return redirect('dashboard:manage_candidates')


def edit_position(request, pk):
    position = get_object_or_404(Position, pk=pk)
    if request.method == "POST":
        position.title = request.POST.get('title')
        position.description = request.POST.get('description')
        position.save()
        messages.success(request, f"Position '{position.title}' updated.")
        return redirect('dashboard:manage_positions')
    return render(request, 'edit_position.html', {'position': position})

def delete_position(request, pk):
    position = get_object_or_404(Position, pk=pk)
    title = position.title
    position.delete()
    messages.warning(request, f"Position '{title}' deleted.")
    return redirect('dashboard:manage_positions')


# ================= CANDIDATES =================

def edit_candidate(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    positions = Position.objects.all()
    
    if request.method == "POST":
        candidate.name = request.POST.get('name')
        candidate.bio = request.POST.get('bio')
        # ADD THIS LINE BELOW
        candidate.manifesto = request.POST.get('manifesto') 
        
        pos_id = request.POST.get('position')
        candidate.position = get_object_or_404(Position, id=pos_id)
        
        if request.FILES.get('photo'):
            candidate.photo = request.FILES.get('photo')
            
        candidate.save()
        messages.success(request, f"Candidate {candidate.name} updated.")
        return redirect('dashboard:manage_candidates')
        
    return render(request, 'edit_candidate.html', {
        'candidate': candidate,
        'positions': positions
    })


@staff_member_required
def manage_elections(request):
    elections = Election.objects.all().order_by('-created_at')
    if request.method == "POST":
        form = ElectionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "New election created successfully.")
            return redirect('dashboard:manage_elections')
    else:
        form = ElectionForm()
    
    return render(request, 'manage_elections.html', {
        'elections': elections,
        'form': form
    })

@staff_member_required
def edit_election(request, pk):
    election = get_object_or_404(Election, pk=pk)
    
    if request.method == "POST":
        # Pass the POST data and the existing election to the form
        form = ElectionForm(request.POST, instance=election)
        
        if form.is_valid():
            # .save() converts the 'str' from the browser into 'datetime' objects
            election = form.save() 
            
            # Now election.status will work because start_date is a datetime object
            messages.success(request, f"Election '{election.title}' updated. It is now {election.status}.")
            return redirect('dashboard:manage_elections')
        else:
            messages.error(request, "Please correct the errors in the timing.")
    else:
        form = ElectionForm(instance=election)
    
    return render(request, 'edit_election.html', {
        'form': form, 
        'election': election
    })


from django.http import JsonResponse
from voter.models import Position

def get_positions_ajax(request):
    election_id = request.GET.get('election_id')
    positions = Position.objects.filter(election_id=election_id).values('id', 'title')
    return JsonResponse(list(positions), safe=False)


from django.db.models import Count
from voter.models import Election, Position, Candidate, AnonymousBallot

@staff_member_required
def election_results(request):
    elections = Election.objects.all().order_by('-start_date')
    total_students = Student_list.objects.count()
    
    results_data = []
    for election in elections:
        pos_list = []
        for pos in election.positions.all():
            candidates = Candidate.objects.filter(position=pos).annotate(
                vote_count=Count('anonymousballot')
            ).order_by('-vote_count')

            # Admin Detail: How many people actually finished voting for this position?
            participation_count = ParticipationLedger.objects.filter(position=pos).count()
            winner = candidates.first() if candidates.exists() and candidates.first().vote_count > 0 else None

            pos_list.append({
                'position': pos,
                'candidates': candidates,
                'turnout': participation_count,
                'winner': winner
            })

        results_data.append({
            'election': election,
            'positions': pos_list
        })

    return render(request, 'admin_results.html', {
        'results_data': results_data,
        'total_students': total_students
    })