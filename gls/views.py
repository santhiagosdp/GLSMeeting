##   IMPORTAÇÕES   ##

# configurações
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
import http.client
from django.conf import settings
import gitlab
import json
from datetime import datetime
# autenticação e usuarios
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
# renderizando e protegendo páginas e posts/get
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
import requests
from django.contrib import messages
# gerar pdf
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
# importando models.py
from .models import cerimonia, Workspace, Colaborador, User, Token


##   FUNÇÕES   ##


# PÁGINA ==> LOGIN
def login_user(request):
    return render(request, 'login.html')
        
# SUBMIT ==> LOGIN
@csrf_protect
def submit_login(request):
    if request.POST:
        #url = 'https://gitlab.com/oauth/authorize?client_id='+settings.APP_ID+'&redirect_uri='+settings.REDIRECT+'&response_type=code&state='+settings.APP_SECRET+'&scope=api+read_user'
        # Com code não consegui pegar os dados do Git.

        url = 'https://gitlab.com/oauth/authorize?client_id=' + settings.APP_ID + '&redirect_uri=' + \
            settings.REDIRECT + '&response_type=token&state=' + \
            settings.APP_SECRET + '&scopes=api+read_user'

        return redirect(url)

#PÁGINA ==> PEGANDO VAVOR DE ACESS_TOKEN COM CODIGO JS NO HTML
def access_token(request):
    state = settings.APP_SECRET
    return render(request, 'gls/access_token.html', {'state': state})

#from django.core.mail import send_mail
from django.core.mail import send_mail
# AÇÃO ==> AUTENTICAR
def autenticar(request):
    access_token = request.GET['access_token']
    url = 'https://gitlab.com/api/v4/user?access_token=' + access_token
    resp = requests.get(url)  # retorna os dados do usuário

# se status for "ok", pega os dados do usuário
    if resp.status_code == 200:
        #return HttpResponse(resp.content)
        perfil = json.loads(resp.text)
        #return HttpResponse(perfil['email'])
        nome_usuario = perfil['username']
        email = perfil['email']
        senha = str(perfil['id']) + email
        name = perfil['name']
        avatar = perfil['avatar_url']

# 1ª tentativa de autenticar
        user = authenticate(username=nome_usuario, password=senha)
        if user is not None:
            # se existir usuario no sistema, faz login e vai para pagina de perfil
            login(request, user)

            usuario = request.user
            token = Token.objects.get(user=usuario)
            if access_token != token.token:
                token.token = access_token
                token.save()
            return redirect('/ws')
        else:
            # se nao existir, cria usuario
            new_user = User.objects.create_user(
                first_name=name, username=nome_usuario, email=email, password=senha)
            new_user.save()
# 2ª tentativa de autenticar
            user = authenticate(username=nome_usuario, password=senha)
            if user is not None:
                # se existir usuario no sistema, faz login, cria token padrão e vai para página de perfil
                login(request, user)
                user = request.user
                new_token = Token.objects.create(user=user, nome=user.first_name, token=access_token, url=settings.GITLAB_LINK,
                                                 versao=settings.VERSAO, avatar=avatar)
                new_token.save()
                return redirect('/perfil')
# se ainda com erro, retorna mensagem pra tela de login
            else:
                messages.error(
                    request, 'Não logado,  tentar novamente, ou acionar a Administração')
                return redirect('/login/')
    else:
        messages.error(
            request, 'Não logado,  tentar novamente, ou acionar o Suporte')

# LOGOUT
def logout_user(request):
    logout(request)
    return redirect('/login/')

#EXTRA ==> RETORNA DADOS PARA MENU LATERAL
def dados_menu(email,info):
# INICIO - mostrar WS no menu lateral
    wsgeral = Workspace.objects.filter(active=True)
    user_colab = Colaborador.objects.filter(email=email)
    workspaces = []
    convite = []
    workspaces_pendentes = []
    for ws_user in user_colab:
        for ws in wsgeral:
            if ws_user.workspace == ws:
                if ws_user.active == False:
                    workspaces_pendentes.append(ws)
                else:
                    workspaces.append(ws)
    if len(workspaces_pendentes) > 0:
        convite.append('True')
# FIM - Mostrar WS no menu lateral
    if info == "convite":
        return convite
    if info == "workspaces":
        return workspaces
    if info == "user_colab":
        return user_colab
    if info == "workspaces_pendentes":
        return workspaces_pendentes

    else:
        return False

