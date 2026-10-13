"""
Overwatch Queue Notifier
------------------------
Observa a tela do PC e envia uma notificação para o celular quando o aviso
de "Partida encontrada" aparece.

O script apenas LÊ a imagem da tela (captura em memória, nada é salvo em disco).
Não acessa a memória do jogo e não automatiza nenhuma ação.
Projeto não afiliado à Blizzard Entertainment.

Uso:
    python overwatch_notifier.py            # inicia o monitoramento
    python overwatch_notifier.py --test     # só envia uma notificação de teste
    python overwatch_notifier.py --debug    # mostra a pontuação de similaridade ao vivo
"""

import argparse
import json
import sys
import time
from pathlib import Path

import cv2
import mss
import numpy as np
import requests

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"

DEFAULTS = {
    "provider": "ntfy",              
    "ntfy_topic": "",
    "telegram_token": "",
    "telegram_chat_id": "",
    "reference_image": "reference/match_found.png",
    "monitor": 1,                    
    "scales": [0.8, 0.9, 1.0, 1.1, 1.2],
    "work_scale": 0.5,               
    "cooldown": 60,                 
    "message": "Partida encontrada! Volte para o Overwatch e aceite.",
}


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        sys.exit(
            "config.json não encontrado.\n"
            "Copie config.example.json para config.json e preencha seus dados."
        )
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        user_cfg = json.load(f)
    cfg = {**DEFAULTS, **user_cfg}

    if cfg["provider"] == "ntfy" and not cfg["ntfy_topic"]:
        sys.exit("Defina 'ntfy_topic' no config.json.")
    if cfg["provider"] == "telegram" and not (
        cfg["telegram_token"] and cfg["telegram_chat_id"]
    ):
        sys.exit("Defina 'telegram_token' e 'telegram_chat_id' no config.json.")
    if cfg["provider"] not in ("ntfy", "telegram"):
        sys.exit("'provider' deve ser 'ntfy' ou 'telegram'.")
    return cfg


def send_notification(cfg: dict, message: str) -> bool:
    """Envia a notificação para o celular. Retorna True se deu certo."""
    try:
        if cfg["provider"] == "ntfy":
            r = requests.post(
                f"https://ntfy.sh/{cfg['ntfy_topic']}",
                data=message.encode("utf-8"),
                headers={
                    "Title": "Overwatch - Partida encontrada",
                    "Priority": "urgent",
                    "Tags": "video_game",
                },
                timeout=10,
            )
        else:
            r = requests.post(
                f"https://api.telegram.org/bot{cfg['telegram_token']}/sendMessage",
                json={"chat_id": cfg["telegram_chat_id"], "text": message},
                timeout=10,
            )
        r.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"[erro] Falha ao enviar notificação: {e}")
        return False


def load_template(cfg: dict) -> np.ndarray:
    path = BASE_DIR / cfg["reference_image"]
    if not path.exists():
        sys.exit(
            f"Imagem de referência não encontrada: {path}\n"
            "Rode primeiro: python capture_reference.py"
        )
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        sys.exit(f"Não foi possível ler a imagem: {path}")
    ws = cfg["work_scale"]
    if ws != 1.0:
        img = cv2.resize(img, None, fx=ws, fy=ws, interpolation=cv2.INTER_AREA)
    return img


def grab_gray(sct: mss.mss, monitor: dict, work_scale: float) -> np.ndarray:
    """Captura o monitor, converte para cinza e reduz. Tudo em memória."""
    shot = np.array(sct.grab(monitor))  # BGRA
    gray = cv2.cvtColor(shot, cv2.COLOR_BGRA2GRAY)
    if work_scale != 1.0:
        gray = cv2.resize(
            gray, None, fx=work_scale, fy=work_scale, interpolation=cv2.INTER_AREA
        )
    return gray


def best_score(screen: np.ndarray, template: np.ndarray, scales: list) -> float:
    """Template matching em várias escalas; devolve a melhor similaridade."""
    best = 0.0
    for s in scales:
        t = cv2.resize(template, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        if t.shape[0] >= screen.shape[0] or t.shape[1] >= screen.shape[1]:
            continue
        result = cv2.matchTemplate(screen, t, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        best = max(best, float(max_val))
    return best


def main() -> None:
    parser = argparse.ArgumentParser(description="Overwatch Queue Notifier")
    parser.add_argument("--test", action="store_true", help="envia uma notificação de teste e sai")
    parser.add_argument("--debug", action="store_true", help="mostra a pontuação ao vivo")
    args = parser.parse_args()

    cfg = load_config()

    if args.test:
        ok = send_notification(cfg, "Teste: o notificador está funcionando!")
        print("Notificação de teste enviada." if ok else "Falha no envio.")
        return

    template = load_template(cfg)

    sct = mss.mss()
    if cfg["monitor"] >= len(sct.monitors):
        sys.exit(
            f"Monitor {cfg['monitor']} não existe. "
            f"Disponíveis: 1 a {len(sct.monitors) - 1}."
        )
    monitor = sct.monitors[cfg["monitor"]]

    print("Monitorando a tela... (Ctrl+C para parar)")
    last_notify = 0.0
    failures = 0

    try:
        while True:
            try:
                screen = grab_gray(sct, monitor, cfg["work_scale"])
                failures = 0
            except mss.exception.ScreenShotError as e:
                
                failures += 1
                if failures == 1 or failures % 10 == 0:
                    print(f"\n[aviso] Falha ao capturar a tela ({failures}x): {e}")
                try:
                    sct.close()
                except Exception:
                    pass
                time.sleep(min(2 * failures, 10))
                sct = mss.mss()
                monitor = sct.monitors[cfg["monitor"]]
                continue

            score = best_score(screen, template, cfg["scales"])

            if args.debug:
                print(f"\rsimilaridade: {score:.3f}  (limite: {cfg['threshold']})   ", end="")

            now = time.time()
            if score >= cfg["threshold"] and now - last_notify >= cfg["cooldown"]:
                print(f"\n[{time.strftime('%H:%M:%S')}] Partida detectada (score {score:.2f})!")
                if send_notification(cfg, cfg["message"]):
                    print("Notificação enviada.")
                last_notify = now

            time.sleep(cfg["check_interval"])
    except KeyboardInterrupt:
        print("\nEncerrado.")
    finally:
        sct.close()


if __name__ == "__main__":
    main()
