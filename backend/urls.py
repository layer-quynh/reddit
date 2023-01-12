from django.urls import path

from backend import views

urlpatterns = [
    path('posts', views.PostsView.as_view()),
    path('posts/<int:post_id>', views.PostView.as_view()),
    path('posts/<int:post_id>/comments', views.CommentsView.as_view()),
    path('posts/<int:post_id>/comments/<int:comment_id>', views.NestedCommentsView.as_view()),
]
