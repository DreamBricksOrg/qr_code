import os
import logging

# Configuração básica do logger
logging.basicConfig(
    filename='scanner.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger()

VALID_FILE = "list_valids.txt"
USED_FILE = "list_useds.txt"

def read_list(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return [linha.strip() for linha in f if linha.strip()]

def save_list(path, data_list):
    with open(path, "w") as f:
        for item in data_list:
            f.write(item + "\n")

def process_code(code):
    valids = read_list(VALID_FILE)
    useds = read_list(USED_FILE)

    if code in valids:
        logger.info(f"Código {code} válido.")
        valids.remove(code)
        useds.append(code)
        save_list(VALID_FILE, valids)
        save_list(USED_FILE, useds)
    elif code in useds:
        logger.warning(f"Código {code} já foi usado.")

    else:
        logger.error(f"Código {code} inválido.")

def usb_new_list():
    mounts = [
        "/media/pi",
        "/mnt/usb",
        "/mnt/e",
        "/mnt/f",
        "/mnt/d"
    ]

    for base in mounts:
        if not os.path.exists(base):
            continue
        for device in os.listdir(base):
            path = os.path.join(base, device, "new_codes.txt")
            if os.path.isfile(path):  # WSL pode não tratar como pasta
                process_new_list(path)
                return

            new_path = os.path.join(base, "new_codes.txt")
            if os.path.isfile(new_path):
                process_new_list(new_path)
                return

def process_new_list(path):
    with open(path, "r") as f:
        new_codes = [line.strip() for line in f if line.strip()]
    if new_codes:
        logger.info(f"Adicionando {len(new_codes)} itens da nova lista.")
        valids = read_list(VALID_FILE)
        updateds = list(set(valids + new_codes))
        save_list(VALID_FILE, updateds)
        os.remove(path)

def main():
    logger.info("Sistema iniciado. Aguardando QR Codes...")
    print("\nInciando...")
    while True:
        try:
            # usb_new_list()  # Verifica se há nova lista no pen drive
            code = input().strip()
            # print(f"\nCode: {code}")
            process_code(code)
        except KeyboardInterrupt:
            logger.info("Sistema finalizado manualmente.")
            print("\nEncerrando...")
            break
        except Exception as e:
            logger.error(f"Erro inesperado no loop principal: {e}")

if __name__ == "__main__":
    main()