# PÁGINA ==> BASE.HTML INICIAL
@login_required(login_url='/login/')
def inicial(request):
    convite = dados_menu(request.user.email,"convite")
    workspaces = dados_menu(request.user.email,"workspaces")
    token = Token.objects.get(active=True, user=request.user)

    return render(request, 'gls/base.html', {'workspaces': workspaces, 'token': token, 'convite': convite})

# PÁGINA ==> PERFIL
@login_required(login_url='/login/')
def perfil(request):
    convite = dados_menu(request.user.email,"convite")
    workspaces = dados_menu(request.user.email,"workspaces")
    user = request.user
    token = Token.objects.get(active=True, user=user)

    return render(request, 'gls/perfil.html', {'workspaces': workspaces, 'user': user, 'token': token, 'convite': convite})

# AÇÃO ==> EDITAR PERFIL
@login_required(login_url='/login/')
def submit_perfil(request):
    if request.POST:
        nome = request.POST.get('nome')
        user = request.user
        alterar = Token.objects.get(user=user)
        alterar.nome = nome
        alterar.save()
        user.first_name = nome
        user.save()
    return redirect('/ws')


# PÁGINA ==> ADD WORKSPACE
@login_required(login_url='/login/')
def nova_workspace(request):
    convite = dados_menu(request.user.email,"convite")
    workspaces = dados_menu(request.user.email,"workspaces")

    token = Token.objects.get(user=request.user)
    # mudar gl para autenticar
    autenticar = gitlab.Gitlab(token.url, oauth_token=token.token)
    autenticar.auth()
    groups = autenticar.groups.list()
    return render(request, 'gls/new_workspaces.html', {'workspaces': workspaces, 'grupos': groups, 'token': token, 'convite': convite})


# AÇÃO ==> ADD WORKSPACE
@login_required(login_url='/login/')
def submit_workspace(request):
    if request.POST:
        nome = request.POST.get('nome')
        grupo_id = request.POST.get('grupo')
        # return HttpResponse(grupo_id)
        if nome=="":
            nome = "Workspace grupo: "+grupo_id
        user = request.user
        workspace = Workspace.objects.create(
            nome=nome, user=user, grupo=grupo_id)
        workspace.save()
        colab = Colaborador.objects.create(
            email=user.email, workspace=workspace, convite=user, active=True)
        colab.save()
        return redirect('/ws')
    return HttpResponse("Erro ao salvar workspace")


# PÁGINA ==> WORKSPACES DESABILITADAS
@login_required(login_url='/login/')
def workspaces_desabilitadas(request):
    convite = dados_menu(request.user.email,"convite")
    workspaces = dados_menu(request.user.email,"workspaces")
    user_colab = dados_menu(request.user.email,"user_colab")

    token = Token.objects.get(active=True, user=request.user)
    wsgeral_desab = Workspace.objects.filter(active=False)
    ws_desab = []
    for ws_user in user_colab:
        for ws in wsgeral_desab:
            if ws_user.workspace == ws:
                ws_desab.append(ws)
    return render(request, 'gls/ws_desabilitados.html',
                  {'workspaces': workspaces, 'ws_desab': ws_desab, 'token': token, 'convite': convite})


# AÇÃO ==> DESABILITAR WORKSPACE
@login_required(login_url='/login/')
def desabilitar_workspace(request, id):
    ehexcluir = request.GET['excluir']
    #return HttpResponse(ehexcluir)
    if ehexcluir =="sim":
        #return HttpResponse("ehexcluir")
        workspace = Workspace.objects.get(id=id)
        #return HttpResponse(workspace.id)
        workspace.delete()
        return redirect('/ws/desabilitados')
    else:
        workspace = Workspace.objects.get(active=True, id=id)
        workspace.active = False
        workspace.save()
        return redirect('/ws')


# AÇÃO ==> HABILITAR WORKSPACE
@login_required(login_url='/login/')
def habilitar_workspace(request, id):
    workspace = Workspace.objects.get(active=False, id=id)
    workspace.active = True
    workspace.save()
    return redirect('/ws/' + id)

