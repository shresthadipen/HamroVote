from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction

from accounts.forms import StudentRegisterForm
from accounts.models import Student_list, Voter


# ================= REGISTER =================
def student_register(request):
    if request.method == "POST":
        form = StudentRegisterForm(request.POST)

        if form.is_valid():
            # 1. STRIP WHITESPACE to prevent "Not Found" errors
            reg_no = form.cleaned_data["registration_number"].strip()
            name = form.cleaned_data["full_name"].strip()
            phone = form.cleaned_data["phone"].strip()
            email = form.cleaned_data["email"].strip()
            password = form.cleaned_data["password1"]

            # 2. Check student list (Using strip and iexact)
            student = Student_list.objects.filter(
                registration_number__iexact=reg_no
            ).first()

            if not student:
                messages.error(request, f"Registration number '{reg_no}' not found in the authorized list.")
                return render(request, "register.html", {"form": form})

            if student.is_registered:
                messages.error(request, "This registration number has already created an account.")
                return render(request, "register.html", {"form": form})

            # Check User duplicates
            if User.objects.filter(username=reg_no).exists():
                messages.error(request, "A user with this registration number already exists.")
                return render(request, "register.html", {"form": form})

            try:
                with transaction.atomic():
                    # Create User
                    user = User.objects.create_user(
                        username=reg_no,
                        email=email,
                        password=password,
                        first_name=name.split()[0],
                        last_name=" ".join(name.split()[1:]) if " " in name else ""
                    )

                    # Create Voter Profile
                    Voter.objects.create(
                        user=user,
                        student=student,
                        phone=phone,
                        email=email
                    )

                    # Mark student as registered
                    student.is_registered = True
                    student.save()

                # 3. FIX THE REDIRECT
                # Since we call login(), redirect them straight to the Voter Dashboard
                login(request, user)
                messages.success(request, "Account created successfully! Welcome to the Voting Booth.")
                return redirect("voter:voter_dashboard")

            except Exception as e:
                messages.error(request, f"Database Error: {e}")
        else:
            # If form is invalid, show specific errors in console for debugging
            print(form.errors)
            messages.error(request, "Please correct the errors below.")

    else:
        form = StudentRegisterForm()

    # 4. TEMPLATE PATH: Ensure you use accounts/register.html
    return render(request, "register.html", {"form": form})


# ================= LOGIN =================
def login_view(request):
    # If user is already logged in, redirect to appropriate dashboard
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect("dashboard:admin_dashboard")
        return redirect("voter:voter_dashboard")

    if request.method == "POST":
        identifier = request.POST.get("username")
        password = request.POST.get("password")

        user = None

        # login by email
        if "@" in identifier:
            try:
                u = User.objects.get(email=identifier)
                user = authenticate(request, username=u.username, password=password)
            except User.DoesNotExist:
                pass
        else:
            user = authenticate(
                request,
                username=identifier.strip(),
                password=password
            )

        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            
            if user.is_staff or user.is_superuser:
                return redirect("dashboard:admin_dashboard")
            return redirect("voter:voter_dashboard")

        messages.error(request, "Invalid credentials")

    return render(request, "login.html")


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully")
    return redirect("voter:landing")
