import RPi.GPIO as GPIO
import time

# Configurações da GPIO
GPIO.setmode(GPIO.BCM)       # Usa o número da GPIO (não o número do pino físico)
GPIO.setup(22, GPIO.OUT)     # Configura a GPIO 22 como saída

try:
    print("Enviando sinal HIGH por 2 segundos...")
    GPIO.output(22, GPIO.HIGH)  # Sinal HIGH (3.3V)
    time.sleep(2)               # Espera 2 segundos
    GPIO.output(22, GPIO.LOW)   # Sinal LOW (0V)
    print("Sinal desligado.")
finally:
    GPIO.cleanup()              # Limpa a configuração da GPIO
