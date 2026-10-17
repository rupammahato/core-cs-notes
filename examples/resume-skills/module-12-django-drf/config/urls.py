from django.urls import path, include
from rest_framework.routers import DefaultRouter
from work.views import TaskViewSet, health, SessionProbe
router = DefaultRouter()
router.register('tasks', TaskViewSet, basename='task')
urlpatterns = [path('health/',health), path('api/',include(router.urls)),
               path('session-probe/',SessionProbe.as_view())]
