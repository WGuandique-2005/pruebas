from flask import Flask, render_template, Response, request, redirect, url_for
import cv2
from threading import Lock
from vocales import Camara  
import time

app = Flask(__name__)
app.config['DEBUG'] = True

# Variables globales
camara = None
camera_active = False
camara_lock = Lock()

def GenerarFrame():
    """Generar flujo de video con detección de letras"""
    global camara
    while True:
        with camara_lock:  # Bloquea la cámara para evitar conflictos
            if camara and camera_active:
                ret, frame = camara.captura.read()
                if not ret:
                    break
                frame = cv2.flip(frame, 1)  # Modo espejo
                
                # Procesar el frame y detectar letras
                frame, letra_detectada = camara.ProcesarFrame(frame, evaluar_dedos=True)
                
                # Mostrar la vocal propuesta en el frame
                if letra_detectada:
                    camara.CompararVocal(letra_detectada)
                    texto_respuesta = f"Letra detectada: {letra_detectada}. Respuesta: {camara.respuesta_vocal}"
                else:
                    texto_respuesta = "No se detectó ninguna letra."

                cv2.putText(frame, texto_respuesta, (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
                
                # Codificar el frame para transmisión
                ret, jpeg = cv2.imencode('.jpg', frame)
                if ret:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
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
    return render_template('nivelPri.html', camera_active=camera_active)

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
    """Activar o desactivar la cámara."""
    global camera_active, camara
    with camara_lock:
        if camera_active:
            camera_active = False
            camara = None
            print("Cámara desactivada")
        else:
            camera_active = True
            camara = Camara()
            print("Cámara activada")
    return redirect(url_for(page))

if __name__ == '__main__':
    app.run(debug=False)