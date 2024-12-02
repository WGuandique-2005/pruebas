from flask import Flask, render_template, Response, request, redirect, url_for
import cv2
from mano import *
import time
from threading import Lock

app = Flask(__name__)
app.config['DEBUG'] = True

# Variables globales
camara = None
camera_active = False

# Crear un Lock global
camara_lock = Lock()

def GenerarFrame():
    global camara
    while True:
        with camara_lock:  # Asegura que solo un hilo acceda a la cámara a la vez
            if camara and camera_active:
                ret, frame = camara.captura.read()
                if not ret:
                    break
                frame = cv2.flip(frame, 1)  # Modo espejo
                frame = camara.ProcesarFrame(frame)
                ret, jpeg = cv2.imencode('.jpg', frame)
                if ret:
                    frame_bytes = jpeg.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/grupo')
def pag1():
    return render_template('grupo.html')

@app.route('/jugar')
def pag2():
    return render_template('jugar.html')

@app.route('/letras')
def pag3():
    return render_template('letras.html')

@app.route('/selcNivel')
def pag4():
    return render_template('selecNivel.html')

@app.route('/redirect', methods=['POST'])
def redirect_level():
    nivel = request.form.get('nivel')
    if nivel == 'principiante':
        return redirect(url_for('pag5'))
    elif nivel == 'intermedio':
        return redirect(url_for('pag6'))
    elif nivel == 'avanzado':
        return redirect(url_for('pag7'))
    else:
        return redirect(url_for('index'))

@app.route('/nivelPri')
def pag5():
    return render_template('nivelPri.html')

@app.route('/nivelMed')
def pag6():
    return render_template('nivelMed.html')

@app.route('/nivelAvan')
def pag7():
    return render_template('nivelAvan.html')

@app.route('/video')
def video():
    return Response(GenerarFrame(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Ruta para alternar la cámara
@app.route('/toggle_camera/<page>', methods=['POST'])
def toggle_camera(page):
    global camera_active, camara
    if camera_active:
        # Desactivar cámara
        camera_active = False
        if camara:
            camara = None
        print("Cámara desactivada")
    else:
        # Activar cámara
        camera_active = True
        camara = Camara()  # Iniciar la cámara
        print("Cámara activada")
    
    # Redirigir a la misma página en la que estaba
    return redirect(url_for(page))  # Redirige a la página actual

if __name__ == '__main__':
    app.run(debug=False)