# PÁGINA ==> LISTAR ATAS DO WORKSPACE
@login_required(login_url='/login/')
def lista_atas(request, id):
    convite = dados_menu(request.user.email,"convite")
    workspaces = dados_menu(request.user.email,"workspaces")

    token = Token.objects.get(active=True, user=request.user)
    atas = cerimonia.objects.filter(
        active=True, workspace=id).order_by('-dataInicio')
    team = Colaborador.objects.filter(active=True, workspace=id)
    colaboradores = []
    for p in team:
        todos = User.objects.all()
        for um in todos:
            if p.email == um.email:
                colaboradores.append(um)

    ws = Workspace.objects.get(active=True, id=id)
    autorization = False
    for colab in team:
        if colab.email == request.user.email:
            autorization = True
    if autorization == True:
        return render(request, 'gls/lista_atas.html',
                      {'atas': atas, 'team': colaboradores, 'ws': ws, 'workspaces': workspaces, 'id': id, 'token': token, 'convite': convite})
    else:
        #return HttpResponse('Usuario não autorizado para ver a ata')
        mensagem = 'Usuario não autorizado para ver Ata!'
        return redirect('/erro_autorizacao/'+mensagem)


# AÇÃO ==> DELETAR ATA
@login_required(login_url='/login/')
def deletar_ata(request, wid, aid):
    desativar = cerimonia.objects.get(
        active=True, id=aid)
    desativar.active = False
    desativar.save()
    return redirect('/ws/' + wid)

# PÁGINA ==> NOVO INTEGRANTE
@login_required(login_url='/login/')
def novo_integrante(request, id):
    convite = dados_menu(request.user.email,"convite")
    workspaces = dados_menu(request.user.email,"workspaces")

    token = Token.objects.get(active=True, user=request.user)
    return render(request, 'gls/integrante.html', {'workspaces': workspaces, 'id': id, 'token': token, 'convite': convite})

# AÇÃO ==> ADD CONVITE INTEGRANTE
@login_required(login_url='/login/')
def submit_integrante(request, id):
    if request.POST:
        email = request.POST.get('email')
        user = request.user
        workspace = Workspace.objects.get(active=True, id=id)
        colab = Colaborador.objects.filter(email=email, workspace=workspace)
        if len(colab) == 0:
            add = Colaborador.objects.create(
                email=email, workspace=workspace, convite=user)
            add.save()
        return redirect('/ws/' + id)


# AÇÃO ==> DELETAR INTEGRANTE
@login_required(login_url='/login/')
def deletar_integrante(request, idw, idi):
    workspace = Workspace.objects.get(active=True, id=idw)
    integrante = Colaborador.objects.get(
        active=True, email=idi, workspace=workspace)
    integrante.delete()
    if request.user.email == idi:
        return redirect('/ws')
    else:
        return redirect('/ws/' + idw)


# PÁGINA ==> INTEGRANTE ACEITAR/RECUSAR CONVITE
@login_required(login_url='/login/')
def resposta_convite(request):
    convite = dados_menu(request.user.email,"convite")
    workspaces = dados_menu(request.user.email,"workspaces")
    workspaces_pendentes = dados_menu(request.user.email, "workspaces_pendentes")

    token = Token.objects.get(active=True, user=request.user)
    return render(request, 'gls/convites.html', {'workspaces': workspaces, 'token': token, 'workspaces_pendentes': workspaces_pendentes, 'convite': convite})

# AÇÃO ==> ACEITAR OU DELETAR CONVITE
@login_required(login_url='/login/')
def submit_convite(request, id):
    convite = request.GET['resp']
    if convite == 'recusar':
        print(convite)
        workspace = Workspace.objects.get(id=id)
        convite = Colaborador.objects.get(
            workspace=workspace, email=request.user.email)
        convite.delete()

    if convite == "aceitar":
        # print(convite)
        workspace = Workspace.objects.get(id=id)
        convite = Colaborador.objects.get(
            workspace=workspace, email=request.user.email)
        convite.active = True
        convite.save()

    return redirect('/ws')


# AÇÃO ==>  RETORNA GRUPO ESPECIFICO
def grupo_gl(token, id_grupo):
    autenticar = gitlab.Gitlab(token.url, oauth_token=token.token)
    autenticar.auth()
    #verificar se usuario pertence ao grupo
    grupos = autenticar.groups.list()  # busca todos grupo do user
    
    grupo = autenticar.groups.get(id_grupo)  # busca grupo especifico
    return grupo

def autorizagrupo(token, id_grupo):
    autenticar = gitlab.Gitlab(token.url, oauth_token=token.token)
    autenticar.auth()
    grupos = autenticar.groups.list()  # busca todos grupo do user
    for g in grupos:
        if g.id == id_grupo:#VERIFICA SE USUARIO TA NO GRUPO
            return True 
    return False

