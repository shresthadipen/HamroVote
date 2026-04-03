from django.urls import path
from . import views

app_name = 'voter'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.voter_dashboard, name='voter_dashboard'),
    path('candidates/<int:position_id>/', views.candidates, name='candidates'),
    path('candidate/<int:candidate_id>/', views.candidate_detail, name='candidate_detail'), # Match this
    path('vote/<int:candidate_id>/', views.vote_confirmation, name='vote'), # Match this
    path('results/', views.results, name='results'),
    path('ballot/<int:election_id>/', views.election_ballot, name='election_ballot'),
]