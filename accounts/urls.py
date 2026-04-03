from django.urls import path
from accounts import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.student_register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
path("change-password/", views.change_password, name="change_password"),
path("profile/edit/", views.edit_profile, name="edit_profile"),
]
