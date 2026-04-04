from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'dashboard'

urlpatterns = [
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('students/', views.manage_students, name='manage_students'),
     path('positions/', views.manage_positions, name='manage_positions'),
        path('positions/edit/<int:pk>/', views.edit_position, name='edit_position'),
    path('positions/delete/<int:pk>/', views.delete_position, name='delete_position'),
    
    # Candidate Edit
    path('candidates/', views.manage_candidates, name='manage_candidates'),
    path('candidates/delete/<int:candidate_id>/', views.delete_candidate, name='delete_candidate'),
    path('candidates/edit/<int:pk>/', views.edit_candidate, name='edit_candidate'),

    path('elections/', views.manage_elections, name='manage_elections'),
path('elections/edit/<int:pk>/', views.edit_election, name='edit_election'),
path('ajax/get-positions/', views.get_positions_ajax, name='get_positions_ajax'),
 path('election-results/', views.election_results, name='admin_results'),
 path('elections/delete/<int:pk>/', views.delete_election, name='delete_election'),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)