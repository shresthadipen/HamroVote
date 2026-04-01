import csv, io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count

from accounts.models import Student_list, Voter
from voter.models import Election, Position, Candidate, Vote

# ================= 1. ANALYTICS (Home) =================
@staff_member_required
def admin_dashboard(request):
    # Analytics Stats
    total_students = Student_list.objects.count()
    registered_voters = Voter.objects.count()
    total_votes = Vote.objects.count()
    
    # Calculate Turnout %
    turnout = round((total_votes / registered_voters * 100), 1) if registered_voters > 0 else 0

    # Privacy Algorithm: Get vote counts per position without voter names
    positions = Position.objects.annotate(v_count=Count('vote'))
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
    students = Student_list.objects.all().order_by('-id')
    
    if request.method == "POST":
        # Manual Add
        if 'manual_add' in request.POST:
            reg_no = request.POST.get('registration_number')
            name = request.POST.get('full_name')
            Student_list.objects.get_or_create(registration_number=reg_no, defaults={'full_name': name})
            messages.success(request, f"Student {name} added.")
        
        # Bulk CSV Upload
        elif 'bulk_upload' in request.POST:
            csv_file = request.FILES.get('file')
            if csv_file and csv_file.name.endswith('.csv'):
                data_set = csv_file.read().decode('UTF-8')
                io_string = io.StringIO(data_set)
                next(io_string) # Skip header
                for row in csv.reader(io_string, delimiter=','):
                    if len(row) >= 2:
                        Student_list.objects.get_or_create(
                            registration_number=row[0].strip(),
                            defaults={'full_name': row[1].strip()}
                        )
                messages.success(request, "Bulk import completed.")
            else:
                messages.error(request, "Please upload a valid CSV file.")
        
        return redirect('dashboard:manage_students')

    return render(request, 'manage_students.html', {'students': students})


# ================= 3. POSITION MANAGEMENT =================
@staff_member_required
def manage_positions(request):
    # Fetch existing election (create one if none exists)
    election, created = Election.objects.get_or_create(
        is_active=True, 
        defaults={'title': 'Current Election', 'start_date': '2024-01-01 00:00', 'end_date': '2025-01-01 00:00'}
    )
    positions = Position.objects.filter(election=election)

    if request.method == "POST" and 'add_position' in request.POST:
        title = request.POST.get('title')
        desc = request.POST.get('description')
        Position.objects.create(election=election, title=title, description=desc)
        messages.success(request, f"Position '{title}' created.")
        return redirect('dashboard:manage_positions')

    return render(request, 'manage_positions.html', {'positions': positions})


# ================= 4. CANDIDATE MANAGEMENT =================
@staff_member_required
def manage_candidates(request):
    candidates = Candidate.objects.all().order_by('-created_at')
    positions = Position.objects.all()

    if request.method == "POST" and 'add_candidate' in request.POST:
        pos_id = request.POST.get('position')
        name = request.POST.get('name')
        bio = request.POST.get('bio')
        photo = request.FILES.get('photo')

        position = get_object_or_404(Position, id=pos_id)
        Candidate.objects.create(
            position=position,
            name=name,
            bio=bio,
            photo=photo
        )
        messages.success(request, f"Candidate {name} registered.")
        return redirect('dashboard:manage_candidates')

    return render(request, 'manage_candidates.html', {
        'candidates': candidates,
        'positions': positions
    })

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