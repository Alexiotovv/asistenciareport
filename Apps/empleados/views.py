from django.shortcuts import render, redirect, get_object_or_404
from .models import Departamento, Empleado, Horario
from django.contrib import messages
from django.http import JsonResponse

def index_empleados(request):
    empleados=Empleado.objects.all()
    return render(request, 'empleados/index_empleados.html', {'empleados':empleados})


def agregar_empleado(request):
    if request.method == "POST":
        nombres = request.POST.get("nombres")
        codigo = request.POST.get("codigo")
        empresa = request.POST.get("empresa")
        departamento = request.POST.get("departamento")
        horario = request.POST.get("horario")

        if nombres and empresa and departamento and horario:
                Empleado.objects.create(
                    nombres=nombres,
                    codigo=codigo,
                    empresa=empresa,
                    departamento=departamento,
                    horario=horario
                )
                messages.success(request, "Empleado guardado correctamente.")
                return redirect("app_index_empleados")  # Redirige a la lista de empleados o donde desees
            
        else:
            messages.error(request, "Todos los campos son obligatorios.")


    return render(request, "empleados/formulario.html")



def actualizar_empleado(request):
    empleado_id = request.POST.get("empleado_id")
    empleado = get_object_or_404(Empleado, id=empleado_id)

    if request.method == "POST":
        nombres = request.POST.get("nombres_editar")
        codigo = request.POST.get("codigo_editar")
        empresa = request.POST.get("empresa_editar")
        departamento = request.POST.get("departamento_editar")
        horario = request.POST.get("horario_editar")
        
        if nombres and empresa and departamento and horario:
            empleado.nombres = nombres
            empleado.codigo = codigo
            empleado.empresa = empresa
            empleado.departamento = departamento
            empleado.horario = horario
            empleado.save()
            
            messages.success(request, "Empleado actualizado correctamente.")
            return redirect("app_index_empleados")  # Redirige a la lista de empleados
        
        else:
            messages.error(request, "Todos los campos son obligatorios.")

    return redirect("app_index_empleados")

def index_horarios(request):
    departamentos = Departamento.objects.all()
    horarios = Horario.objects.all()
    return render(request,'horarios/index_horarios.html',{
        'departamentos':departamentos,
        'horarios':horarios
    })

def store_horarios(request):
    
    if request.method=="POST":
    
        Horario.objects.create(
            hora_inicio=request.POST.get("hora_inicio"),
            hora_fin=request.POST.get("hora_fin"),
            departamento_id=request.POST.get("departamento_id")
        )
    
        return redirect("app_index_horarios")

def delete_horarios(request):
    if request.method=="POST":
        horario_id=request.POST.get("horario_id")
        registro=get_object_or_404(Horario, id=horario_id)
        registro.delete()
        return redirect("app_index_horarios")
    
def edit_horarios(request,id):
    horario = get_object_or_404(Horario, id=id)  # Busca el horario o devuelve error 404
    data = {
        "id": horario.id,
        "hora_inicio": horario.hora_inicio,
        "hora_fin": horario.hora_fin,
    }
    
    return JsonResponse(data)

def update_horarios(request):
    if request.method=="POST":
        horario_id=request.POST.get("edit_horario_id")
        horario = Horario.objects.get(id=horario_id)
        horario.hora_inicio=request.POST.get("edit_hora_inicio")
        horario.hora_fin=request.POST.get("edit_hora_fin")
        horario.save()
        return redirect("app_index_horarios")