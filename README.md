<div align="center">
  <img src="src/myTime/data/icons/myTime.svg" alt="myTime" width="128" height="128">
  <h1>🍅 myTime</h1>
  <p><strong>Gerenciador inteligente de tempo com Pomodoro e Jornadas de Trabalho</strong></p>
  <p>
    <img src="https://img.shields.io/badge/Python-3.11%2B-blue" alt="Python 3.11+">
    <img src="https://img.shields.io/badge/PySide6-6.6%2B-green" alt="PySide6 6.6+">
    <img src="https://img.shields.io/badge/license-MIT-yellow" alt="License MIT">
    <img src="https://img.shields.io/badge/status-em%20desenvolvimento-orange" alt="Status">
  </p>
  <br>
</div>

---

## 📋 Sobre

**myTime** é um aplicativo desktop Linux que combina a **Técnica Pomodoro** com um sistema de **Jornadas de Trabalho** para ajudar você a organizar seu dia de forma produtiva.

Com o myTime você pode:

- 🎯 **Focar** com blocos de concentração alternados com pausas curtas e longas
- 📅 **Planejar jornadas** — defina quantas horas quer trabalhar e o motor calcula automaticamente a sequência ideal de blocos
- 📊 **Acompanhar estatísticas** diárias e semanais do seu histórico de sessões
- 🔔 **Receber notificações** sonoras e visuais no início e fim de cada bloco
- 🎨 **Personalizar** cores, tempos, tamanho do ícone e muito mais
- 🌐 **Idiomas**: Português (pt_BR) e Inglês (en_US)

---

## ✨ Funcionalidades

| Funcionalidade | Descrição |
|---|---|
| **Pomodoro clássico** | Ciclo foco → pausa curta → foco → ... → pausa longa |
| **Modo Jornada** | Informe o total de horas de trabalho e o motor monta o cronograma automaticamente |
| **Ícone na bandeja** | Ícone dinâmico com progresso circular, tempo restante e cores por estado |
| **Notificações** | Alertas via `notify-send` com som personalizável |
| **Histórico** | Registro completo de sessões com estatísticas diárias/semanais |
| **Tarefas rápidas** | Associar tarefas às sessões com histórico de tarefas recentes |
| **Exportar/Importar** | Backup completo dos seus dados |
| **Auto-início** | Iniciar foco ou pausa automaticamente ao término do bloco atual |
| **Ícone customizável** | Tamanho, cores, opacidade, texto, modo largo (KDE) |
| **Pular blocos** | Pule pausas ou blocos de foco conforme sua necessidade |

---

## 🚀 Instalação

### Via pip (recomendado)

```bash
pip install mytime
```

### A partir do código fonte

```bash
git clone https://github.com/douglas/myTime.git
cd myTime
pip install -e .
```

### Desenvolvimento

```bash
git clone https://github.com/douglas/myTime.git
cd myTime
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### Flatpak

```bash
./scripts/build_flatpak.sh
```

### AppImage

```bash
./scripts/build_appimage.sh
```

### Instalação completa no sistema

O script `scripts/install.sh` instala o pacote, os ícones e a entrada `.desktop`:

```bash
./scripts/install.sh
```

---

## 🎮 Como usar

### Iniciar

```bash
myTime
```

Ou sem instalar:

```bash
python -m myTime
```

### Bandeja do sistema

O myTime é executado na **bandeja do sistema**. Clique com o botão direito no ícone para:

- Ver o estado atual e tempo restante
- Iniciar/retomar/pausar/pular blocos
- Iniciar uma jornada
- Abrir configurações
- Sair

### Jornadas

1. Clique em **"Nova Jornada"** no menu da bandeja
2. Defina quantas horas e minutos deseja trabalhar
3. (Opcional) Dê um nome à tarefa
4. O motor calcula automaticamente a sequência: foco → pausa curta → foco → ... → pausa longa
5. Acompanhe o progresso na janela principal

---

## ⚙️ Configuração

Todas as configurações são acessíveis pelo menu da bandeja → **Configurações**:

| Aba | Opções |
|---|---|
| **Geral** | Idioma, horário da jornada de trabalho, meta diária, auto-início |
| **Tempos** | Duração do foco, pausa curta, pausa longa, sessões antes da pausa longa |
| **Notificações** | Ativar/desativar, duração, som, som personalizado |
| **Ícone** | Tamanho (22-64px), exibição de texto, cores por estado, modo largo (KDE) |
| **Avançado** | Exportar/importar dados, resetar configurações, diretório de dados |

Os dados ficam em `~/.config/myTime/`.

---

## 🧪 Testes

```bash
pytest
```

Com cobertura:

```bash
pytest --cov=myTime
```

---

## 🏗️ Estrutura do projeto

```
myTime/
├── src/
│   └── myTime/
│       ├── __init__.py          # Metadados do pacote
│       ├── __main__.py          # Ponto de entrada
│       ├── core/
│       │   ├── engine.py         # Motor de jornadas (cálculo Pomodoro)
│       │   ├── models.py         # Modelos de dados
│       │   └── storage.py        # Persistência em JSON
│       ├── ui/
│       │   ├── main_window.py    # Janela principal
│       │   ├── tray.py           # Gerenciador da bandeja do sistema
│       │   ├── config_dialog.py  # Diálogo de configurações
│       │   ├── task_dialog.py    # Diálogo de tarefas
│       │   └── journey_dialog.py # Diálogo de jornadas
│       ├── utils/
│       │   ├── icons.py          # Geração de ícones dinâmicos
│       │   ├── audio.py          # Gerenciamento de áudio
│       │   └── notifications.py  # Notificações desktop
│       ├── data/
│       │   ├── icons/myTime.svg  # Ícone do aplicativo
│       │   └── myTime.desktop    # Arquivo .desktop
│       └── locales/
│           ├── pt_BR.json        # Tradução português
│           └── en_US.json        # Tradução inglês
├── tests/
│   ├── test_engine.py
│   └── test_storage.py
├── scripts/
│   ├── install.sh
│   ├── dev_install.sh
│   ├── build_flatpak.sh
│   └── build_appimage.sh
├── flatpak/
│   └── io.github.mytime.yml
├── pyproject.toml
├── LICENSE
└── README.md
```

---

## 🧰 Tecnologias

- **Python 3.11+**
- **PySide6** (Qt6) — Interface gráfica
- **notify-send** — Notificações desktop
- **libcanberra / PulseAudio / ALSA** — Som

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Fazer um **fork** do projeto
2. Criar uma **branch** (`git checkout -b feature/nova-feature`)
3. Fazer **commit** das suas alterações (`git commit -m 'Adiciona nova feature'`)
4. Fazer **push** para a branch (`git push origin feature/nova-feature`)
5. Abrir um **Pull Request**

Relate bugs ou sugira melhorias abrindo uma [Issue](https://github.com/douglas/myTime/issues).

---

## 📄 Licença

Distribuído sob licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para mais informações.

---

## 🌟 Apoie

Se o myTime for útil para você, considere deixar uma ⭐ no GitHub!

---

<div align="center">
  <sub>Feito com ☕ e 🍅 por <strong>Douglas</strong></sub>
</div>
