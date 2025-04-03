from django.urls import path
from .views import *

urlpatterns = [
    path("subir/index", index_subir, name="app_index_subir"),
    path("index/procesar", index_procesar, name="app_index_procesar"),
    path("subir/archivo", upload_excel, name="app_procesar_subir_archivo"),
    path("listar/procesar", listar_marcaciones, name="app_listar_marcaciones"),
    path("calcular/tardanzas", calcular_tardanzas, name="app_calcular_tardanzas"),
    
    

]


