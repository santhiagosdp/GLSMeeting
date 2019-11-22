#from django.conf import settings
from django.db import models
#from django.utils import timezone
from django.contrib.auth.models import User


class Workspace(models.Model):
    nome = models.CharField(max_length=100)
    grupo = models.IntegerField()
    active = models.BooleanField(default=True)
    user = models.ForeignKey(User, null = True, on_delete=models.SET_NULL)

    class Meta:
        db_table = 'Workspaces'

class Colaborador(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    convite = models.ForeignKey(User,null = True, on_delete=models.SET_NULL)
    email = models.EmailField(max_length=100)
    active = models.BooleanField(default=False) #Desativar e ativar quando ele aceitar

    class Meta:
        db_table = 'Colaboradores'

class Token(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    url = models.CharField(max_length=100)
    versao= models.IntegerField()
    token = models.CharField(max_length=100)
    avatar = models.URLField(max_length=100)
    active = models.BooleanField(default=True)


    class Meta:
        db_table = 'Tokens'

class cerimonia(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=100)
    dataInicio = models.CharField(max_length=100)
    dataFim = models.CharField(max_length=100)
    presentes = models.TextField()
    projeto = models.CharField(max_length=100)
    assuntos = models.TextField()
    active = models.BooleanField(default=True)  # ativar e desativar
    user = models.ForeignKey(User,  null = True, on_delete=models.SET_NULL)

    class Meta:
        db_table = 'cerimonia'