#PAGINA ==> ERRO DE AUTORIZAÇÃO
def erro_autorizacao(request,mensagem):
    convite = dados_menu(request.user.email,"convite")
    workspaces = dados_menu(request.user.email,"workspaces")
    token = Token.objects.get(active=True, user=request.user)

    return render(request, 'gls/semAutorizacao.html',{'mensagem': mensagem,
                        'convite': convite,'workspaces':workspaces,'token':token })

# PÁGINA ==> REUNIÃO PLANEJAMENTO
def nova_planejamento(request, id):
    convite = dados_menu(request.user.email,"convite")
    workspaces = dados_menu(request.user.email,"workspaces")

    token = Token.objects.get(active=True, user=request.user)
# acessando gitlab
    ws = Workspace.objects.get(id=id)
    autoriza = autorizagrupo(token, ws.grupo)
    if  autoriza == True:
        grupo_esp = grupo_gl(token, ws.grupo)  # busca grupo especifico
        projects = grupo_esp.projects.list()  # busca Projetos do grupo

        datainicio = datetime.now()
        date = datainicio.strftime('%d/%m/%Y %H:%M')

        team = Colaborador.objects.filter(active=True, workspace=id)
        colaboradores = []
        for p in team:
            todos = User.objects.all()
            for um in todos:
                if p.email == um.email:
                    colaboradores.append(um)

        # INICIO - verificando se user pode criar ata
        autorization = False
        for colab in team:
            if colab.email == request.user.email:
                autorization = True
        # FIM - verificando se user pode criar ata

        if autorization == True:
            return render(request, 'gls/planejamento.html',
                        {'datainicio': date, 'participantes': colaboradores, 'token': token, 'id': id,
                        'workspaces': workspaces, 'projects': projects, 'convite': convite})
        else:
            '''messages.error(
                request, 'Usuario não autorizado para ver a ata')
            return redirect('/login/')'''
            #return HttpResponse('Usuario não autorizado')
            mensagem = 'Usuario não autorizado para ver Ata!'
            return redirect('/erro_autorizacao/'+mensagem)
    
    else:
        mensagem = 'Usuário sem permissão de cadastro de ata. Verifique se está vinculado como membro do grupo no gitlab.com.'
        return redirect('/erro_autorizacao/'+mensagem)

#Pagina selecionar projeto
def seleciona_projeto(request,id):
    convite = dados_menu(request.user.email,"convite")
    workspaces = dados_menu(request.user.email,"workspaces")

    token = Token.objects.get(
        active=True, user=request.user)  # token do usuario
# acessando gitlab
    ws = Workspace.objects.get(id=id)
    autoriza = autorizagrupo(token, ws.grupo)
    if  autoriza == True:
        grupo_esp = grupo_gl(token, ws.grupo)  # busca grupo especifico
        projects = grupo_esp.projects.list()  # busca Projetos do grupo
        
        return render(request, 'gls/selecProj.html',{'convite': convite, 'workspaces': workspaces, 'token': token,
                                                'id': id,'ws': ws, 'projects': projects})
    else:
        mensagem = 'Usuário sem permissão de cadastro de ata. Verifique se está vinculado como  membro do grupo no gitlab.com.'
        return redirect('/erro_autorizacao/'+mensagem)


# PÁGINA ==> REUNIÃO DIÁRIA
def nova_diaria(request, id):
    convite = dados_menu(request.user.email,"convite")
    workspaces = dados_menu(request.user.email,"workspaces")

    token = Token.objects.get(
        active=True, user=request.user)  # token do usuario
