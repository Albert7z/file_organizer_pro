# File Organizer Pro v1.0 📂✨

> **Organize milhares de arquivos automaticamente. Desfaça tudo com um clique.**

Sistema inteligente de organização com **detecção de duplicados** e **reversão 100% confiável**.



## 🚀 Uso Rápido

```bash
# 1. Sempre simule primeiro (RECOMENDADO)
python organizer.py --dest "C:/Organizado" --dry-run

# 2. Execute de verdade
python organizer.py --dest "C:/Organizado" --open-report

# 3. Se precisar desfazer tudo
python reverter.py --report "relatorio_organizador_123456.html"
```

## ✨ O que faz

### 🗂️ **Organização Automática**
```
Origem:                    Resultado:
Downloads/                 Organizado/
├── foto.jpg              ├── Midia/Imagens/2024/
├── relatorio.pdf         │   └── 2024-08-16 - foto.jpg
├── musica.mp3            ├── Documentos/PDFs/2024/
└── backup.zip            │   └── 2024-08-16 - relatorio.pdf
                          ├── Midia/Audio/2024/
                          │   └── 2024-08-16 - musica.mp3
                          └── Arquivos/Compactados/2024/
                              └── 2024-08-16 - backup.zip
```

### 🔍 **Detecção de Duplicados**
- Usa **hash SHA-256** (100% preciso)
- Move duplicados para pasta `Duplicates/` ou remove completamente
- Economiza espaço automaticamente

### 📊 **Relatórios Visuais**
- Dashboard HTML profissional
- Estatísticas por categoria e extensão
- Lista completa para **reversão total**

### 🔄 **Sistema de Reversão Único**
- **Desfaz qualquer organização** perfeitamente
- Reconstrói estruturas originais exatamente como eram
- Baseado nos relatórios HTML gerados automaticamente
- **Nenhuma outra ferramenta oferece isso!**

## 🎯 Por que este projeto?

**História real:** Executei um organizador automático e ele "bagunçou" completamente meus arquivos de jogos e projetos. Em vez de desistir, **transformei o problema em solução**.

**O resultado:** Uma ferramenta que não apenas organiza melhor, mas permite **voltar atrás com 100% de segurança**.

## 🔧 Instalação

### Pré-requisitos
- Python 3.9+ (sem dependências externas!)

### Download
```bash
git clone https://github.com/Albert7z/file_organizer_pro
cd file-organizer-pro
```

## 📖 Exemplos

### Organização Básica
```bash
# Organiza Downloads, Desktop e Documents
python organizer.py --dest "C:/Organizado" --dry-run
python organizer.py --dest "C:/Organizado"
```

### Pastas Específicas
```bash
python organizer.py \
  --sources "C:/Downloads" "D:/Projetos" \
  --dest "E:/Organizado" \
  --delete-duplicates \
  --clean-empty
```

### Reversão Total
```bash
# Sempre teste primeiro
python reverter.py --report "relatorio.html" --dry-run

# Desfaz tudo
python reverter.py --report "relatorio.html" --clean-empty
```

## 🎛️ Opções

| Opção | Descrição |
|-------|-----------|
| `--sources` | Pastas a organizar (padrão: Downloads, Desktop, Documents) |
| `--dest` | Pasta de destino (obrigatório) |
| `--dry-run` | **Simula sem modificar** (recomendado na primeira vez) |
| `--delete-duplicates` | Remove duplicados em vez de mover para `Duplicates/` |
| `--clean-empty` | Remove pastas vazias após organização |
| `--open-report` | Abre relatório HTML automaticamente |

## 📊 Categorias Suportadas

| Tipo | Extensões | Destino |
|------|-----------|---------|
| **Documentos** | `.pdf`, `.doc`, `.docx`, `.txt` | `Documentos/PDFs/`, `Documentos/Word/` |
| **Imagens** | `.jpg`, `.png`, `.gif`, `.svg` | `Midia/Imagens/` |
| **Áudio/Vídeo** | `.mp3`, `.mp4`, `.mkv` | `Midia/Audio/`, `Midia/Videos/` |
| **Código** | `.py`, `.js`, `.html`, `.css` | `Dev/Codigo/`, `Dev/Web/` |
| **Compactados** | `.zip`, `.rar`, `.7z` | `Arquivos/Compactados/` |
| **Outros** | Demais extensões | `Diversos/` |

## 🛡️ Segurança

- ✅ **Modo simulação obrigatório** para primeira execução
- ✅ **Backup automático** via relatórios detalhados
- ✅ **Validação de caminhos** antes de qualquer operação
- ✅ **Reversão testada** e aprovada em cenário real
- ✅ **Zero dependências** externas

## 🔬 Tecnologia

- **Python 3.9+** com bibliotecas padrão apenas
- **SHA-256** para detecção confiável de duplicados
- **Pathlib** para manipulação moderna de arquivos
- **HTML/CSS** para relatórios profissionais
- **Multiplataforma** (Windows, macOS, Linux)

## 📈 Casos de Uso

- **🎮 Bibliotecas de Jogos** - Organiza mantendo estruturas importantes
- **📁 Limpeza de Downloads** - Remove duplicados automaticamente  
- **💾 Migração de Dados** - Reorganiza estruturas antigas com segurança
- **🔍 Auditoria de Espaço** - Identifica onde está ocupado o disco

## 🤝 Contribuição

1. Fork o projeto
2. Crie sua branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 🛣️ Roadmap v2.0

- [ ] Interface gráfica (GUI)
- [ ] Monitoramento em tempo real
- [ ] Regras por data/tamanho
- [ ] Plugins personalizados
- [ ] Integração com cloud storage

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

## 👨‍💻 Autor

**Albertt**
- GitHub: (https://github.com/Albert7z)
- LinkedIn: (https://www.linkedin.com/in/albertdorval/)

---

⭐ **Se este projeto te ajudou, dê uma estrela!**

**File Organizer Pro v1.0 - Organize com segurança. Reverta com confiança.**