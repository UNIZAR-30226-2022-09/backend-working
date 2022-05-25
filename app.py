
from flask import Flask, jsonify, request, redirect, url_for, session
import jwt
import datetime
from random import sample
import os
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import  select
from flask_migrate import Migrate
from flask_cors import CORS
from sqlalchemy import  Integer
import json
from pdf2image import convert_from_path
from sqlalchemy import func
from sqlalchemy import and_

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretollave'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
ABSOLUTE_PATH_TO_YOUR_FOLDER ='/home/dani/flask/static/fotosPerfil'
ABSOLUTE_PATH_TO_YOUR_PDF_FOLDER ='/home/dani/flask/static/pdf'
CORS(app)
db  = SQLAlchemy(app)
migrate = Migrate(app, db)

# Models
class Usuario(db.Model):
    nick = db.Column(db.String(20), primary_key=True)
    Nombre_de_usuario = db.Column(db.String(50))
    password = db.Column(db.String(50))
    e_mail = db.Column(db.String(50), unique=True, nullable=False)
    descripcion  = db.Column(db.String(1000))
    link  = db.Column(db.String(200))
    foto_de_perfil = db.Column(db.String(400))

class Sigue(db.Model):
    Usuario_Nicka = db.Column(db.String(20), db.ForeignKey('usuario.nick'),primary_key=True) # le sigue el usuario b
    Usuario_Nickb = db.Column(db.String(20), db.ForeignKey('usuario.nick'),primary_key=True) # sigue al usuario a

class Chat(db.Model):
    __tablename__="chat"

    id=db.Column(db.Integer, primary_key=True)                                                      
    nick=db.Column(db.String(20), db.ForeignKey('usuario.nick'))                                    # Usuario emisor del mensaje
    created_at=db.Column(db.DateTime, default=datetime.datetime.utcnow())                                      # Momento creación mensaje
    message=db.Column(db.String(500))                                                               # Contenido del mensaje
    room=db.Column(db.String(10))                                                                   # Chat al que pertenece

class chatRoom(db.Model):
    __tablename__="chatRoom"

    roomid = db.Column(db.Integer)   
    user1 = db.Column(db.String(20), db.ForeignKey('usuario.nick'), primary_key=True)
    user2 = db.Column(db.String(20), db.ForeignKey('usuario.nick'), primary_key=True)

class Publicacion(db.Model):

    id  = db.Column(Integer,primary_key=True)
    descripcion  = db.Column(db.String(1000))
    timestamp = db.Column(db.TIMESTAMP, nullable=False,
                  server_default=db.func.now(),
                  onupdate=db.func.now())
    Usuario_Nicka = db.Column(db.String(20), db.ForeignKey('usuario.nick'))

class Propia(db.Model):

    pdf = db.Column(db.String(400))
    portada = db.Column(db.String(400))
    id = db.Column(db.String(20), db.ForeignKey('publicacion.id'),primary_key=True)
    Usuario_Nicka = db.Column(db.String(20), db.ForeignKey('usuario.nick'))


class Recomendacion(db.Model):

    link  = db.Column(db.String(200),nullable=False)
    titulo = db.Column(db.String(200),nullable=False)
    autor  = db.Column(db.String(200),nullable=False)
    id = db.Column(db.String(20), db.ForeignKey('publicacion.id'),primary_key=True)
    Usuario_Nicka = db.Column(db.String(20), db.ForeignKey('usuario.nick'))


class Notificaciones(db.Model):
    #__tablename__="notificaciones"

    id  = db.Column(Integer,primary_key=True)                                                # Id Notificacion
    tipo = db.Column(Integer,nullable=False)                                                                       
    idPubli = db.Column(Integer)
    nickEmisor = db.Column(db.String(20),db.ForeignKey('usuario.nick'),nullable=False)           # Nick Receptor
    timestamp = db.Column(db.TIMESTAMP, nullable=False,                                             # Momento de publicación
                  server_default=db.func.now(),                                                     
                  onupdate=db.func.now())                                                                   # Fecha Notificacion
    nickReceptor = db.Column(db.String(20), db.ForeignKey('usuario.nick'),nullable=False)        # Nick Emisor
    comentario =  db.Column(db.String(200))                                                        # Comentario

class Prefiere(db.Model):

    Usuario_Nicka = db.Column(db.String(20), db.ForeignKey('usuario.nick'),primary_key=True)
    tema = db.Column(db.String(50),primary_key=True)


class Trata_pub_del_tema(db.Model):

    id = db.Column(db.Integer, db.ForeignKey('publicacion.id'),primary_key=True)
    tema = db.Column(db.String(50),primary_key=True)

class Gusta(db.Model):

    id = db.Column(db.Integer, db.ForeignKey('publicacion.id'),primary_key=True)
    Usuario_Nicka = db.Column(db.String(20), db.ForeignKey('usuario.nick'),primary_key=True)


class Comenta(db.Model):
    id  = db.Column(Integer,primary_key=True)
    idPubli = db.Column(db.Integer, db.ForeignKey('publicacion.id'))

    Usuario_Nicka = db.Column(db.String(20), db.ForeignKey('usuario.nick'))
    comentario  = db.Column(db.String(1000))


class Guarda(db.Model):

    id = db.Column(db.Integer, db.ForeignKey('publicacion.id'),primary_key=True)
    Usuario_Nicka = db.Column(db.String(20), db.ForeignKey('usuario.nick'),primary_key=True) # de quien son los guardados
    tipo =db.Column(db.Integer,nullable=False)


class Comentario:
  def __init__(self, id,idComen,nick, foto_de_perfil,comentario):
    self.id = id
    self.nick = nick
    self.foto_de_perfil = foto_de_perfil
    self.comentario = comentario
    self.idComen = idComen


class PublicacionHome:
  def __init__(self, nick,Nombre_de_usuario, foto_de_perfil,ids,descripciones,timestamps,Gustas,Guardados,Comentarios):
    self.nick = nick
    self.Nombre_de_usuario = Nombre_de_usuario
    self.foto_de_perfil = foto_de_perfil
    self.ids = ids
    self.descripciones = descripciones
    self.timestamps = timestamps
    self.Gustas = Gustas
    self.Guardados = Guardados
    self.Comentarios = Comentarios

class Pdfs(PublicacionHome):
    """Clase que representa a un pdf"""

    def __init__(self, nick,Nombre_de_usuario, foto_de_perfil,ids,descripciones,timestamps,Gustas,Guardados,Comentarios,pdf,portada):
        """Constructor de clase pdf"""

        # Invoca al constructor de clase Persona
        PublicacionHome.__init__(self, nick,Nombre_de_usuario, foto_de_perfil,ids,descripciones,timestamps,Gustas,Guardados,Comentarios)

        # Nuevos atributos
        self.pdf = pdf
        self.portada = portada

class Recomendados(PublicacionHome):
    """Clase que representa a un pdf"""

    def __init__(self, nick,Nombre_de_usuario, foto_de_perfil,ids,descripciones,timestamps,Gustas,Guardados,Comentarios,links,titulos,autores):
        """Constructor de clase pdf"""

        # Invoca al constructor de clase Persona
        PublicacionHome.__init__(self,nick, Nombre_de_usuario, foto_de_perfil,ids,descripciones,timestamps,Gustas,Guardados,Comentarios)

        # Nuevos atributos
        self.links = links
        self.titulos = titulos
        self.autores = autores

