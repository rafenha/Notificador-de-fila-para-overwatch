"""
Cria a imagem de referência do aviso "Partida encontrada" no SEU PC.

Duas formas de usar:

1) A partir de um print que você já tirou (recomendado):
       python capture_reference.py --image meu_print.png
   Dica: quando a partida for encontrada, aperte Win+Shift+S (ou a tecla
   PrintScreen) e salve o print.

2) Capturando a tela depois de uma contagem:
       python capture_reference.py --delay 10
   Útil se você já está com o aviso na tela quando o tempo acabar.

Depois, selecione com o mouse só a área do aviso e aperte ENTER (ou ESPAÇO).
Aperte C para cancelar.
"""

import argparse
import sys
import time
from pathlib import Path

import cv2
import mss
import numpy as np

OUTPUT = Path(__file__).resolve().parent / "reference" / "match_found.png"


def main() -> None:
    parser = argparse.ArgumentParser(description="Captura a imagem de referência")
    parser.add_argument("--image", help="caminho de um print já existente")
    parser.add_argument("--delay", type=int, default=5, help="segundos antes de capturar a tela")
    parser.add_argument("--monitor", type=int, default=1, help="número do monitor (1 = principal)")
    args = parser.parse_args()

    if args.image:
        img = cv2.imread(args.image)
        if img is None:
            sys.exit(f"Não consegui abrir a imagem: {args.image}")
    else:
        print(f"Capturando a tela em {args.delay} segundos...")
        time.sleep(args.delay)
        with mss.mss() as sct:
            shot = np.array(sct.grab(sct.monitors[args.monitor]))
        img = cv2.cvtColor(shot, cv2.COLOR_BGRA2BGR)

    print("Selecione a área do aviso e aperte ENTER. (C para cancelar)")
    roi = cv2.selectROI("Selecione o aviso de Partida encontrada", img, showCrosshair=False)
    cv2.destroyAllWindows()

    x, y, w, h = map(int, roi)
    if w == 0 or h == 0:
        sys.exit("Nenhuma área selecionada.")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(OUTPUT), img[y : y + h, x : x + w])
    print(f"Referência salva em: {OUTPUT}")


if __name__ == "__main__":
    main()
