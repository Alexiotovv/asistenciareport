from django.http import JsonResponse
import pandas as pd
from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from empleados.models import Empleado, Departamento, Horario
import datetime
from datetime import datetime, timedelta
from django.db.models import Min, Max
from collections import defaultdict
from datetime import datetime, timedelta

def index_subir(request):
    return render(request, 'procesar/index_subir.html', {
            'total_registros':0,
            'total_marcaciones':0,
            'total_guardados':0,
            'total_duplicados':0})


def upload_excel(request):
    
    if request.method == "POST" and request.FILES.get("excel_file"):
        excel_file = request.FILES["excel_file"]
        total_registros=0
        total_marcaciones=0
        total_guardados=0
        total_duplicados=0
        # Guardar el archivo temporalmente
        fs = FileSystemStorage()
        filename = fs.save(excel_file.name, excel_file)
        file_path = fs.path(filename)
        
        # Leer el archivo con pandas
        # try:
        df = pd.read_excel(file_path)
        df.columns=['codigo', 'nombres','empresa','departamento','fecha','cant_marcaciones','hora']
        total_registros=df.shape[0]
        df['hora'] = df['hora'].str.split(',')
        # Paso 2: Crear una fila por cada hora
        df = df.explode('hora')
        # Paso 3: Resetear el índice (opcional)
        df = df.reset_index(drop=True)
        df['fecha'] = pd.to_datetime(df['fecha'], format="%d/%m/%Y")
        total_marcaciones=df.shape[0]
        
        for _, row in df.iterrows():
            # Encontrando id de la empresa
            
            departamento = Departamento.objects.filter(nombre=row['departamento']).first()
        
            if not departamento:
                departamento = Departamento(nombre=row['departamento'])
                departamento.save()

            existe = Empleado.objects.filter(
                    codigo=row['codigo'],
                    fecha=row['fecha'],
                    hora=row['hora'],
                    departamento_id=departamento.id
                ).exists()
            total_guardados+=1
            if not existe:  
                empleado = Empleado(
                    codigo=row['codigo'],
                    nombres=row['nombres'],
                    empresa=row['empresa'],
                    departamento_id=departamento.id,
                    fecha = row['fecha'],  # Convertir fecha
                    cant_marcaciones=row['cant_marcaciones'],
                    hora=row['hora']
                )
                empleado.save()


        # except Exception as e:
        #     print(f"Error al leer el archivo: {e}")
        
        # Opcional: Eliminar el archivo después de procesarlo
        fs.delete(filename)
        total_duplicados=total_marcaciones-total_guardados
        return render(request, "procesar/index_subir.html",{
            'total_registros':total_registros,
            'total_marcaciones':total_marcaciones,
            'total_guardados':total_guardados,
            'total_duplicados':total_duplicados})
    

def index_procesar(request):
    return render(request,"procesar/index_procesar.html")

def listar_marcaciones(request):
    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_final = request.GET.get("fecha_final")

    if fecha_inicio and fecha_final:
        empleados = Empleado.objects.filter(fecha__range=[fecha_inicio, fecha_final])
    else:
        empleados = Empleado.objects.all()

    empleados_data = list(empleados.values(
        "id", 
        "nombres", 
        "codigo", 
        "empresa", 
        "hora",
        "departamento__nombre",
        "cant_marcaciones",
        "fecha")
        )  # Ajusta los campos según tu modelo
    
    
    return JsonResponse({"data": empleados_data})

def calcular_tardanzas(request):
    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_final = request.GET.get("fecha_final")

    if not fecha_inicio or not fecha_final:
        return JsonResponse({"error": "Debes seleccionar un rango de fechas."}, status=400)

    empleados = Empleado.objects.filter(fecha__range=[fecha_inicio, fecha_final]).order_by("codigo", "fecha", "hora")
        
    estado=True
    hora_entrada=""
    hora_salida=""
    fecha_entrada=""
    fecha_salida=""
    codigo_actual = None
    data=[]
    for e in empleados:
        if codigo_actual != e.codigo:
            codigo_actual = e.codigo
            if estado==False:
                fecha_salida="No hay fecha"
                hora_entrada="No hay marcación"
            estado = True  # La siguien

        if estado:
           hora_entrada=e.hora
           fecha_entrada=e.fecha
           estado=False
        else:
            hora_salida=e.hora
            fecha_salida=e.fecha
            estado=True
        
            tardanza_minutos, salida_temprano_minutos, total_minutos_deuda = calcular_minutos(hora_entrada, hora_salida, e.departamento_id)

            data.append({
                "codigo": e.codigo,
                "nombres": e.nombres,
                "departamento": e.departamento.nombre if e.departamento else "Sin asignar",
                "fecha_entrada": fecha_entrada,
                "hora_entrada": hora_entrada,
                "fecha_salida": fecha_salida,
                "hora_salida": hora_salida,
                "tardanza_minutos":tardanza_minutos,
                "salida_temprano_minutos": salida_temprano_minutos,
                "total_minutos_deuda": total_minutos_deuda

            })
        
        #llamar a la función para encontrar los minutos de tardanza
            
    return JsonResponse({"data": data})
     



