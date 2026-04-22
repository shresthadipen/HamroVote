from django.db import models
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
        if not self.is_active: return "Disabled"
        if now < self.start_date: return "Upcoming"
        elif now > self.end_date: return "Closed"
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

# ================= THE CRYPTOGRAPHIC ALGORITHM MODELS =================

class ParticipationLedger(models.Model):
    """
    ALGORITHM PART 1: The Cryptographic Identity Ledger.
    We store a unique SHA-256 hash instead of a student name.
    """
    # unique=True prevents double voting
    voter_hash = models.CharField(max_length=64, unique=True) 
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    voted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Encrypted participation for {self.position.title}"

class AnonymousBallot(models.Model):
    """
    ALGORITHM PART 2: The Decoupled Ballot Box.
    Records the choice. NO Voter ID or Hash is stored here.
    """
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    voted_at = models.DateTimeField(auto_now_add=True)