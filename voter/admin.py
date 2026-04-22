from django.contrib import admin
from .models import Election, Position, Candidate, ParticipationLedger, AnonymousBallot

# 1. Standard Registrations
admin.site.register(Election)
admin.site.register(Position)
admin.site.register(Candidate)

# 2. Participation Ledger (Admin can see WHO voted)
@admin.register(ParticipationLedger)
class ParticipationLedgerAdmin(admin.ModelAdmin):
    # Change 'voter' to 'voter_hash'
    list_display = ('voter_hash', 'position', 'voted_at') 
    list_filter = ('position',)
    # Remove search_fields that refer to the old voter model
    search_fields = ('voter_hash',)
    
# 3. Anonymous Ballots (Admin can see the CHOICES, but they are anonymous)
@admin.register(AnonymousBallot)
class AnonymousBallotAdmin(admin.ModelAdmin):
    list_display = ('election', 'position', 'candidate', 'voted_at')
    list_filter = ('election', 'position', 'candidate')
    
    # Security: Make these records read-only in the admin panel 
    # so no one can tamper with the results.
    readonly_fields = ('election', 'position', 'candidate', 'voted_at')

    def has_add_permission(self, request): return False