class Notificacion:
  def __init__(self, ids,nick,tipo, foto_de_perfil,timestamps):
    self.ids = ids
    self.nick = nick
    self.foto_de_perfil = foto_de_perfil
    self.tipo = tipo
    self.timestamps = timestamps

class meGusta(Notificacion):

    def __init__(self, ids,nick,tipo, foto_de_perfil,timestamps, idPub):
        """Constructor de clase pdf"""

        # Invoca al constructor de clase Persona
        Notificacion.__init__(self,ids,nick,tipo, foto_de_perfil,timestamps)

        # Nuevos atributos
        self.idPub = idPub

class comenta(Notificacion):

    def __init__(self, ids,nick,tipo, foto_de_perfil,timestamps, comentario,idPub):
        """Constructor de clase pdf"""

        # Invoca al constructor de clase Persona
        Notificacion.__init__(self,ids,nick,tipo, foto_de_perfil,timestamps)

        # Nuevos atributos
        self.comentario = comentario
        self.idPub = idPub




def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        token = request.headers['token']
        if not token:
            return jsonify({'error': 'Token no existe'}), 403

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = Usuario.query.filter_by(nick=data['nick']).first()
            current_user = data['nick']
        except:
            return jsonify({'error': 'Token no valido'}), 403

        return f(current_user,*args, **kwargs)
    return decorated



@app.route('/unprotected')
def unprotected():
    return jsonify({'message': 'Puede entrar tol mundo'})

@app.route('/protected')
@token_required
def protected(current_user):
    print(current_user)
    return jsonify({'message': 'Puedes entrar si puedes'})

# Ruta para el login



