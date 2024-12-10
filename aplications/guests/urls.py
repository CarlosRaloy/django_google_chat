from django.urls import path
from aplications.guests import views

urlpatterns = [

    path(
        route='',
        view=views.feed_view,
        name='feed'
    ),

    path(
        route='add_user/',
        view=views.add_user,
        name='add_user'
    ),

    path(
        route='edit_user/<int:user_id>/',
        view=views.edit_user,
        name='edit_user'
    ),

    path(
        route='delete_user/<int:user_id>/',
        view=views.delete_user,
        name='delete_user'
    ),

    path(
        route='send_message/',
        view=views.send_message,
        name='send_message'
    ),

    path(
        route='start_oauth/',
        view=views.start_oauth,
        name='start_oauth'
    ),

    path(
        route='oauth_callback/',
        view=views.oauth_callback,
        name='oauth_callback'
    ),

]