# acessando gitlab
    ws = Workspace.objects.get(id=id)
    grupo_esp = grupo_gl(token, ws.grupo)  # busca grupo especifico
    projects = grupo_esp.projects.list()  # busca Projetos do grupo
    projeto_diaria = request.POST.get('projeto_selecionado')
    #return HttpResponse(projeto_diaria)
    nomeProjeto = ""
    for proj in projects:
        if proj.id == int(projeto_diaria):
            nomeProjeto = projeto_diaria+" - "+proj.name

    issues = []
    page = 0
    # print(datetime.now())
    while True:
        next_page = grupo_esp.issues.list(per_page=50, page=page)
        if not next_page:
            break
        issues.extend(next_page)
        page += 1
    # print(datetime.now())

    issues_projeto = []
    for issue in issues:
        if int(issue.project_id) == int(projeto_diaria):
            print(issue.project_id)
            issues_projeto.append(issue)
    datainicio = datetime.now()
    date = datainicio.strftime('%d/%m/%Y %H:%M')

    team = Colaborador.objects.filter(active=True, workspace=id)
    colaboradores = []
    for p in team:
        todos = User.objects.all()
        for um in todos:
            if p.email == um.email:
                colaboradores.append(um)

    # INICIO - verificando se user pode criar ata
    autorization = False
    for colab in team:
        if colab.email == request.user.email:
            autorization = True
    # FIM - verificando se user pode criar ata

    if autorization == True:
        return render(request, 'gls/diaria.html',
                      {'datainicio': date, 'participantes': colaboradores, 'token': token, 'id': id,
                       'workspaces': workspaces, 'projeto': nomeProjeto, 'issues': issues_projeto, 'convite': convite})
    else:
        #return HttpResponse('Usuario não autorizado')
        mensagem = 'Usuario não autorizado!'
        return redirect('/erro_autorizacao/'+mensagem)

# PÁGINA ==> REUNIÃO FINAL
def nova_final(request, id):
    convite = dados_menu(request.user.email,"convite")
    workspaces = dados_menu(request.user.email,"workspaces")

    token = Token.objects.get(
        active=True, user=request.user)  # token do usuario

# acessando gitlab
    ws = Workspace.objects.get(id=id)
    autoriza = autorizagrupo(token, ws.grupo)
    if  autoriza == True:
        grupo_esp = grupo_gl(token, ws.grupo)  # busca grupo especifico
        projects = grupo_esp.projects.list()  # busca Projetos do grupo

        datainicio = datetime.now()
        date = datainicio.strftime('%d/%m/%Y %H:%M')

        team = Colaborador.objects.filter(active=True, workspace=id)
        colaboradores = []
        for p in team:
            todos = User.objects.all()
            for um in todos:
                if p.email == um.email:
                    colaboradores.append(um)

        # INICIO - verificando se user pode criar ata
        autorization = False
        for colab in team:
            if colab.email == request.user.email:
                autorization = True
        # FIM - verificando se user pode criar ata

        if autorization == True:
            return render(request, 'gls/final.html',
                        {'datainicio': date, 'participantes': colaboradores, 'token': token, 'id': id,
                        'workspaces': workspaces, 'projects': projects, 'convite': convite})
        else:
            '''messages.error(
                request, 'Usuario não autorizado para ver a ata')
            return redirect('/login/')'''
            #return HttpResponse('Usuario não autorizado')
            mensagem = 'Usuario não autorizado para ver Ata!'
            return redirect('/erro_autorizacao/'+mensagem)
    else:
        mensagem = 'Usuário sem permissão de cadastro de ata. Verifique se está vinculado como  membro do grupo no gitlab.com.'
        return redirect('/erro_autorizacao/'+mensagem)


# AÇÃO ==> ADICIONAR REUNIÃO
def submit_reuniao(request, id):
    if request.POST:
        workspace = Workspace.objects.get(
            active=True, id=id)

        # presentes = request.GET['presentes']
        tipo = request.GET['tipo']

        if tipo == "Reunião Diária":
            assuntos = request.POST.getlist('assuntos[]')
        else:
            assuntos = request.POST.get('assuntos')

        projeto = request.POST.get('projeto')
        datainicio = request.POST.get('datainicio')
        participantes = request.POST.getlist('participantes[]')
        presentes =""
        for nome in participantes:
            presentes = presentes+nome+", " 
        #return HttpResponse(presentes)  #só pra testes

        if (datainicio == ""):
            # print (datainicio)
            datainicio = request.GET['datainicio']
            # print (datainicio)

        datafim = request.POST.get('datafim')
        if (datafim == ""):
            datafim = datetime.now().strftime('%d/%m/%Y %H:%M')
            # print(datafim)
        # print(projeto)

        user_colab = Colaborador.objects.filter(email=request.user.email)
        for ws_user in user_colab:
            if ws_user.workspace == workspace:
                add = cerimonia.objects.create(workspace=workspace, dataFim=datafim, dataInicio=datainicio, tipo=tipo,
                                               presentes=presentes, assuntos=assuntos, projeto=projeto, user=request.user)
                add.save()
                return redirect('/ws/' + id)

        #return HttpResponse('Usuário não autorizado')
        mensagem = 'Usuario não autorizado para criar Ata!'
        return redirect('/erro_autorizacao/'+mensagem)

