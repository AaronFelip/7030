from flask import Flask, render_template, redirect, url_for, request, g, session
from functools import wraps
from database import Database


regex = r"[A-Za-z0-9#$%&'*+/=?@]{8,}" #possiblement incomplet


app = Flask(__name__, static_url_path='', static_folder='static')


# Dans config.py ou .env pas ici
app.secret_key = 'ebb506dc18624cb16aa029f6c20af44a'

#print(secrets.token_hex(16))



def connection_requise(f):
    @wraps(f)
    def decorated_fucntion(*args, **kwargs):
        if 'id' not in session:
            return redirect(url_for('login')), 302
        return f(*args, **kwargs)
    return decorated_fucntion


def valider_courriel_existe(courriel):
    return get_db().courriel_existe(courriel)


def valider_courriel(courriel, validation_courriel):
    return courriel == validation_courriel



def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        g._database = Database()
    return g._database


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close_connection()


@app.route('/')
def index():
    title = "MGL7030 PROJET SESSION"
    return render_template('index.html',
                           title=title), 200




@app.route('/signin', methods=['GET', 'POST'])
def signin():
    title = "Mon site veuillez-vous inscrires."
    if request.method == 'GET':
        return render_template("sign-in.html", title=title), 200

    form_data = { 'nom' : request.form.get('nom').strip(),
                  'prenom' : request.form.get('prenom').strip(),
                  'courriel' : request.form.get('courriel').strip(),
                  'validation-courriel' : request.form.get('validation-courriel').strip(),
                  'mdp' : request.form.get('mdp'),
                  }
    erreurs = {}

    if not all(form_data.values()):
        erreurs["message_erreur"] = "Tous les champs doivent être remplis."

    if valider_courriel_existe(form_data['courriel']):
        erreurs["courriel_erreur"] = "Ce courriel existe déjà."


    try:
        get_db().creer_utilisateur(
            form_data['nom'],
            form_data['prenom'],
            form_data['courriel'],
            form_data['mdp'],
        )
    except Exception as e:
        erreurs["db_erreur"] = "Une erreur est survenu durant l'inscription"

        return render_template("sign-in.html",
                               title=title,
                               **erreurs,
                               **form_data), 500

    return redirect(url_for("index")), 302


@app.route('/login', methods=['GET', 'POST'])
def login():
    title = "login"
    if request.method == 'GET':
        if 'id' in session:
            return redirect(url_for('index'))
        return render_template("login.html",title=title), 200

    courriel = request.form.get('courriel', ' ').strip()
    mdp = request.form.get('mdp')

    erreurs = {}

    if not courriel or not mdp:
        erreurs['message_erreur'] = "Tous les champs"
        return render_template("login.html",
                               title=title,
                               courriel=courriel,
                               **erreurs), 400

    utilisateur = get_db().verifier_utilisateur(courriel, mdp)

    if utilisateur is None:
        erreurs['message_errreur'] = "Ce courriel ou mot de passe est incvorrect"
        return render_template("login.html",
                               title=title,
                               courriel=courriel,
                               **erreurs), 401

    session.clear()
    session['id'] = utilisateur['id']
    session['nom'] = utilisateur['nom']
    session['prenom'] = utilisateur['prenom']
    session['courriel'] = utilisateur['courriel']

    return redirect(url_for('index')), 302



@app.route('/logout')
@connection_requise
def logout():
    session.clear()
    return redirect(url_for('index')), 302



if __name__ == '__main__':
    app.run()
