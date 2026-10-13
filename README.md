# Overwatch Queue Notifier

Avisa no seu celular quando o Overwatch encontra uma partida, para você não
precisar ficar olhando a tela durante filas longas.

O script tira capturas da tela **somente na memória RAM** (nada é salvo em disco),
procura o aviso de "Partida encontrada" por reconhecimento de imagem e manda uma
notificação via **ntfy** ou **Telegram**.

> ⚠️ Projeto não afiliado à Blizzard Entertainment. O script apenas lê a imagem
> da tela: não modifica o jogo, não lê a memória e não automatiza nenhuma ação.
> Mesmo assim, o uso é por sua conta e risco.

## Requisitos

- Windows (testado no PC; não funciona em consoles)
- Python 3.9+
- Overwatch em **tela cheia sem bordas** ou **modo janela** (tela cheia exclusiva pode impedir a captura)

## Instalação (VS Code)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

No VS Code, selecione o interpretador da `.venv` (Ctrl+Shift+P → *Python: Select Interpreter*).

## Configuração

1. Copie `config.example.json` para `config.json`.
2. **ntfy (mais simples):** instale o app *ntfy* no celular, inscreva-se em um tópico
   com nome único e coloque o mesmo nome em `ntfy_topic`.
   **Telegram:** crie um bot com o @BotFather e preencha `telegram_token` e
   `telegram_chat_id`, trocando `"provider"` para `"telegram"`.
3. Teste o envio:
   ```bash
   python overwatch_notifier.py --test
   ```

## Criando a imagem de referência

A imagem depende da sua resolução, escala de interface e idioma, então cada
pessoa cria a sua. Quando uma partida for encontrada, tire um print (Win+Shift+S),
salve e rode:

```bash
python capture_reference.py --image meu_print.png
```

Selecione só a área do aviso com o mouse e aperte ENTER. A imagem é salva em
`reference/match_found.png` (ela **não** vai para o GitHub, por conter material da Blizzard).

## Uso

```bash
python overwatch_notifier.py            # monitora
python overwatch_notifier.py --debug    # mostra a similaridade ao vivo
```

Deixe rodando enquanto estiver na fila. Ctrl+C para parar.

## Ajustes (`config.json`)

| Campo | O que faz |
|---|---|
| `threshold` | Rigidez da detecção (0 a 1). Se não detecta, diminua; se dá falso alarme, aumente. |
| `monitor` | Número do monitor onde o jogo roda (1 = principal). |
| `check_interval` | Segundos entre verificações. |
| `scales` | Escalas testadas, para tolerar pequenas diferenças de tamanho. |
| `work_scale` | Reduz a captura para economizar CPU. |
| `cooldown` | Tempo mínimo entre duas notificações. |

## Dica

Use o `--debug` com o aviso na tela para ver qual pontuação ele atinge e ajuste o `threshold` um pouco abaixo disso.

## Licença

MIT
