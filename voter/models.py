# voter/models.py
from django.db import models
from django.utils import timezone
from accounts.models import Voter  # Import Voter from accounts

class Election(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    # --- THE TIME LOGIC ---
    @property
    def is_running(self):
        now = timezone.now()
        # Election is running ONLY if: Start < Now < End AND is_active is True
        return self.start_date <= now <= self.end_date and self.is_active

    @property
    def status(self):
        now = timezone.now()
        if not self.is_active:
            return "Disabled"
        if now < self.start_date:
            return "Upcoming"
        elif now > self.end_date:
            return "Closed"
        return "Running"

class Position(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='positions')
    title = models.CharField(max_length=100)  # e.g., "School Captain", "Vice Captain"
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)  # For ordering positions

    def __str__(self):
        return f"{self.title}"

    class Meta:
        ordering = ['order']

class Candidate(models.Model):
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='candidates')
    name = models.CharField(max_length=100)
    bio = models.TextField()
    manifesto = models.TextField()
    photo = models.ImageField(upload_to='candidates/', blank=True, null=True)
    grade = models.CharField(max_length=10, blank=True)
    section = models.CharField(max_length=5, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.position.title}"

    class Meta:
        ordering = ['name']

class Vote(models.Model):
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE, related_name='votes')  # Using Voter from accounts
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='votes')
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['voter', 'election', 'position']  # One vote per position per voter
        ordering = ['-voted_at']

    def __str__(self):
        return f"{self.voter.student.full_name} voted for {self.candidate.name}"
    

# voter/models.py

class AuthorizedVoter(models.Model):
    # This links an election to a registration number
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='authorized_list')
    registration_number = models.CharField(max_length=50)
    full_name = models.CharField(max_length=100)

    class Meta:
        # Prevents adding the same student twice to the same election
        unique_together = ['election', 'registration_number']

    def __str__(self):
        return f"{self.registration_number} for {self.election.title}"