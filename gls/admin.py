from django.contrib import admin
from .models import cerimonia, Workspace, Token, Colaborador
# Register your models here.

@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ['id', 'active', 'nome', 'grupo', 'user']

@admin.register(Colaborador)
class ColaboradorAdmin(admin.ModelAdmin):
    list_display = ['id', 'email', 'workspace', 'convite','active']

@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ['id','nome','token', 'user', 'url', 'versao','avatar']

@admin.register(cerimonia)
class cerimoniaAdmin(admin.ModelAdmin):
    list_display = ['id', 'active', 'workspace', 'dataInicio', 'dataFim', 'presentes', 'tipo','user']