@app.route('/register', methods=['POST'])
def add_data():
    data= request.get_json()

    user = Usuario.query.filter_by(e_mail=data['e_mail']).first()
    nick = Usuario.query.filter_by(nick=data['nick']).first()
    if user: # si esto devuelve algo entonces el email existe
        return jsonify({'error': 'Existe correo'}) #json diciendo error existe email
    if nick:
        return jsonify({'error': 'Existe nick'})
    
    register = Usuario(nick=data['nick'],password=generate_password_hash(data['password']), e_mail=data['e_mail'],foto_de_perfil="platon.jpg")
    db.session.add(register)
    db.session.commit()

    token = jwt.encode({'nick' : data['nick'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
    return jsonify({'token' : token.decode('UTF-8')})



@app.route('/login', methods=['POST'])
def login():

    data= request.get_json()
    if '@' in data['nickOcorreo']:
        user = Usuario.query.filter_by(e_mail=data['nickOcorreo']).first()
        
    else:
        user = Usuario.query.filter_by(nick=data['nickOcorreo']).first()

    if not user:
        return jsonify({'error': 'No existe ese usuario'})#error mal user
    if not check_password_hash(user.password, data['password']):
        return jsonify({'error': 'Mala contraseña'}) #error mala contraseña


    token = jwt.encode({'nick' : user.nick, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=9999999)}, app.config['SECRET_KEY'])
    return jsonify({'token' : token.decode('UTF-8'), 'nick' : user.nick})




@app.route('/mostrarPerfil', methods=['GET'])
@token_required
def mostrarPerfil(current_user):
    nick = request.headers['nick']
    s = select([Usuario.Nombre_de_usuario,  Usuario.descripcion,Usuario.link, Usuario.foto_de_perfil]).where((Usuario.nick == nick))
    result = db.session.execute(s)

    siguiendo = db.session.query(Sigue).filter(and_(Sigue.Usuario_Nicka == nick , Sigue.Usuario_Nickb == current_user)).count()
    seguidos= db.session.query(Sigue).filter(Sigue.Usuario_Nickb == nick ).count()
    seguidores= db.session.query(Sigue).filter(Sigue.Usuario_Nicka == nick ).count()
    nposts= db.session.query(Publicacion).filter(Publicacion.Usuario_Nicka == nick ).count()

    tema = select([Prefiere.tema]).where((Prefiere.Usuario_Nicka == nick))
    temas = db.session.execute(tema)
    vector = []
    for row in temas:
        vector += row
    for row in result:
        fila = {
            "nick": nick,
            "nombre_de_usuario":row[0],
            "descripcion":row[1],
            "link":row[2],
            "foto_de_perfil": 'http://51.255.50.207:5000/display/' + row[3],
            "nsiguiendo": seguidos,
            "nseguidores": seguidores,
            "nposts": nposts,
            "siguiendo" : bool(siguiendo),
            "tematicas": vector
        }
    return fila

@app.route('/display/<filename>')
def fotoget(filename):
    return redirect(url_for('static', filename='fotosPerfil/' + filename),code = 301)


@app.route('/editarPerfil', methods=['POST'])
@token_required
def editarPerfilpost(current_user):

    data= request.get_json()
    user = Usuario.query.filter_by(nick=current_user).first()
    user.Nombre_de_usuario = data['nombre_de_usuario']
    user.descripcion = data['descripcion']
    user.link = data['link']
    tematicas = data['tematicas']
    todo = Prefiere.query.filter_by( Usuario_Nicka=current_user).first()
    while todo is not None:
        db.session.delete(todo)
        todo = Prefiere.query.filter_by( Usuario_Nicka=current_user).first()
    db.session.commit()
    for temas in tematicas:
        #tema = Prefiere.query.filter_by(tema=temas).first()
        #if not tema:
        tema = Prefiere(Usuario_Nicka=current_user, tema = temas)
        db.session.add(tema)
    
    db.session.commit()

    token = jwt.encode({'nick' : current_user, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
    return jsonify({'token' : token.decode('UTF-8')})


@app.route('/actualizarImagen', methods=['POST'])
@token_required
def actualizarImagen(current_user):
    user = Usuario.query.filter_by(nick=current_user).first()

    if request.files['nueva_foto'] is not None: 
            file = request.files['nueva_foto']

            filename = secure_filename(str(current_user)) + ".jpg"

            file.save(os.path.join(ABSOLUTE_PATH_TO_YOUR_FOLDER, filename))
            user.foto_de_perfil = filename 
            db.session.commit()

    token = jwt.encode({'nick' : current_user, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
    return jsonify({'token' : token.decode('UTF-8')})

@app.route('/subirPost', methods=['POST'])
@token_required
def subirPost(current_user):

    data= request.get_json()
    
    publicacion = Publicacion(descripcion=data['descripcion'],Usuario_Nicka=current_user) #coger id
    db.session.add(publicacion)
    db.session.commit()
    tematicas = data['tematicas']
    for temas in tematicas:
        #temita = Tematica.query.filter_by(tema=temas).first()
        #if temita:
            nuevo = Trata_pub_del_tema(id=publicacion.id, tema = temas)
            db.session.add(nuevo)
    db.session.commit()
    if (data['tipo']=="1"): # articulo
        return jsonify({'id' : publicacion.id})
        #guardarPDF(request.files['pdf'], publicacion.id)
    elif(data['tipo']=="2"): # recomendacion
        recomendacion = Recomendacion(link=data['link'],titulo=data['titulo'], autor = data['autor'], id = publicacion.id, Usuario_Nicka=current_user)
        db.session.add(recomendacion)
        
    db.session.commit()
    token = jwt.encode({'nick' : current_user, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
    return jsonify({'token' : token.decode('UTF-8')})

@app.route('/subirPdf', methods=['POST'])
@token_required
def guardarPDF(current_user):
    print("bn : " + request.headers['id'])
    _id=request.headers['id']

    propia = Propia( id = _id, Usuario_Nicka=current_user)
    db.session.add(propia)
    db.session.commit()
    propia = Propia.query.filter_by(id=_id).first()
    if propia:
        if request.files['pdf'] is not None:
            file = request.files['pdf']
            filename = str(_id) + '.pdf'
            file.save(os.path.join(ABSOLUTE_PATH_TO_YOUR_PDF_FOLDER, filename))
            propia.pdf = filename
            
            path= ABSOLUTE_PATH_TO_YOUR_PDF_FOLDER + '/' +  filename
            pages = convert_from_path(path, 0)
            for page in pages:
                output = str(_id) + '.png'
                pathimage = 'static/portadasPdf/' + output
                page.save(pathimage, 'PNG')
                propia.portada = output
                db.session.add(propia)
                db.session.commit()
                token = jwt.encode({'nick' : current_user, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
                return jsonify({'token' : token.decode('UTF-8')})
        else:
            print("pdf nulo")
            return jsonify({'error': 'No existe parámetro PDF'}), 403
    else:
        return jsonify({'error': 'Mal envio'}), 403
@app.route('/display3/<filename>')
def portadaGet(filename):
    return redirect(url_for('static', filename='portadasPdf/' + filename),code = 301)


@app.route('/mostrarArticulos', methods=['GET'])
@token_required
def mostrarArticulos(current_user):
    Publis = []
    
    mostrarHome(Publis,request.headers['nick'],1)

    finalDictionary = {}
    i=0
    x=0
    for x in  range(len(Publis)):
            existe = db.session.query(Propia).filter(Propia.id == Publis[x].ids ).count()
                #ver si ese ID existe en recomendacion sino es un post propio
            if bool(existe):
                guardaPDF(Publis[x],finalDictionary,current_user)
                i = i + 1
    
    return json.dumps(finalDictionary, indent = i)
                

@app.route('/display2/<filename>')
def pdf(filename):
    return redirect(url_for('static', filename='pdf/' + filename),code = 301)

@app.route('/mostrarRecomendaciones', methods=['GET'])
@token_required
def getPostsRecomendados(current_user):

    Publis = []
    
    mostrarHome(Publis,request.headers['nick'],2)

    finalDictionary = {}
    i=0
    x=0
    for x in  range(len(Publis)):
            existe = db.session.query(Recomendacion).filter(Recomendacion.id == Publis[x].ids ).count()
            
                #ver si ese ID existe en recomendacion sino es un post propio
            if bool(existe):
                print("es recomendacion: " ,Publis[x].ids, " ", Publis[x].Nombre_de_usuario, " ",Publis[x])
                guardaRecomendacion(Publis[x],finalDictionary,current_user)
                i = i + 1
    
    return json.dumps(finalDictionary, indent = i)            

@app.route('/buscarUsuarios', methods=['GET'])
@token_required
def getUsuarios(current_user):
    nick = request.headers['nick']

    search = "%{}%".format(nick)
    resulta = Usuario.query.filter(Usuario.nick.like(search)).all()
    #resultb = Usuario.query.filter(Usuario.nick.like(search)).all()

    print(resulta)
    nicks = []
    finalDictionary = {}
    foto_de_perfil= []
    for a in resulta: 
         nicks.append(str(a.nick))
         foto_de_perfil.append(str(a.foto_de_perfil))
    i=0
    for x in  nicks:
        print(x)
        nombreCompletofoto = "http://51.255.50.207:5000/display/" + str(foto_de_perfil[i])
        finalDictionary[x] = { 'foto_de_perfil' : nombreCompletofoto } #funciona

        i = i+1
    print (i)
    print (finalDictionary)
    return  json.dumps(finalDictionary, indent = i)



@app.route('/darLike', methods=['POST'])
@token_required
def darLike(current_user):
    data= request.get_json()
    
    gusta = Gusta.query.filter_by(id=data['id'] ,Usuario_Nicka=current_user).first()

    if gusta: 
        db.session.delete(gusta)
    else:        
        like = Gusta(id=data['id'], Usuario_Nicka=current_user) 
        nickRecep = Publicacion.query.filter_by(id=data['id']).first()
        notificacion = Notificaciones(tipo=1,idPubli=data['id'], nickEmisor=current_user, nickReceptor= nickRecep.Usuario_Nicka)
        db.session.add(like)
        db.session.add(notificacion)

    db.session.commit()

    token = jwt.encode({'nick' : current_user, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
    return jsonify({'token' : token.decode('UTF-8')})


@app.route('/comentar', methods=['POST'])
@token_required
def comentar(current_user):
    data= request.get_json()

    guardar = Comenta(idPubli=data['id'], Usuario_Nicka=current_user,comentario=data['comentario'])
    nickRecep = Publicacion.query.filter_by(id=data['id']).first()
    notificacion = Notificaciones(tipo=2,idPubli=data['id'], nickEmisor=current_user, nickReceptor= nickRecep.Usuario_Nicka, comentario=data['comentario'])
    db.session.add(notificacion)

    db.session.add(guardar)
    db.session.commit()


    token = jwt.encode({'nick' : current_user, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
    return jsonify({'token' : token.decode('UTF-8')})

@app.route('/verComentarios', methods=['GET'])
@token_required
def verComentarios(current_user):

    coments = []
    comentarios=Comenta.query.filter_by(idPubli=request.headers['id']).order_by(Comenta.id.desc())
    for r in comentarios:
        x = select([ Usuario.foto_de_perfil]).where((Usuario.nick == r.Usuario_Nicka))
        resultb = db.session.execute(x)
        for a in resultb:
            coments.append(Comentario(r.idPubli,r.id,r.Usuario_Nicka,a.foto_de_perfil,r.comentario))
    finalDictionary = {}
    i=0
    for comen in coments:
        foto_de_perfil_Completo= 'http://51.255.50.207:5000/display/' + str(comen.foto_de_perfil)
        finalDictionary[comen.idComen] = { 'nick' : str(comen.nick) ,'foto_de_perfil' : str(foto_de_perfil_Completo), 'comentario':  str(comen.comentario)}
        i = i + 1

    return json.dumps(finalDictionary, indent = i)
@app.route('/guardar', methods=['POST'])
@token_required
def guardarPost(current_user):
    data= request.get_json()
    guardado = Guarda.query.filter_by(id=data['id'], Usuario_Nicka=current_user).first()
    if guardado: 
        print("true")
        db.session.delete(guardado)
        
    else:

        art = Propia.query.filter_by(id=data['id']).first()
        if art:
            guardar = Guarda(id=data['id'],  Usuario_Nicka=current_user, tipo=1) #Usuario_Nicka=r.Usuario_Nicka,
            db.session.add(guardar)
        else:
            guardar = Guarda(id=data['id'],  Usuario_Nicka=current_user, tipo=2) #Usuario_Nicka=r.Usuario_Nicka,
            db.session.add(guardar)
    db.session.commit()

    token = jwt.encode({'nick' : current_user, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
    return jsonify({'token' : token.decode('UTF-8')})


@app.route('/seguirUser', methods=['POST'])
@token_required
def seguirUser(current_user):
    data = request.get_json()
    print(data['nick'])
    siguiendo = Sigue.query.filter_by(Usuario_Nicka=data['nick'], Usuario_Nickb=current_user).first()
    if siguiendo: 
        print("true")
        db.session.delete(siguiendo)
        
    else:
        print("false")
        seguir = Sigue(Usuario_Nicka=data['nick'], Usuario_Nickb=current_user)
        notificacion = Notificaciones(tipo=3, nickEmisor=current_user, nickReceptor= data['nick'])
        db.session.add(notificacion)
        db.session.add(seguir)

    db.session.commit()

    token = jwt.encode({'nick' : current_user, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
    return jsonify({'token' : token.decode('UTF-8')})



@app.route('/Home', methods=['GET'])
@token_required
def Home(current_user):

    Publis = []
    
    todosSiguiendo=Sigue.query.filter_by(Usuario_Nickb=current_user).all()
    for nick in todosSiguiendo:
        mostrarHome(Publis,nick.Usuario_Nicka,3)

    finalDictionary = {}
    i=0
    x=0
    for x in  range(len(Publis)):
            existe = db.session.query(Propia).filter(Propia.id == Publis[x].ids ).count()
                #ver si ese ID existe en recomendacion sino es un post propio
            if bool(existe):
                guardaPDF(Publis[x],finalDictionary,current_user)
                i = i + 1
            else:
                guardaRecomendacion(Publis[x],finalDictionary,current_user)
                i = i + 1

    return json.dumps(finalDictionary, indent = i)


@app.route('/Guardados', methods=['GET'])
@token_required
def Guardados(current_user):

    Publis = []
    
    todosGuardados=Guarda.query.filter_by(Usuario_Nicka=current_user).all()
    for ids in todosGuardados:
        print("vamos: ", ids.id)
        guardarId(Publis,ids.id)

    finalDictionary = {}
    i=0
    x=0
    for x in  range(len(Publis)):
            existe = db.session.query(Propia).filter(Propia.id == Publis[x].ids ).count()
                #ver si ese ID existe en recomendacion sino es un post propio
            if bool(existe):
                guardaPDF(Publis[x],finalDictionary,current_user)
                i = i + 1
            else:
                guardaRecomendacion(Publis[x],finalDictionary,current_user)
                i = i + 1

    return json.dumps(finalDictionary, indent = i)


@app.route('/GuardadosArticulos', methods=['GET'])
@token_required
def GuardadosArticulos(current_user):

    Publis = []
    
    todosGuardados=Guarda.query.filter_by(Usuario_Nicka=current_user).all()
    for ids in todosGuardados:
        print("vamos: ", ids.id)
        guardarId(Publis,ids.id)

    finalDictionary = {}
    i=0
    x=0
    for x in  range(len(Publis)):
            existe = db.session.query(Propia).filter(Propia.id == Publis[x].ids ).count()
                #ver si ese ID existe en recomendacion sino es un post propio
            if bool(existe):
                guardaPDF(Publis[x],finalDictionary,current_user)
                i = i + 1

    return json.dumps(finalDictionary, indent = i)

@app.route('/GuardadosRecomendaciones', methods=['GET'])
@token_required
def GuardadosRecomendaciones(current_user):

    Publis = []
    
    todosGuardados=Guarda.query.filter_by(Usuario_Nicka=current_user).all()
    for ids in todosGuardados:
        print("vamos: ", ids.id)
        guardarId(Publis,ids.id)

    finalDictionary = {}
    i=0
    x=0
    for x in  range(len(Publis)):
            existe = db.session.query(Recomendacion).filter(Recomendacion.id == Publis[x].ids ).count()
                #ver si ese ID existe en recomendacion sino es un post propio
            if bool(existe):
                guardaRecomendacion(Publis[x],finalDictionary,current_user)
                i = i + 1

    return json.dumps(finalDictionary, indent = i)



def guardaPDF(Publis,finalDictionary,current_user):
    GustaMio = db.session.query(Gusta).filter(Gusta.Usuario_Nicka == current_user, Gusta.id == Publis.ids  ).count()
    GuardadoMio = db.session.query(Guarda).filter(Guarda.Usuario_Nicka == current_user, Guarda.id == Publis.ids ).count()
    nombreCompletopdf = "http://51.255.50.207:5000/display2/" + str(Publis.pdf)
    nombreCompletoPortada = "http://51.255.50.207:5000/display3/" + str(Publis.portada)
    foto_de_perfil_Completo= 'http://51.255.50.207:5000/display/' + str(Publis.foto_de_perfil)
    finalDictionary[Publis.ids] = { 'tipo' : 1 ,'pdf' :nombreCompletopdf, 'portada':  nombreCompletoPortada, 'descripcion' : str(Publis.descripciones),'usuario' : Publis.nick,'foto_de_perfil' : foto_de_perfil_Completo,'nlikes' : int(Publis.Gustas),'likemio' : bool(GustaMio),'ncomentarios' : int(Publis.Comentarios),'nguardados' : int(Publis.Guardados),'guardadomio' : bool(GuardadoMio) }

def guardaRecomendacion(Publis,finalDictionary,current_user):
    GustaMio = db.session.query(Gusta).filter(Gusta.Usuario_Nicka == current_user, Gusta.id == Publis.ids  ).count()
    #print("GustaMio: ", Publis.nick , "  ", Publis.ids , " ",GustaMio)
    GuardadoMio = db.session.query(Guarda).filter(Guarda.Usuario_Nicka == current_user, Guarda.id == Publis.ids ).count()
    foto_de_perfil_Completo= 'http://51.255.50.207:5000/display/' + str(Publis.foto_de_perfil)
    finalDictionary[Publis.ids] = { 'tipo' : 2 ,'titulo' : str(Publis.titulos), 'autor' : str(Publis.autores),'descripcion' : str(Publis.descripciones),'link' : str(Publis.links),'usuario' : Publis.nick,'foto_de_perfil' : foto_de_perfil_Completo,'nlikes' : int(Publis.Gustas),'likemio' : bool(GustaMio),'ncomentarios' : int(Publis.Comentarios),'nguardados' : int(Publis.Guardados),'guardadomio' : bool(GuardadoMio) }
                


def mostrarHome(Publis,nick,tipo):
    Nombre_de_usuario=""
    foto_de_perfil=""
    ids=""
    Gustas=""
    Comentarios=""
    descripciones=""
    timestamps=""   
    Guardados=""
    pdfname=""
    portadaname=""
    links=""
    titulos=""
    autores=""
    x = select([Usuario.Nombre_de_usuario, Usuario.foto_de_perfil]).where((Usuario.nick == nick))
    resultb = db.session.execute(x)
    
    
    for b in resultb: 
        Nombre_de_usuario= str(b.Nombre_de_usuario)
        foto_de_perfil=str(b.foto_de_perfil)

    publicaciones = select([Publicacion.id,Publicacion.timestamp,Publicacion.descripcion ]).where(Publicacion.Usuario_Nicka == nick ).order_by(Publicacion.id.desc())

    results = db.session.execute(publicaciones)

    for r in results:
        #print("hola: ", r.id)
        ids=str(r.id)
        Gustas=str(db.session.query(func.count(Gusta.id).filter(Gusta.id == r.id)).scalar())
        #print("gustas: ", Gustas)
        Comentarios=str(db.session.query(Comenta).filter(Comenta.idPubli == r.id ).count())
        Guardados=(db.session.query(Guarda).filter(Guarda.id == r.id).count())
        descripciones=str(r.descripcion)
        timestamps=str(r.timestamp)
    
        pdf = Propia.query.filter_by(id=r.id).first()
        if pdf and (tipo==1 or tipo==3):
            print("es un pdf este numero: " , r.id)
            pdfname , portadaname = cargarDatosPDFstr(pdfname,portadaname,r.id)
            Publis.append(Pdfs(nick,Nombre_de_usuario,foto_de_perfil,ids,descripciones,timestamps,Gustas,Guardados,Comentarios,pdfname,portadaname))
        elif (tipo==2 or tipo==3):
            links,titulos,autores = cargarDatosRecomendacionesstr(links,titulos,autores,r.id)
            Publis.append(Recomendados(nick,Nombre_de_usuario,foto_de_perfil,ids,descripciones,timestamps,Gustas,Guardados,Comentarios,links,titulos,autores))

        

def guardarId(Publis,id):
    Nombre_de_usuario=""
    foto_de_perfil=""
    ids=""
    Gustas=""
    Comentarios=""
    descripciones=""
    timestamps=""   
    Guardados=""
    pdfname=""
    portadaname=""
    links=""
    titulos=""
    autores=""

    publicaciones = select([Publicacion.id,Publicacion.timestamp,Publicacion.descripcion ,Publicacion.Usuario_Nicka]).where(Publicacion.id == id )
    results = db.session.execute(publicaciones)
    for a in results: 
        print(a)
        x = select([Usuario.Nombre_de_usuario, Usuario.foto_de_perfil, Usuario.nick]).where((Usuario.nick == a.Usuario_Nicka))
        resultb = db.session.execute(x)
        for b in resultb: 
            Nombre_de_usuario= str(b.Nombre_de_usuario)
            foto_de_perfil=str(b.foto_de_perfil)


            ids=str(a.id)
            Gustas=str(db.session.query(func.count(Gusta.id).filter(Gusta.id == a.id)).scalar())
            print (Gustas)
            Comentarios=str(db.session.query(Comenta).filter(Comenta.idPubli == a.id ).count())
            Guardados=(db.session.query(Guarda).filter(Guarda.id == a.id).count())
            descripciones=str(a.descripcion)
            timestamps=str(a.timestamp)
        
            pdf = Propia.query.filter_by(id=a.id).first()
            if pdf :
                #print("es un pdf este numero: " , a.id)
                pdfname , portadaname = cargarDatosPDFstr(pdfname,portadaname,a.id)
                Publis.append(Pdfs(b.nick,Nombre_de_usuario,foto_de_perfil,ids,descripciones,timestamps,Gustas,Guardados,Comentarios,pdfname,portadaname))
            else:
                links,titulos,autores = cargarDatosRecomendacionesstr(links,titulos,autores,a.id)
                Publis.append(Recomendados(b.nick,Nombre_de_usuario,foto_de_perfil,ids,descripciones,timestamps,Gustas,Guardados,Comentarios,links,titulos,autores))




@app.route('/mostrarRecomendacionesPaginadas', methods=['GET'])
@token_required
def mostrarRecomendacionesPaginadas(current_user):
    Publis = []
    
    offsetreal = 0
    limite=request.headers['limit']
    offsetreal = int(request.headers['offset'])*int(limite)
    #todosGuardados=Guarda.query.filter_by(Usuario_Nicka=current_user).all()
    recomendacion = select([Recomendacion.id ]).where(Recomendacion.Usuario_Nicka == request.headers['nick'] ).order_by(Recomendacion.id.desc()).limit(int(limite)).offset(int(offsetreal))
    recomendaciones = db.session.execute(recomendacion)

    for ids in recomendaciones:
        print("vamos: ", ids.id)
        guardarId(Publis,ids.id)

    if len(Publis) == 0:
        print("hola", " offset: ", offsetreal, "limite: ", limite)
        return jsonify({'fin': 'La lista se ha acabado no hay mas posts'})

    Publis.sort(key = customSort, reverse=True)
    finalDictionary = {}
    i=0
    x=0
    for x in  range(len(Publis)):
        guardaRecomendacion(Publis[x],finalDictionary,current_user)
        i = i + 1
    
    return json.dumps(finalDictionary, indent = i)
                

@app.route('/mostrarArticulosPaginados', methods=['GET'])
@token_required
def mostrarArticulosPaginados(current_user):
    Publis = []
    
    offsetreal = 0
    limite=request.headers['limit']
    offsetreal = int(request.headers['offset'])*int(limite)
    #todosGuardados=Guarda.query.filter_by(Usuario_Nicka=current_user).all()
    propias = select([Propia.id ]).where(Propia.Usuario_Nicka == request.headers['nick'] ).order_by(Propia.id.desc()).limit(int(limite)).offset(int(offsetreal))
    results = db.session.execute(propias)
    for ids in results:
        print("vamos: ", ids.id)
        guardarId(Publis,ids.id)

    if len(Publis) == 0:
        print("hola", " offset: ", offsetreal, "limite: ", limite)
        return jsonify({'fin': 'La lista se ha acabado no hay mas posts'})
    finalDictionary = {}
    i=0
    x=0
    for x in  range(len(Publis)):
        guardaPDF(Publis[x],finalDictionary,current_user)
        i = i + 1
    
    return json.dumps(finalDictionary, indent = i)
                

@app.route('/mostrarGuardadosPaginados', methods=['GET'])
@token_required
def mostrarGuardadosPaginados(current_user):
    Publis = []
    
    offsetreal = 0
    limite=request.headers['limit']
    offsetreal = int(request.headers['offset'])*int(limite)
    #todosGuardados=Guarda.query.filter_by(Usuario_Nicka=current_user).all()
    Publis = []
    
    todosGuardados=select([Guarda.id ]).where(Guarda.Usuario_Nicka == current_user ).order_by(Guarda.id.desc()).limit(int(limite)).offset(int(offsetreal))
    todosGuardados = db.session.execute(todosGuardados)
    for ids in todosGuardados:
        guardarId(Publis,ids.id)

    if len(Publis) == 0:
        print("hola", " offset: ", offsetreal, "limite: ", limite)
        return jsonify({'fin': 'La lista se ha acabado no hay mas posts'})
    finalDictionary = {}
    i=0
    x=0
    for x in  range(len(Publis)):
            existe = db.session.query(Propia).filter(Propia.id == Publis[x].ids ).count()
                #ver si ese ID existe en recomendacion sino es un post propio
            if bool(existe):
                guardaPDF(Publis[x],finalDictionary,current_user)
                i = i + 1
            else:
                guardaRecomendacion(Publis[x],finalDictionary,current_user)
                i = i + 1

    return json.dumps(finalDictionary, indent = i)
                
@app.route('/GuardadosArticulosPaginados', methods=['GET'])
@token_required
def GuardadosArticulosPaginados(current_user):

    Publis = []
    offsetreal = 0
    limite=request.headers['limit']
    offsetreal = int(request.headers['offset'])*int(limite)
    
    
    todosGuardados=select([Guarda.id, Guarda.Usuario_Nicka ]).where(and_(Guarda.tipo==1 , Guarda.Usuario_Nicka == current_user)) .order_by(Guarda.id.desc()).limit(int(limite)).offset(int(offsetreal)).distinct()
    todosGuardados = db.session.execute(todosGuardados)
    

    for ids in todosGuardados:
        print("CURRENT USER", current_user , "muestra la pub de: ",ids.Usuario_Nicka )
        print("vamos: ", ids.id )
        guardarId(Publis,ids.id)

    if len(Publis) == 0:
        print("hola", " offset: ", offsetreal, "limite: ", limite)
        return jsonify({'fin': 'La lista se ha acabado no hay mas posts'})
    finalDictionary = {}
    i=0
    x=0
    for x in  range(len(Publis)):
            existe = db.session.query(Propia).filter(Propia.id == Publis[x].ids ).count()
                #ver si ese ID existe en recomendacion sino es un post propio
            if bool(existe):
                guardaPDF(Publis[x],finalDictionary,current_user)
                i = i + 1

    return json.dumps(finalDictionary, indent = i)

@app.route('/GuardadosRecomendacionesPaginados', methods=['GET'])
@token_required
def GuardadosRecomendacionesPaginados(current_user):

    Publis = []
    offsetreal = 0
    limite=request.headers['limit']
    offsetreal = int(request.headers['offset'])*int(limite)

    
    todosGuardados=select([Guarda.id ]).where(and_(Guarda.tipo==2 , Guarda.Usuario_Nicka == current_user)) .order_by(Guarda.id.desc()).limit(int(limite)).offset(int(offsetreal)).distinct()
    todosGuardados = db.session.execute(todosGuardados)
    for ids in todosGuardados:
        print("vamos: ", ids.id)
        guardarId(Publis,ids.id)

    if len(Publis) == 0:
        print("hola", " offset: ", offsetreal, "limite: ", limite)
        return jsonify({'fin': 'La lista se ha acabado no hay mas posts'})
    finalDictionary = {}
    i=0
    x=0
    for x in  range(len(Publis)):
            existe = db.session.query(Recomendacion).filter(Recomendacion.id == Publis[x].ids ).count()
                #ver si ese ID existe en recomendacion sino es un post propio
            if bool(existe):
                guardaRecomendacion(Publis[x],finalDictionary,current_user)
                i = i + 1

    return json.dumps(finalDictionary, indent = i)


@app.route('/HomePaginado', methods=['GET'])
@token_required
def HomePaginado(current_user):
    
    offsetreal = 0
    limite=request.headers['limit']
    offsetreal = int(request.headers['offset'])*int(limite)
    limitereal=  (int(request.headers['offset'])*int(limite)) + int(limite)
    Publis = []


    todosSiguiendo=Sigue.query.filter_by(Usuario_Nickb=current_user).all()#   order_by(Propia.id.desc()).limit(int(limite)).offset(int(offsetreal))
    for nick in todosSiguiendo:
        posts=select([Publicacion.id ]).where(Publicacion.Usuario_Nicka == nick.Usuario_Nicka ).order_by(Publicacion.id.desc()).limit(int(limitereal))#.offset(int(offsetreal))
        posts = db.session.execute(posts)    
        for posteos in posts:
            guardarId(Publis,posteos.id)


    
    #ordenar por id
    Publis.sort(key = customSort, reverse=True)

    Publis2=[]
    for i in range (int(offsetreal), int(offsetreal) + int(limite)):
        #print("x es = ", x , "i es: ", i ," offset: ", offsetreal, "limite: ", limite, "publis[i]: ", Publis[i])
        if i< len(Publis): 
            print("i es: ", i ,"len publis: ", len(Publis))
            Publis2.append(Publis[i])

    if len(Publis2) == 0:
        print("hola", " offset: ", offsetreal, "limite: ", limite)
        return jsonify({'fin': 'La lista se ha acabado no hay mas posts'})

    finalDictionary = {}
    i=0
    x=0
    for x in  range(len(Publis2)):
            existe = db.session.query(Propia).filter(Propia.id == Publis2[x].ids ).count()
                #ver si ese ID existe en recomendacion sino es un post propio
            #print(" postesos despues: ", Publis2[x].ids)
            if bool(existe):
                guardaPDF(Publis2[x],finalDictionary,current_user)
                i = i + 1
            else:
                guardaRecomendacion(Publis2[x],finalDictionary,current_user)
                i = i + 1

    return json.dumps(finalDictionary, indent = i)
            

def customSort(k):
    return k.ids



def cargarDatosPDFstr(pdfname,portadaname,id):
    pdf = select([Propia.pdf,Propia.portada]).where((Propia.id == id))
    resulta = db.session.execute(pdf)

    for a in resulta:
        pdfname=str(a.pdf)
        portadaname=str(a.portada)
    return pdfname,portadaname
def cargarDatosRecomendacionesstr(links,titulos,autores,id):
    recom = select([Recomendacion.link,Recomendacion.titulo,Recomendacion.autor]).where((Recomendacion.id == id))
    resulta = db.session.execute(recom)

    for a in resulta:
        links=str(a.link)
        titulos=str(a.titulo)
        autores=str(a.autor)
    return links,titulos,autores


@app.route('/Populares', methods=['GET'])
@token_required
def Populares(current_user):


# class Trata_pub_del_tema(db.Model):

#     id = db.Column(db.Integer, db.ForeignKey('publicacion.id'),primary_key=True)
#     tema = db.Column(db.String(50), db.ForeignKey('tematica.tema'),primary_key=True)

# class Prefiere(db.Model):

#     Usuario_Nicka = db.Column(db.String(20), db.ForeignKey('usuario.nick'),primary_key=True)
#     tema = db.Column(db.String(50), db.ForeignKey('tematica.tema'),primary_key=True)

    Publis = []
    limite=request.headers['limit']
    todosUsuarios = Usuario.query.all()
    for nicks in todosUsuarios:
        if nicks.nick != current_user:
            leSigue= db.session.query(Sigue).filter(and_(Sigue.Usuario_Nicka== 'nicks.nick' and Sigue.Usuario_Nickb== 'current_user')).first()
            if leSigue is None:
                preferidas = []
                if request.headers['tematicas']=="pref":
                    tema = select([Prefiere.tema]).where((Prefiere.Usuario_Nicka == current_user))
                    temas = db.session.execute(tema)
                    for row in temas:
                        preferidas.append(row.tema)
                else:
                    preferidas.append(request.headers['tematicas'])

                posts=""
                if request.headers['filtrado']!="":
                    search = "%{}%".format(request.headers['filtrado'])
                    posts =  db.session.query(Publicacion).filter(and_(Publicacion.descripcion.like(search), Publicacion.Usuario_Nicka == nicks.nick)).all()
                else:
                    posts=select([Publicacion.id ]).where(Publicacion.Usuario_Nicka == nicks.nick )
                    posts = db.session.execute(posts)  

                for posteos in posts:
                    pref = False
                    print("PREFERIDAS: ",preferidas )
                    for temas in preferidas:
                        
                        prefiere = Trata_pub_del_tema.query.filter_by(id=posteos.id ,tema= temas).first()
                        if prefiere:
                            print("si: ", posteos.id)
                            pref = True
                        else:
                            print("no: ", posteos.id, "tema: ", temas )

                    if pref ==True:
                        guardarId(Publis,posteos.id)
            # else:
            #     print(leSigue)
            #     print("este user: ", current_user , " sigue a este: ",nicks.nick  )



    Publis.sort(key = orderLikes, reverse=True)

    # for x in  range(len(Publis)):
    #     print("MEGUSTAS DE ID: ", Publis[x].ids ," gustas: ", Publis[x].Gustas )

    Publis2=[]
    for i in range (0, int(limite)):
        #print("x es = ", x , "i es: ", i ," offset: ", offsetreal, "limite: ", limite, "publis[i]: ", Publis[i])
        if i< len(Publis): 
            # print("i es: ", i ,"likes publis: ", Publis[i].Gustas)
            Publis2.append(Publis[i])

    if len(Publis2) == 0:
        # print("hola", "limite: ", limite)
        return jsonify({'fin': 'La lista se ha acabado no hay mas posts'})

    finalDictionary = {}
    i=0
    x=0
    for x in  range(len(Publis2)):
            existe = db.session.query(Propia).filter(Propia.id == Publis2[x].ids ).count()
                #ver si ese ID existe en recomendacion sino es un post propio
            #print(" postesos despues: ", Publis2[x].ids)
            if bool(existe):
                guardaPDF(Publis2[x],finalDictionary,current_user)
                i = i + 1
            else:
                guardaRecomendacion(Publis2[x],finalDictionary,current_user)
                i = i + 1

    return json.dumps(finalDictionary, indent = i)




@app.route('/PopularesRecomendaciones', methods=['GET'])
@token_required
def PopularesRecomendaciones(current_user):

    Publis = []
    limite=request.headers['limit']
    offsetreal = int(request.headers['offset'])*int(limite)
    paginaExplorados(Publis,current_user,request.headers['tematicas'],request.headers['filtrado'],2)



    Publis.sort(key = orderLikes, reverse=True)

    Publis2=[]
    for i in range (int(offsetreal), int(offsetreal) + int(limite)):
        #print("x es = ", x , "i es: ", i ," offset: ", offsetreal, "limite: ", limite, "publis[i]: ", Publis[i])
        if i< len(Publis): 
            print("i es: ", i ,"len publis: ", len(Publis))
            Publis2.append(Publis[i])

    if len(Publis2) == 0:
        print("hola", " offset: ", offsetreal, "limite: ", limite)
        return jsonify({'fin': 'La lista se ha acabado no hay mas posts'})

    finalDictionary = {}
    i=0
    x=0
    for x in  range(len(Publis2)):
        print("hola soy el id: ", Publis2[x].ids)
        guardaRecomendacion(Publis2[x],finalDictionary,current_user)
        i = i + 1

    return json.dumps(finalDictionary, indent = i)


@app.route('/PopularesArticulos', methods=['GET'])
@token_required
def PopularesArticulos(current_user):

    Publis = []
    limite=request.headers['limit']
    offsetreal = int(request.headers['offset'])*int(limite)
    paginaExplorados(Publis,current_user,request.headers['tematicas'],request.headers['filtrado'],1)


    Publis.sort(key = orderLikes, reverse=True)

    Publis2=[]
    for i in range (int(offsetreal), int(offsetreal) + int(limite)):
        #print("x es = ", x , "i es: ", i ," offset: ", offsetreal, "limite: ", limite, "publis[i]: ", Publis[i])
        if i< len(Publis): 
            print("i es: ", i ,"len publis: ", len(Publis))
            Publis2.append(Publis[i])

    if len(Publis2) == 0:
        print("hola", " offset: ", offsetreal, "limite: ", limite)
        return jsonify({'fin': 'La lista se ha acabado no hay mas posts'})


    finalDictionary = {}
    i=0
    x=0
    for x in  range(len(Publis2)):
        guardaPDF(Publis2[x],finalDictionary,current_user)
        i = i + 1

    return json.dumps(finalDictionary, indent = i)



@app.route('/Recientes', methods=['GET'])
@token_required
def Recientes(current_user):

    Publis = []
    limite=request.headers['limit']
    paginaExplorados(Publis,current_user,request.headers['tematicas'],request.headers['filtrado'],3)

    Publis.sort(key = orderRecientes, reverse=True)


    Publis2=[]
    for i in range (0, int(limite)):
        if i< len(Publis): 
            Publis2.append(Publis[i])

    if len(Publis2) == 0:
        return jsonify({'fin': 'La lista se ha acabado no hay mas posts'})

    finalDictionary = {}
    i=0
    x=0
    for x in  range(len(Publis2)):
            existe = db.session.query(Propia).filter(Propia.id == Publis2[x].ids ).count()

            if bool(existe):
                guardaPDF(Publis2[x],finalDictionary,current_user)
                i = i + 1
            else:
                guardaRecomendacion(Publis2[x],finalDictionary,current_user)
                i = i + 1

    return json.dumps(finalDictionary, indent = i)



@app.route('/RecientesRecomendaciones', methods=['GET'])
@token_required
def RecientesRecomendaciones(current_user):

    Publis = []
    limite=request.headers['limit']
    paginaExplorados(Publis,current_user,request.headers['tematicas'],request.headers['filtrado'],2)

    Publis.sort(key = orderRecientes, reverse=True)

    Publis2=[]
    for i in range (0, int(limite)):
        if i< len(Publis): 
            Publis2.append(Publis[i])

    if len(Publis2) == 0:
        return jsonify({'fin': 'La lista se ha acabado no hay mas posts'})

    finalDictionary = {}
    i=0
    x=0
    for x in  range(len(Publis2)):
        guardaRecomendacion(Publis2[x],finalDictionary,current_user)
        i = i + 1

    return json.dumps(finalDictionary, indent = i)

@app.route('/RecientesArticulos', methods=['GET'])
@token_required
def RecientesArticulos(current_user):

    Publis = []
    limite= int(request.headers['limit'])
    paginaExplorados(Publis,current_user,request.headers['tematicas'],request.headers['filtrado'],1)

    Publis.sort(key = orderRecientes, reverse=True)

    Publis2=[]
    for i in range (0, int(limite)):
        if i< len(Publis): 
            Publis2.append(Publis[i])

    if len(Publis2) == 0:
        return jsonify({'fin': 'La lista se ha acabado no hay mas posts'})

    finalDictionary = {}
    i=0
    x=0
    for x in  range(len(Publis2)):
        guardaPDF(Publis2[x],finalDictionary,current_user)
        i = i + 1

    return json.dumps(finalDictionary, indent = i)


def paginaExplorados(Publis,current_user,tematicas,filtrado,art):

    todosUsuarios = Usuario.query.all()
    for nicks in todosUsuarios:
        if nicks.nick != current_user:
            leSigue= db.session.query(Sigue).filter(and_(Sigue.Usuario_Nicka== 'nicks.nick' , Sigue.Usuario_Nickb== 'current_user')).first()
            if leSigue is None:
                preferidas = []
                if tematicas=="pref":
                    tema = select([Prefiere.tema]).where((Prefiere.Usuario_Nicka == current_user))
                    temas = db.session.execute(tema)
                    for row in temas:
                        preferidas.append(row.tema)
                else:
                    preferidas.append(tematicas)

                posts=""
                if filtrado!="":
                    search = "%{}%".format(filtrado)
                    posts =  db.session.query(Publicacion).filter(and_(Publicacion.descripcion.like(search), Publicacion.Usuario_Nicka == nicks.nick)).all()
                else:
                    posts=select([Publicacion.id ]).where(Publicacion.Usuario_Nicka == nicks.nick )
                    posts = db.session.execute(posts)  

                for posteos in posts:
                    pref = False
                    #print("PREFERIDAS: ",preferidas )
                    for temas in preferidas:
                        
                        prefiere = db.session.query(Trata_pub_del_tema).filter(and_(Trata_pub_del_tema.id==posteos.id ,Trata_pub_del_tema.tema== temas)).first()
                        if prefiere:
                            pref = True

                    if pref ==True:
                        existeP = db.session.query(Propia).filter(Propia.id == posteos.id ).count()
                        existeR = db.session.query(Recomendacion).filter(Recomendacion.id == posteos.id ).count()
                        if bool(existeP and art==1):
                            guardarId(Publis,posteos.id)
                        elif bool(existeR and art==2):
                            guardarId(Publis,posteos.id)
                        elif bool(art==3):
                            guardarId(Publis,posteos.id)
                        

@app.route('/infoPost', methods=['GET'])
@token_required
def infoPost(current_user):
    Publis = []
    guardarId(Publis,request.headers['id'])
    finalDictionary = {}
    i=0
    x=0
    for x in  range(len(Publis)):
            existe = db.session.query(Propia).filter(Propia.id == Publis[x].ids ).count()
                #ver si ese ID existe en recomendacion sino es un post propio
            #print(" postesos despues: ", Publis2[x].ids)
            if bool(existe):
                guardaPDF(Publis[x],finalDictionary,current_user)
                i = i + 1
            else:
                guardaRecomendacion(Publis[x],finalDictionary,current_user)
                i = i + 1

    return json.dumps(finalDictionary, indent = i)



@app.route('/notificaciones', methods=['GET'])
@token_required
def verNotificaciones(current_user):

    offsetreal = 0
    limite=request.headers['limit']
    offsetreal = int(request.headers['offset'])*int(limite)
    notiVec = []
    notis=Notificaciones.query.filter_by(nickReceptor=current_user).order_by(Notificaciones.id.desc())
    for r in notis:
        x = select([ Usuario.foto_de_perfil]).where((Usuario.nick == r.nickEmisor))
        resultb = db.session.execute(x)
        for a in resultb:
            if current_user != r.nickEmisor:
                if r.tipo ==1:
                    notiVec.append(meGusta(r.id,r.nickEmisor,r.tipo,a.foto_de_perfil,r.timestamp,r.idPubli))
                elif r.tipo ==2:
                    notiVec.append(comenta(r.id,r.nickEmisor,r.tipo,a.foto_de_perfil,r.timestamp,r.comentario,r.idPubli))
                else:
                    notiVec.append(Notificacion(r.id,r.nickEmisor,r.tipo,a.foto_de_perfil,r.timestamp))



    notiVec2=[]
    for i in range (int(offsetreal), int(offsetreal) + int(limite)):
        #print("x es = ", x , "i es: ", i ," offset: ", offsetreal, "limite: ", limite, "publis[i]: ", Publis[i])
        if i< len(notiVec): 
            print("i es: ", i ,"len publis: ", len(notiVec))
            notiVec2.append(notiVec[i])

    if len(notiVec2) == 0:
        return jsonify({'fin': 'La lista se ha acabado no hay mas notis'})

    finalDictionary = {}
    i=0
    for noti in notiVec2:
        foto_de_perfil_Completo= 'http://51.255.50.207:5000/display/' + str(noti.foto_de_perfil)
        if noti.tipo==1:
            finalDictionary[noti.ids] = { 'tipo': int(noti.tipo),'nickEmisor' : str(noti.nick) ,'foto_de_perfil' : str(foto_de_perfil_Completo), 'comentario': "",'idPubli' : int(noti.idPub)}
        elif noti.tipo==2:
            finalDictionary[noti.ids] = { 'tipo': int(noti.tipo),'nickEmisor' : str(noti.nick) ,'foto_de_perfil' : str(foto_de_perfil_Completo), 'comentario': str(noti.comentario), 'idPubli': int(noti.idPub)}
        else:
            finalDictionary[noti.ids] = { 'tipo': int(noti.tipo),'nickEmisor' : str(noti.nick) ,'foto_de_perfil' : str(foto_de_perfil_Completo), 'comentario': "", 'idPubli': ""}
        i=i+1

    return json.dumps(finalDictionary, indent = i)


# Funcion para cargar todos los chat que un usuario tiene abierto

@app.route("/chat", methods=['GET'])
@token_required
def load_chat(current_user):
    current_user = request.headers['current_user']
    list_users = []

    users = chatRoom.query.filter_by(user1 = current_user).all()                # Cargamos las salas donde el usuario figura como 1
    for user in users:
        if user.user1 == current_user:
            list_users.append(user.user2)
        else:
            list_users.append(user.user1)

    users = chatRoom.query.filter_by(user2 = current_user).all()                # Cargamos las salas donde el usuario figura como 2
    for user in users:
        if user.user1 == current_user:
            list_users.append(user.user2)
        else:
            list_users.append(user.user1)
    
    print(list_users)    
    return jsonify(list_users)

@app.route("/new_chat",methods=['GET'])
def new_chat():
    
    userOrigin = request.headers['userOrigin']              # Cambiar al metodo de recibir el usuario origen.
    userDest = request.headers['userDest']                  # Cambiar la metodo de recibir el usuario destino.
    print(userOrigin)
    print(userDest)
    randomNumber = sample(range(10,99999),1)
    print(randomNumber[0])

    if check_room(userOrigin,userDest):
        NewRoom = chatRoom(roomid = randomNumber[0],user1=userOrigin, user2=userDest)
        db.session.add(NewRoom)
        db.session.commit()
        return str(randomNumber[0])
    else:
        roomId = getRoom(userOrigin,userDest)
        return str(roomId)

# Cargamos las conversaciones de una sala

@app.route("/private/<string:roomId>",methods=['GET'])
def index(roomId):
     
    print('Se ha unido a la sala {}'.format(roomId))
    
    messages = Chat.query.filter_by(room = roomId).order_by(Chat.created_at.desc()).all()
    messagelist = []
    for i in messages:
        message = {
            'nick' : i.nick,
            'message' : i.message,
            'created_at' : i.created_at
        }
        messagelist.append(message)
 
    return jsonify(messagelist)

# Comprobamos que no exista una room con ambos usuarios dentro

def check_room(userOrigin,userDest):
    room = chatRoom.query.filter_by(user1 = userOrigin , user2=userDest).first()
    if room is None:
        room = chatRoom.query.filter_by(user2 = userOrigin , user1=userDest).first()
        if room is None:
            return True
        else: 
            return False
    else:
        return False

# Devuelve el sid del usuario que se conecta
"""
def checkReceiver(sid):
    receiver = UserSid.query.filter_by(Sid=sid).first()
    return receiver.User
"""
def getRoom(userOrigin, userDest):
    chat = chatRoom.query.filter_by(user1 = userOrigin , user2=userDest).first()
    if chat is None:
        chat = chatRoom.query.filter_by(user2 = userOrigin , user1=userDest).first()
        return chat.roomid
    else:
        return chat.roomid



def orderLikes(k):
    
    return k.Gustas


def orderRecientes(k):
    
    return k.timestamps


def check_email(email):

    regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'

    if(regex.search(regex,email)):
        return True
    else:
        return False

# Contraseñas de entre 8 y 32 carácteres.

def check_password(password):

    regex = '^(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])(?=.*[*.!@$%^&(){}[]:;<>,.?/~_+-=|\]).{8,32}$'

    if(regex.search(regex,password)):
        return True
    else:
        return False

if __name__ == '__main__':
    app.run(debug=True)