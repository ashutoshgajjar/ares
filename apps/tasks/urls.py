from django.urls import path
from .views import TaskDetailView, TaskListCreateView

urlpatterns = [
    path("tasks/", TaskListCreateView.as_view(), name="task_list_create"),
    path("tasks/<uuid:pk>/", TaskDetailView.as_view(), name="task_detail"),
]