def calcular_minutos(hora_entrada, hora_salida, departamento_id):
    formato = "%H:%M:%S"

    # Obtener los horarios del departamento
    horarios = Horario.objects.filter(departamento_id=departamento_id)

    if not horarios.exists():
        return 0, 0, 0  # Si no hay horarios, no hay tardanzas ni salidas tempranas

    # Convertimos las horas de entrada y salida a objetos datetime
    hora_entrada_real = datetime.strptime(hora_entrada, formato)
    hora_salida_real = datetime.strptime(hora_salida, formato)

    # Determinar el horario más cercano
    horario_mas_cercano = None
    menor_diferencia = float('inf')

    for horario in horarios:
        hora_inicio = datetime.strptime(horario.hora_inicio, formato)
        diferencia = abs((hora_entrada_real - hora_inicio).total_seconds())

        if diferencia < menor_diferencia:
            menor_diferencia = diferencia
            horario_mas_cercano = horario

    if not horario_mas_cercano:
        return 0, 0, 0  # Seguridad, en caso no se encuentre horario

    # Usar el horario encontrado
    hora_entrada_esperada = datetime.strptime(horario_mas_cercano.hora_inicio, formato)
    hora_salida_esperada = datetime.strptime(horario_mas_cercano.hora_fin, formato)

    # Cálculo de tardanza en minutos
    tardanza_minutos = max(0, (hora_entrada_real - hora_entrada_esperada).total_seconds() // 60)

    # Cálculo de salida temprana en minutos
    salida_temprano_minutos = max(0, (hora_salida_esperada - hora_salida_real).total_seconds() // 60)

    # Total de minutos de deuda
    total_minutos_deuda = tardanza_minutos + salida_temprano_minutos

    return int(tardanza_minutos), int(salida_temprano_minutos), int(total_minutos_deuda)


    # # Diccionario para agrupar las marcaciones por empleado
    # registros = defaultdict(list)

    # for empleado in empleados:
    #     clave = (empleado.codigo, empleado.fecha)
    #     registros[clave].append(empleado.hora)  # Guardamos todas las marcaciones del día

    # data = []
    
    # for (codigo, fecha), marcaciones in registros.items():
    #     empleado = Empleado.objects.filter(codigo=codigo, fecha=fecha).first()
    #     horarios = Horario.objects.filter(departamento=empleado.departamento).order_by("hora_inicio")

    #     if not horarios:
    #         continue  # Si no hay horarios asociados, se omite

    #     # Convertimos horarios a datetime para comparar
    #     horarios_disponibles = []
    #     for h in horarios:
    #         horarios_disponibles.append(datetime.strptime(str(h.hora_inicio), "%H:%M:%S"))
        
    #     # Ordenamos las marcaciones del día
    #     marcaciones.sort()
    #     registros_entrada_salida = []
        
    #     for marcacion in marcaciones:
    #         hora_marcacion = datetime.strptime(marcacion, "%H:%M:%S")
            
    #         # Encontrar el horario más cercano
    #         horario_cercano = min(horarios_disponibles, key=lambda h: abs((hora_marcacion - h).total_seconds()))
    #         diferencia = (hora_marcacion - horario_cercano).total_seconds()

    #         if diferencia <= 0:  # Antes o en punto => ENTRADA
    #             registros_entrada_salida.append((hora_marcacion, None))
    #         else:  # Después del horario => SALIDA
    #             if registros_entrada_salida and registros_entrada_salida[-1][1] is None:
    #                 registros_entrada_salida[-1] = (registros_entrada_salida[-1][0], hora_marcacion)
    #             else:
    #                 registros_entrada_salida.append((hora_marcacion, None))

    #     # Si la última entrada no tiene salida, asumimos 8 horas después
    #     if registros_entrada_salida and registros_entrada_salida[-1][1] is None:
    #         registros_entrada_salida[-1] = (registros_entrada_salida[-1][0], registros_entrada_salida[-1][0] + timedelta(hours=8))

    #     # Primera entrada y última salida
    #     hora_entrada = registros_entrada_salida[0][0]
    #     hora_salida = registros_entrada_salida[-1][1]

    #     # Encontrar el horario real al que pertenece la entrada
    #     horario_real = min(horarios, key=lambda h: abs((hora_entrada - datetime.strptime(str(h.hora_inicio), "%H:%M:%S")).total_seconds()))

    #     hora_inicio = datetime.strptime(str(horario_real.hora_inicio), "%H:%M:%S")
    #     hora_fin = datetime.strptime(str(horario_real.hora_fin), "%H:%M:%S")

    #     # Cálculo de tardanza
    #     tardanza_minutos = max((hora_entrada - hora_inicio).total_seconds() / 60, 0)

    #     # Cálculo de salida temprano
    #     salida_temprano_minutos = max((hora_fin - hora_salida).total_seconds() / 60, 0)

    #     # Total de minutos de deuda
    #     total_minutos_deuda = tardanza_minutos + salida_temprano_minutos

    #     data.append({
    #         "codigo": empleado.codigo,
    #         "nombres": empleado.nombres,
    #         "departamento": empleado.departamento.nombre if empleado.departamento else "Sin asignar",
    #         "fecha": fecha.strftime("%Y-%m-%d"),
    #         "hora_entrada": hora_entrada.strftime("%H:%M:%S"),
    #         "hora_salida": hora_salida.strftime("%H:%M:%S"),
    #         "tardanza_minutos": int(tardanza_minutos),
    #         "salida_temprano_minutos": int(salida_temprano_minutos),
    #         "total_minutos_deuda": int(total_minutos_deuda)
    #     })

    # return JsonResponse({"data": ''})