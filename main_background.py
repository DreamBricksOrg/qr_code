import os
import logging
import time
import threading
from pathlib import Path

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

from evdev import InputDevice, categorize, ecodes, list_devices
import select

MACHINE_COMMAND = 22
COMMAND_DURATION = 2
USB_PATHS = ["/media/pi", "/mnt/usb", "/mnt/d", "/mnt/e", "/mnt/f", "/mnt/g", "/mnt/h"]
VALID_FILE = "list_valids.txt"
USED_FILE = "list_useds.txt"

if GPIO:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(MACHINE_COMMAND, GPIO.OUT)

logging.basicConfig(
    filename='scanner.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger()

def start_game():
    if GPIO:
        GPIO.output(MACHINE_COMMAND, GPIO.HIGH)
        time.sleep(COMMAND_DURATION)
        GPIO.output(MACHINE_COMMAND, GPIO.LOW)
    else:
        logger.warning("GPIO não disponível. Comando não enviado.")

def read_list(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return [linha.strip() for linha in f if linha.strip()]

def save_list(path, data_list):
    with open(path, "w") as f:
        for item in data_list:
            f.write(item + "\n")

def validate_code(code):
    if not code.isdigit() or len(code) != 15:
        return False
    base_digits = list(map(int, code[:14]))
    checksum_digit = int(code[-1])
    checksum = sum((i + 1) * num for i, num in enumerate(base_digits)) % 10
    return checksum == checksum_digit

def process_code(code):
    if not validate_code(code):
        logger.error(f"Código {code} inválido por verificação.")
        return

    valids = read_list(VALID_FILE)
    #useds = read_list(USED_FILE)

    if code in valids:
        logger.info(f"Código {code} válido.")
        #valids.remove(code)
        #useds.append(code)
        #save_list(VALID_FILE, valids)
        #save_list(USED_FILE, useds)
        start_game()
    #elif code in useds:
        #logger.warning(f"Código {code} já foi usado.")
    else:
        logger.error(f"Código {code} não encontrado nas listas.")

def process_new_list(path):
    with open(path, "r") as f:
        new_codes = [line.strip() for line in f if line.strip()]
    if new_codes:
        logger.info(f"Adicionando {len(new_codes)} itens da nova lista.")
        valids = read_list(VALID_FILE)
        updateds = list(set(valids + new_codes))
        save_list(VALID_FILE, updateds)
        os.remove(path)

def usb_monitor():
    logger.info("Monitor de USB iniciado.")
    while True:
        try:
            for base in USB_PATHS:
                path = Path(base)
                if not path.exists():
                    continue
                try:
                    for item in path.iterdir():
                        if item.name == "new_codes.txt" and item.is_file():
                            logger.info(f"Arquivo detectado: {item}")
                            process_new_list(str(item))
                except Exception as e:
                    logger.warning(f"Erro acessando {base}: {e}")
            time.sleep(10)
        except Exception as e:
            logger.error(f"Erro no monitor de USB: {e}")
            time.sleep(10)

# --------- Captura de Teclado com evdev ---------
typed_code = []

def listen_keyboard_evdev():
    devices = [InputDevice(path) for path in list_devices()]
    scanner = None

    for dev in devices:
        if 'barcode' in dev.name.lower() or 'scanner' in dev.name.lower() or 'henex' in dev.name.lower():
            scanner = dev
            break

    if not scanner:
        logger.error("Scanner não encontrado.")
        return

    logger.info(f"Escutando scanner: {scanner.name} ({scanner.path})")

    typed_code = []

    while True:
        r, _, _ = select.select([scanner], [], [])
        for event in scanner.read():
            if event.type == ecodes.EV_KEY:
                key_event = categorize(event)
                if key_event.keystate == key_event.key_down:
                    keycode = key_event.keycode
                    if isinstance(keycode, list):
                        keycode = keycode[0]

                    if keycode.startswith('KEY_'):
                        char = keycode[4:]
                        if char.isdigit():
                            typed_code.append(char)
                        elif char == 'ENTER':
                            code_str = ''.join(typed_code)
                            typed_code.clear()
                            if code_str:
                                print(f"\nCódigo lido: {code_str}")
                                process_code(code_str)

# --------------------------------------------------

def main():
    logger.info("Sistema iniciado. Escutando teclado evdev...")
    print("\nSistema pronto. Escaneie ou digite o código (pressione Enter para enviar)...")
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Sistema finalizado manualmente.")
            print("\nEncerrando...")
            break
        except Exception as e:
            logger.error(f"Erro inesperado no loop principal: {e}")

if __name__ == "__main__":
    threading.Thread(target=usb_monitor, daemon=True).start()
    threading.Thread(target=listen_keyboard_evdev, daemon=True).start()
    main()