# AÇÃO ==> IMPRIMIR UNICA ATA EM PDF
def imprimir_pdf(request, id):
    ata = cerimonia.objects.get(id=id)
    assuntos = []
    ata.assuntos = ata.assuntos.replace("'","")
    ata.assuntos = ata.assuntos.replace("]","")
    ata.assuntos = ata.assuntos.replace("[","")
    if ata.tipo == "Reunião Diária":
        assuntos = ata.assuntos.split(",")
        #return HttpResponse(assuntos)
    else:
        assuntos.append(ata.assuntos)
        #return HttpResponse(assuntos)
    data = {
        'inicio': ata.dataInicio,
        'fim': ata.dataFim,
        'assuntos': assuntos,
        'presentes': ata.presentes,
        'tipo': ata.tipo,
        'projeto': ata.projeto,
        'dataimpressao': datetime.now(),
    }
    pdf = render_to_pdf('gls/impressao_ata.html', data)
    return HttpResponse(pdf, content_type='application/pdf')

# AÇÃO ==> IMPRIMINDO VARIAS ATAS NO MESMO PDF
def imprimir_pdf_data(request):
    txtColuna1 = request.POST.get("txtColuna1")

    #return HttpResponse(txtColuna1)
    if txtColuna1 == "":
        #return HttpResponse("Campo de data deve ser informado")
        mensagem = 'Campo "data" deve ser informado!'
        return redirect('/erro_autorizacao/'+mensagem)


    if txtColuna1 != "":
        #return HttpResponse(txtColuna1)
        todas_atas = cerimonia.objects.all().order_by('dataInicio')
        atas = []
        for item in todas_atas:
            dataInicio = item.dataInicio
            teste = dataInicio.find(txtColuna1)
            if teste == 0:
                print (item.dataInicio)
                atas.append(item)
        cont = 0
        for ata in atas:
            ata.pag = cont+1
            cont = cont+1
            ata.paginastotal = len(atas)
            assuntos = []
            ata.assuntos = ata.assuntos.replace("'","")
            ata.assuntos = ata.assuntos.replace("]","")
            ata.assuntos = ata.assuntos.replace("[","")
            if ata.tipo == "Reunião Diária":
                assuntos = ata.assuntos.split(",")
                ata.assuntos2 = assuntos
                #return HttpResponse(assuntos)
            else:
                assuntos.append(ata.assuntos)
                ata.assuntos2 = assuntos
                #return HttpResponse(assuntos)

        #return HttpResponse(len(atas))
        data = {
            'atas': atas,
            'dataimpressao': datetime.now(),
        }
        pdf = render_to_pdf('gls/impressao_atas_diversas.html', data)
        return HttpResponse(pdf, content_type='application/pdf')


# AÇÃO == > RECEBE PARAMETROS E IMPRIME TEMPLATE
def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    #pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None



# Só mostra a lista de projetos bruta
@login_required(login_url='/login/')
def brutoAPI(request):
    token = Token.objects.get(id=8)
    gl = gitlab.Gitlab(settings.URL, oauth_token=token.token)
    gl.auth()
    projects = gl.projects.list(visibility='private')
    return HttpResponse(projects)


# Mostra tela projetos.html (teste com os projetos separados)


def projetos(request):
    # return render(request, 'gls/projetos.html'
    workspaces = Workspace.objects.filter(
        active=True).values('id', 'active', 'nome', 'grupo')

    # print(workspaces)

    varia = grupo_gl(5453619)
    print(varia)
    return HttpResponse(varia)

    token = Token.objects.get(user=request.user)  # token do usuario
    # acessando gitlab
    gl = gitlab.Gitlab(token.url, oauth_token=token.token)
    gl.auth()
    # buscando projetos
    groups = gl.groups.list()
    group = gl.groups.get(5453619)  # busca grupo especifico
    projects = group.projects.list()  # busca Projetos do grupo
    issues = group.issues.list()
    milestones = []
    for issue in issues:
        milestones.append(issue.milestone)

    return render(request, 'gls/projetos.html',
                  {'workspaces': workspaces, 'projetos': projects, 'milestones': milestones, 'issues': issues})


def select(request):
    wsgeral = Workspace.objects.filter(active=True)

    #wsgeral = []

    return render(request, 'gls/testeselect2.html', {'ws': wsgeral})
