from django.db import models

class Empresa(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre

class Departamento(models.Model):
    nombre = models.CharField(max_length=255)
    
    def __str__(self):
        return self.nombre

class Empleado(models.Model):
    codigo = models.CharField(max_length=100, null=True, blank=True)
    nombres = models.CharField(max_length=255)
    empresa = models.CharField(max_length=255)
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE)
    fecha=models.DateField()
    cant_marcaciones=models.CharField(max_length=2)
    hora = models.CharField(max_length=100)  # Puedes cambiarlo por otro tipo de campo si manejas horarios estructurados
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombres
    

class Horario(models.Model):
  departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, null=False)
  hora_inicio = models.CharField(max_length=100)
  hora_fin = models.CharField(max_length=100)