from django.urls import path
from .views import *

urlpatterns = [
    path("empleados/", index_empleados, name="app_index_empleados"),
    path("agregar/empleado/", agregar_empleado, name="agregar_empleado"),
    path("actualizar/empleado/", actualizar_empleado, name="actualizar_empleado"),

    path("horarios/index", index_horarios, name="app_index_horarios"),
    path("horarios/store", store_horarios, name="app_store_horarios"),
    path("horarios/delete", delete_horarios, name="app_delete_horarios"),
    path("horarios/edit/<int:id>", edit_horarios, name="app_edit_horarios"),
    path("horarios/update", update_horarios, name="app_update_horarios"),


]


