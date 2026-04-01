# voter/admin.py
from django.contrib import admin
from .models import Vote, Candidate, Position, Election

class VoteAdmin(admin.ModelAdmin):
    # We DO NOT include 'voter' here to maintain privacy
    list_display = ('election', 'position', 'candidate', 'voted_at')
    list_filter = ('election', 'position')
    
    # Make it read-only so admin can't change votes
    readonly_fields = ('voter', 'election', 'position', 'candidate', 'voted_at')

    def has_add_permission(self, request): return False

admin.site.register(Vote, VoteAdmin)
admin.site.register(Candidate)
admin.site.register(Position)
admin.site.register(Election)