import cv2
import mediapipe as mp
import random

# Clase de la cámara
class Camara:
    def __init__(self, cam_id=0, max_num_hands=1, min_detection_confidence=0.9):
        # Inicializar captura de video
        self.captura = cv2.VideoCapture(cam_id, cv2.CAP_DSHOW)
        if not self.captura.isOpened():
            raise ValueError("No se pudo acceder a la cámara")

        # Inicializar Mediapipe y utilidades de dibujo
        self.mp_mano = mp.solutions.hands
        self.mano = self.mp_mano.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence
        )
        self.mp_dibujo = mp.solutions.drawing_utils
        self.letra_propuesta = None
        self.respuesta_letra = None
        
    def liberar_recursos(self):
        """Liberar recursos de la cámara y cerrar ventanas."""
        if self.captura.isOpened():
            self.captura.release()
        cv2.destroyAllWindows()
        
    def ElegirLetra(self):
        # Escoger una letra aleatoria del abecedario
        letras = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        self.letra_propuesta = random.choice(letras)
        return self.letra_propuesta
    
    def CompararLetra(self, letra_detectada):
        # Comparar la letra detectada con la letra propuesta
        if letra_detectada == self.letra_propuesta:
            self.respuesta_letra = "¡Correcta!"
        else:
            self.respuesta_letra = "Incorrecta :("
    
    def DetectarDedos(self, mano_landmarks, alto, ancho):
        # Obtener landmarks clave para detección
        nudo_pulgar = mano_landmarks.landmark[2]
        punta_pulgar = mano_landmarks.landmark[4]
        nudo_indice = mano_landmarks.landmark[6]
        punta_indice = mano_landmarks.landmark[8]
        nudo_mayor = mano_landmarks.landmark[10]
        punta_mayor = mano_landmarks.landmark[12]
        nudo_anular = mano_landmarks.landmark[14]
        punta_anular = mano_landmarks.landmark[16]
        nudo_meñique = mano_landmarks.landmark[18]
        punta_meñique = mano_landmarks.landmark[20]

        # Calcular si los dedos están doblados o extendidos
        dedos = {
            "pulgar": punta_pulgar.y < nudo_pulgar.y,
            "indice": punta_indice.y < nudo_indice.y,
            "mayor": punta_mayor.y < nudo_mayor.y,
            "anular": punta_anular.y < nudo_anular.y,
            "meñique": punta_meñique.y < nudo_meñique.y,
        }

        # Diccionario con las reglas para cada letra
        condiciones = {
            "A": lambda: all(not dedos[d] for d in dedos),  # Puño cerrado
            "B": lambda: all(dedos[d] for d in dedos if d != "pulgar"),  # Todos los dedos extendidos excepto el pulgar
            "C": lambda: all(not dedos[d] for d in dedos if d != "pulgar") and dedos["pulgar"],
            "D": lambda: dedos["indice"] and not dedos["mayor"] and not dedos["anular"] and not dedos["meñique"],
            "E": lambda: not dedos["indice"] and not dedos["mayor"] and not dedos["anular"] and not dedos["meñique"],
            "F": lambda: dedos["pulgar"] and dedos["indice"] and not dedos["mayor"] and not dedos["anular"],
            "G": lambda: dedos["pulgar"] and not dedos["indice"] and not dedos["mayor"],
            "H": lambda: dedos["indice"] and dedos["mayor"] and not dedos["anular"],
            "I": lambda: not dedos["pulgar"] and not dedos["indice"] and not dedos["mayor"],
            "J": lambda: dedos["pulgar"] and not dedos["indice"] and dedos["meñique"],
            "K": lambda: dedos["indice"] and dedos["mayor"] and not dedos["anular"] and not dedos["meñique"],
            "L": lambda: dedos["pulgar"] and dedos["indice"] and not dedos["mayor"],
            "M": lambda: all(not dedos[d] for d in ["indice", "mayor", "anular"]),
            "N": lambda: dedos["indice"] and not dedos["mayor"],
            "O": lambda: all(dedos[d] for d in dedos),
            "P": lambda: dedos["pulgar"] and not dedos["indice"] and dedos["mayor"],
            "Q": lambda: dedos["pulgar"] and dedos["meñique"],
            "R": lambda: dedos["indice"] and dedos["mayor"] and not dedos["anular"],
            "S": lambda: all(not dedos[d] for d in dedos),
            "T": lambda: dedos["pulgar"] and not dedos["indice"],
            "U": lambda: dedos["indice"] and dedos["mayor"] and not dedos["anular"] and not dedos["meñique"],
            "V": lambda: dedos["indice"] and dedos["mayor"] and not dedos["anular"] and not dedos["meñique"],
            "W": lambda: dedos["indice"] and dedos["mayor"] and dedos["anular"] and not dedos["meñique"],
            "X": lambda: dedos["indice"] and not dedos["mayor"],
            "Y": lambda: dedos["pulgar"] and dedos["meñique"],
            "Z": lambda: not dedos["pulgar"] and dedos["indice"],
        }

        # Detectar la letra basada en las condiciones
        for letra, condicion in condiciones.items():
            if condicion():
                return letra
        return "no reconocida"
    
    def ProcesarFrame(self, frame, evaluar_dedos=False):
        # Dimensiones del frame
        alto, ancho, _ = frame.shape

        # Convertir el frame a RGB para Mediapipe
        color = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resultado = self.mano.process(color)

        if self.letra_propuesta is None:
            self.letra_propuesta = self.ElegirLetra()
        cv2.putText(frame, f"Letra propuesta: {self.letra_propuesta}", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        letra_detectada = None
        if resultado.multi_hand_landmarks:
            for mano_landmarks in resultado.multi_hand_landmarks:
                self.mp_dibujo.draw_landmarks(frame, mano_landmarks, self.mp_mano.HAND_CONNECTIONS)

                # Si está habilitada la evaluación de dedos, detectar la letra
                if evaluar_dedos:
                    letra_detectada = self.DetectarDedos(mano_landmarks, alto, ancho)
        return frame, letra_detectada

# Ejecutar el programa
if __name__ == "__main__":
    camara = Camara()

    try:
        while True:
            ret, frame = camara.captura.read()
            if not ret:
                print("No se pudo leer el frame")
                break

            frame = cv2.flip(frame, 1)  # Modo espejo
            frame, letra_detectada = camara.ProcesarFrame(frame, evaluar_dedos=True)

            # Mostrar resultados en pantalla
            cv2.putText(
                frame,
                f"Letra detectada: {letra_detectada}",
                (50, 200),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 0, 0),
                2,
            )
            cv2.putText(
                frame,
                "Presiona Enter para enviar tu respuesta",
                (50, 250),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (255, 0, 0),
                2,
            )
            cv2.imshow("Detección de letras", frame)

            if cv2.waitKey(1) == 13:  # Tecla Enter
                if letra_detectada is not None:
                    camara.CompararLetra(letra_detectada)
                    print(f"Tu respuesta fue: {letra_detectada}. Respuesta: {camara.respuesta_letra}")
                else:
                    print("No se detectó ninguna letra")
                break
    except Exception as e:
        print(f"Error: {e}")
    finally:
        camara.liberar_recursos()
