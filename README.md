# glsmeeting
 Trabalho de TCC2 - Sistemas da Informaçã CEULP ULBRA 2019/2

instalar o PostgreSQL no pc
Criar banco de Dados no PostgreSQL (config em settings.py):
	db_name: glsmeeting
	db_user: postgres
	db_pass: admin
	   host: localhost
	   port: 5432

Instalar o Python 3.7
Executar CMD (verificar Virtual Env):
	python -m pip install -U pip		#instalar PIP
	pip install django            		#instalar Django
	pip install --upgrade python-gitlab	#instalar biblioteca Gitlab
	pip install xhtml2pdf			#Biblioteca pisa pdf
	pip install psycopg2  			#biblioteca postgree	
	python manage.py migrate		#migrar modelo de banco de dados 
	python manage.py runserver		#iniciar servidor 
Acessar no navegador
	http://127.0.0.1:8000/
