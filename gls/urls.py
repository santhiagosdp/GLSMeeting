from django.contrib.staticfiles.templatetags.staticfiles import static
from django.urls import path
from django.contrib import admin
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('', RedirectView.as_view(url="/ws") ),

    #LOGIN e LOGOUT
    path('login/', views.login_user),
    path('login/submit', views.submit_login),
    path('logout/', views.logout_user),

    #OAUTH 
    path('oauth/redirect/', views.access_token),  #Retorna access_token
    path('autenticar/', views.autenticar),  #Retorna Dados Usuários

    #Workspaces
    path('ws/', views.inicial), #mostrando generico
    path('ws/new', views.nova_workspace),
    path('ws/submit', views.submit_workspace),
    path('desabilitar_ws/<id>', views.desabilitar_workspace),
    path('ws/desabilitados', views.workspaces_desabilitadas), #mostrando Workspaces desabilitadas
    path('habilitar_ws/<id>', views.habilitar_workspace),

    path('ws/<id>', views.lista_atas), #mostrando de organizacao especifico
    path('delete_ata/<wid>/<aid>', views.deletar_ata), #wid = id workspace e aid= id ata

    path('new/<id>/planejamento', views.nova_planejamento), #nova Ata planejamento
    path('selecao/projeto/<id>/', views.seleciona_projeto), #Seleção projeto p diária
    path('new/<id>/diaria', views.nova_diaria), #nova Ata Diaria
    path('new/<id>/final', views.nova_final), #nova Ata Final
    path('new/<id>/cerimonia_save',views.submit_reuniao),

    #IMPRIMINDO ATAS
    path('print/<id>', views.imprimir_pdf),  #id da ata
    path('data/print', views.imprimir_pdf_data),  #imprimir atas do dia

    #EDITANDO PERFIL
    path('perfil', views.perfil),
    path('perfil/submit', views.submit_perfil),

    #INTEGRANTES CONVITE
    path('ws/<id>/new_integrante', views.novo_integrante),
    path('ws/<id>/new_integrante/submit', views.submit_integrante),
    path('delete_integrante/<idw>/<idi>', views.deletar_integrante),
    path('convite/', views.resposta_convite), 
    path('resposta_convite/<id>/', views.submit_convite), #integrante aceitar ou recusar


    path('erro_autorizacao/<mensagem>/', views.erro_autorizacao), #Mostrar erro de autorização



   
    
    ## TESTES
    path('brutoAPI/', views.brutoAPI),
    path('projetos/', views.projetos),
    path('select/', views.select),  # Excluir depois
]