from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("n/login", views.login_view, name="login"),
    path("n/logout", views.logout_view, name="logout"),
    path("n/register", views.register, name="register"),
    path("<str:username>", views.profile, name="profile"),
    path("n/following", views.following, name="following"),
    path("n/saved", views.saved, name="saved"),
    path("n/createpost", views.create_post, name="createpost"),
    path("n/post/<int:id>/like", views.like_post, name="likepost"),
    path("n/post/<int:id>/unlike", views.unlike_post, name="unlikepost"),
    path("n/post/<int:id>/save", views.save_post, name="savepost"),
    path("n/post/<int:id>/unsave", views.unsave_post, name="unsavepost"),
    path("n/post/<int:post_id>/comments", views.comment, name="comments"),
    path("n/post/<int:post_id>/write_comment", views.comment, name="writecomment"),
    path("n/post/<int:post_id>/delete", views.delete_post, name="deletepost"),
    path("<str:username>/follow", views.follow, name="followuser"),
    path("<str:username>/toggle_follow", views.toggle_follow, name="toggle_follow"),
    path("<str:username>/unfollow", views.unfollow, name="unfollowuser"),
    path("n/post/<int:post_id>/write_comment_django", views.write_comment_view, name="writecomment_django"),
    path('n/post/<int:post_id>/toggle_like', views.toggle_like, name='toggle_like'),
    path("n/edit_profile", views.edit_profile, name="edit_profile"),
    path('search/', views.search_users, name='search_users'),
    path('premium/', views.premium_subscription, name='premium_subscription'),
    path('premium/success/', views.premium_success, name='premium_success'),
    
    # Password Reset URLs using Django's auth views
    path('n/password_reset/', auth_views.PasswordResetView.as_view(
        template_name='network/password_reset.html',
        email_template_name='network/password_reset_email.html',
        success_url='/n/password_reset/done/'
    ), name='password_reset'),
    
    path('n/password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='network/password_reset_done.html'
    ), name='password_reset_done'),
    
    path('n/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='network/password_reset_confirm.html',
        success_url='/n/reset/complete/'
    ), name='password_reset_confirm'),
    
    path('n/reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='network/password_reset_complete.html'
    ), name='password_reset_complete'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
