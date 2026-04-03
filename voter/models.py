from django.db import models
from accounts.models import Voter
from django.utils import timezone
 
class Election(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def is_running(self):
        now = timezone.now()
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

    class Meta:
        ordering = ['-start_date']

class Position(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='positions')
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.title} ({self.election.title})"

    class Meta:
        ordering = ['order']

class Candidate(models.Model):
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='candidates')
    name = models.CharField(max_length=100)
    bio = models.TextField()
    manifesto = models.TextField()
    photo = models.ImageField(upload_to='candidates/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.position.title}"

# ================= THE PRIVACY ALGORITHM MODELS =================

class ParticipationLedger(models.Model):
    # Using the 'app_name.ModelName' string avoids NameErrors and Circular Imports
    voter = models.ForeignKey('accounts.Voter', on_delete=models.CASCADE) 
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['voter', 'position']

class AnonymousBallot(models.Model):
    """
    ALGORITHM PART 2: The 'Secret Ballot'.
    This table records the CHOICE made.
    It links only to the Position and Candidate.
    IT HAS NO LINK TO THE VOTER. It is mathematically anonymous.
    """
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    voted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Secret vote for {self.candidate.name}"