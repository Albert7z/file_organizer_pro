#!/usr/bin/env python3
"""
File Organizer Pro v1.0 📂✨
============================
Sistema inteligente de organização com detecção de duplicados e reversão completa.

Estrutura simplificada: Categoria/Ano/arquivos
Sem pastas vazias, sem complicação.


#  ===============================================
#  ▶️ Uso Rápido:
#  -----------------------------------------------
#  1. Simule a organização de uma pasta específica (RECOMENDADO)
#  python organizer.py --sources "C:/Caminho/Da/Sua/Pasta  --dest "c:\caminho\da\pasta\Organizado" --dry-run
#
#  2. Execute de verdade para a pasta padrão (Downloads, Desktop, etc.)
#  python organizer.py --dest "C:/Organizado" --open-report
#
#  3. Reverte se necessário (use o script reverter.py)
#  python reverter.py --report "relatorio.html" --dry-run
#  ===============================================

Autor: Albertt
GitHub: https://github.com/Albert7z/file_organizer_pro/
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import shutil
import sys
import textwrap
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

# ============================ Configuração ============================ #

DEFAULT_RULES = {
    # Documentos
    ".pdf": "Documentos/PDFs",
    ".doc": "Documentos/Word",
    ".docx": "Documentos/Word", 
    ".txt": "Documentos/Textos",
    ".xlsx": "Documentos/Planilhas",
    ".csv": "Documentos/Planilhas",
    ".ppt": "Documentos/Apresentacoes",
    ".pptx": "Documentos/Apresentacoes",
    
    # Imagens
    ".jpg": "Midia/Imagens",
    ".jpeg": "Midia/Imagens",
    ".png": "Midia/Imagens", 
    ".gif": "Midia/Imagens",
    ".webp": "Midia/Imagens",
    ".svg": "Midia/Imagens",

    # Áudio/Vídeo
    ".mp3": "Midia/Audio",
    ".wav": "Midia/Audio",
    ".mp4": "Midia/Videos",
    ".mkv": "Midia/Videos",
    ".mov": "Midia/Videos",

    # Desenvolvimento
    ".py": "Dev/Codigo",
    ".js": "Dev/Codigo",
    ".html": "Dev/Web",
    ".css": "Dev/Web",
    ".json": "Dev/Config",

    # Compactados
    ".zip": "Arquivos/Compactados",
    ".rar": "Arquivos/Compactados",
    ".7z": "Arquivos/Compactados",

    # Executáveis
    ".exe": "Apps/Instaladores",
    ".msi": "Apps/Instaladores",
}

FALLBACK_FOLDER = "Diversos"
DUPLICATES_FOLDER = "Duplicates"

# ================================ Utilidades ================================ #

def human_size(num_bytes: int) -> str:
    """Converte bytes para formato legível"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num_bytes < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


def safe_filename(text: str, max_len: int = 100) -> str:
    """Limpa nome de arquivo removendo caracteres problemáticos"""
    # Remove extensão se houver
    if '.' in text:
        text = text.rsplit('.', 1)[0]
    
    # Normaliza espaços e caracteres especiais
    text = re.sub(r'[<>:"/\\|?*]', '', text)  # Remove caracteres proibidos no Windows
    text = re.sub(r'\s+', ' ', text)          # Normaliza espaços
    text = text.strip(' .-_')                 # Remove pontuação nas bordas
    
    # Garante que não fica vazio
    if not text:
        text = "arquivo"
    
    # Limita tamanho
    if len(text) > max_len:
        text = text[:max_len].rstrip()
        
    return text


def compute_hash(path: Path) -> str:
    """Calcula hash SHA-256 do arquivo"""
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


def is_hidden(path: Path) -> bool:
    """Verifica se arquivo/pasta é oculto ou de sistema"""
    name = path.name.lower()
    return (
        name.startswith('.') or 
        name in {'system volume information', '$recycle.bin', '__macosx', 'thumbs.db'}
    )


def unique_path(path: Path) -> Path:
    """Gera caminho único se arquivo já existir"""
    if not path.exists():
        return path
        
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 1
    
    while True:
        new_path = parent / f"{stem} ({counter}){suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


def cleanup_empty_folders(root: Path) -> int:
    """Remove pastas vazias. Retorna quantidade removida."""
    removed = 0
    if not root.exists():
        return removed
        
    # Processa de baixo para cima (subpastas primeiro)
    for folder in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if folder.is_dir() and folder != root:
            try:
                folder.rmdir()  # Remove apenas se estiver vazia
                removed += 1
                print(f"[LIMPEZA] Pasta vazia removida: {folder.name}")
            except OSError:
                pass  # Não está vazia, mantém
    
    return removed


# =============================== Data Classes =============================== #

@dataclass
class FileAction:
    src: Path
    dest: Path
    category: str
    size: int
    date: dt.date
    duplicate_of: Optional[Path] = None


@dataclass
class Stats:
    total_files: int = 0
    processed: int = 0
    duplicates: int = 0
    moved_bytes: int = 0
    per_category: Dict[str, int] = field(default_factory=dict)
    per_ext: Dict[str, int] = field(default_factory=dict)
    largest: List[Tuple[str, int]] = field(default_factory=list)

    def add_file(self, path: Path, size: int):
        self.total_files += 1
        # Mantém top 10 maiores
        self.largest.append((str(path), size))
        self.largest.sort(key=lambda x: x[1], reverse=True)
        if len(self.largest) > 10:
            self.largest.pop()

    def add_processed(self, ext: str, category: str, size: int, is_duplicate: bool):
        self.processed += 1
        self.per_ext[ext] = self.per_ext.get(ext, 0) + 1
        self.per_category[category] = self.per_category.get(category, 0) + 1
        
        if is_duplicate:
            self.duplicates += 1
        else:
            self.moved_bytes += size


# ============================ Processamento Principal ============================ #

def scan_files(sources: List[Path]) -> Iterable[Path]:
    """Escaneia arquivos nas pastas de origem"""
    for source in sources:
        if not source.exists():
            continue
            
        if source.is_file():
            yield source
            continue
            
        try:
            for item in source.rglob("*"):
                if item.is_file() and not is_hidden(item):
                    yield item
        except PermissionError:
            print(f"[AVISO] Sem permissão para acessar: {source}")


def show_progress(current: int, total: int, file_name: str = "", width: int = 50) -> None:
    """Exibe barra de progresso no terminal"""
    if total == 0:
        return
        
    percent = (current / total) * 100
    filled = int(width * current / total)
    bar = "█" * filled + "░" * (width - filled)
    
    # Trunca nome do arquivo se muito longo
    if len(file_name) > 40:
        file_name = file_name[:37] + "..."
    
    print(f"\r🔍 Analisando [{bar}] {percent:5.1f}% ({current:,}/{total:,}) {file_name}", end="", flush=True)


def plan_organization(
    sources: List[Path], 
    dest_root: Path, 
    rules: Dict[str, str],
    exclude_dest: bool = True
) -> Tuple[List[FileAction], Stats]:
    """Planeja as ações de organização"""
    
    actions: List[FileAction] = []
    stats = Stats()
    seen_hashes: Dict[str, Path] = {}
    
    print("[INFO] Contando arquivos...")
    
    # Primeiro, conta todos os arquivos para mostrar progresso
    all_files = list(scan_files(sources))
    total_files = len(all_files)
    
    if total_files == 0:
        print("ℹ️  Nenhum arquivo encontrado.")
        return actions, stats
    
    print(f"[INFO] Encontrados {total_files:,} arquivos. Iniciando análise...")
    
    for i, file_path in enumerate(all_files, 1):
        try:
            # Evita organizar a própria pasta de destino
            if exclude_dest and str(file_path).startswith(str(dest_root)):
                continue
            
            # Atualiza barra de progresso
            show_progress(i, total_files, file_path.name)
                
            size = file_path.stat().st_size
            stats.add_file(file_path, size)
            
            # Determina categoria
            ext = file_path.suffix.lower()
            category = rules.get(ext, FALLBACK_FOLDER)
            
            # Data do arquivo (modificação)
            file_date = dt.datetime.fromtimestamp(file_path.stat().st_mtime).date()
            
            # Nova estrutura: dest_root/categoria/ano/arquivo
            category_path = dest_root / category / str(file_date.year)
            
            # Novo nome: YYYY-MM-DD - nome_limpo.ext
            clean_name = safe_filename(file_path.stem)
            new_filename = f"{file_date:%Y-%m-%d} - {clean_name}{ext}"
            dest_path = unique_path(category_path / new_filename)
            
            # Verifica duplicados
            file_hash = compute_hash(file_path)
            duplicate_of = None
            
            if file_hash and file_hash in seen_hashes:
                duplicate_of = seen_hashes[file_hash]
            elif file_hash:
                seen_hashes[file_hash] = file_path
            
            actions.append(FileAction(
                src=file_path,
                dest=dest_path,
                category=category,
                size=size,
                date=file_date,
                duplicate_of=duplicate_of
            ))
            
            stats.add_processed(ext, category, size, duplicate_of is not None)
            
        except Exception as e:
            print(f"\n[ERRO] Falha ao processar {file_path}: {e}")
    
    # Limpa a linha de progresso e mostra resultado final
    print(f"\n✅ Análise concluída! {len(actions):,} arquivos processados.")
    
    return actions, stats


def execute_organization(
    actions: List[FileAction], 
    dest_root: Path,
    dry_run: bool = False,
    delete_duplicates: bool = False
) -> None:
    """Executa a organização dos arquivos"""
    
    if not dry_run:
        dest_root.mkdir(parents=True, exist_ok=True)
        if not delete_duplicates:
            (dest_root / DUPLICATES_FOLDER).mkdir(exist_ok=True)
    
    total_actions = len(actions)
    errors = 0
    
    for i, action in enumerate(actions, 1):
        try:
            # Atualiza barra de progresso
            action_type = "SIMULA" if dry_run else ("DELETE" if action.duplicate_of and delete_duplicates else "DUPLICATE" if action.duplicate_of else "MOVE")
            show_progress(i, total_actions, f"{action_type}: {action.src.name}")
            
            if action.duplicate_of:
                if delete_duplicates:
                    if not dry_run:
                        action.src.unlink()
                else:
                    # Move duplicado para pasta especial
                    dup_dest = dest_root / DUPLICATES_FOLDER / action.src.name
                    dup_dest = unique_path(dup_dest)
                    
                    if not dry_run:
                        shutil.move(str(action.src), str(dup_dest))
            else:
                # Move arquivo normal
                if not dry_run:
                    action.dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(action.src), str(action.dest))
                    
        except Exception as e:
            errors += 1
            print(f"\n[ERRO] {action.src}: {e}")
    
    # Limpa linha de progresso e mostra resultado
    mode = "Simulação" if dry_run else "Organização"
    print(f"\n✅ {mode} concluída! {total_actions - errors:,} arquivos processados")
    if errors > 0:
        print(f"⚠️  {errors} erros encontrados")


# ================================ Relatório HTML ================================ #

def generate_report(actions: List[FileAction], stats: Stats, dest_root: Path, dry_run: bool = False) -> Path:
    """Gera relatório HTML com estatísticas"""
    
    timestamp = int(time.time())
    # Se for simulação, salva relatório na pasta atual em vez da pasta de destino
    if dry_run:
        report_path = Path.cwd() / f"simulacao_organizador_{timestamp}.html"
    else:
        report_path = dest_root / f"relatorio_organizador_{timestamp}.html"
    
    # Dados para tabela
    table_rows = []
    for action in actions:
        if action.duplicate_of:
            status = "Duplicado"
            dest_display = str(action.duplicate_of)
        else:
            status = "Simulado" if dry_run else "Movido"
            dest_display = str(action.dest)
        
        table_rows.append(
            f"<tr>"
            f"<td>{html.escape(str(action.src))}</td>"
            f"<td>{html.escape(dest_display)}</td>"
            f"<td>{html.escape(action.category)}</td>"
            f"<td>{action.date}</td>"
            f"<td>{human_size(action.size)}</td>"
            f"<td>{status}</td>"
            f"</tr>"
        )
    
    # Gráficos simples
    def simple_chart(title: str, data: Dict[str, int]) -> str:
        if not data:
            return f"<h3>{title}</h3><p>Sem dados</p>"
            
        items = sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]
        max_val = max(v for _, v in items) if items else 1
        
        bars = []
        for label, count in items:
            width = int((count / max_val) * 100)
            bars.append(
                f'<div style="margin: 4px 0">'
                f'<div style="font-size: 12px">{html.escape(label)}: {count}</div>'
                f'<div style="background: #eee; height: 8px; border-radius: 4px">'
                f'<div style="background: #007acc; height: 8px; width: {width}%; border-radius: 4px"></div>'
                f'</div></div>'
            )
        
        return f"<h3>{title}</h3>" + "".join(bars)
    
    # Cabeçalho muda conforme o modo
    header_title = "📂 File Organizer Pro v1.0 - Simulação" if dry_run else "📂 File Organizer Pro v1.0"
    header_badge = "Simulação" if dry_run else "Execução Real"
    badge_color = "#ff9500" if dry_run else "#007acc"
    
    html_content = f'''<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>File Organizer Pro v1.0 - {"Simulação" if dry_run else "Relatório"}</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0; padding: 24px; background: #f8f9fa; color: #212529;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: white; padding: 24px; border-radius: 8px; margin-bottom: 24px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px; }}
        .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .table-container {{ background: white; padding: 20px; border-radius: 8px; margin-top: 24px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #dee2e6; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        .badge {{ background: {badge_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; }}
        .stat {{ text-align: center; }}
        .stat-number {{ font-size: 24px; font-weight: bold; color: {badge_color}; }}
        .stat-label {{ font-size: 12px; color: #6c757d; text-transform: uppercase; }}
        {'.warning {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 16px; border-radius: 8px; margin-bottom: 24px; }}' if dry_run else ''}
    </style>
</head>
<body>
    <div class="container">
        {'<div class="warning">⚠️ <strong>Modo Simulação</strong> - Nenhum arquivo foi realmente movido. Este é apenas um preview do que seria feito.</div>' if dry_run else ''}
        
        <div class="header">
            <h1>{header_title}</h1>
            <p>Relatório gerado em {dt.datetime.now():%d/%m/%Y às %H:%M:%S}</p>
            <div class="badge">{header_badge}</div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h2>📊 Resumo Geral</h2>
                <div class="stats">
                    <div class="stat">
                        <div class="stat-number">{stats.total_files}</div>
                        <div class="stat-label">Arquivos</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">{stats.processed}</div>
                        <div class="stat-label">{"Seriam processados" if dry_run else "Processados"}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">{stats.duplicates}</div>
                        <div class="stat-label">Duplicados</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">{human_size(stats.moved_bytes)}</div>
                        <div class="stat-label">{"Seriam organizados" if dry_run else "Organizados"}</div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                {simple_chart("📁 Por Categoria", stats.per_category)}
            </div>
            
            <div class="card">
                {simple_chart("📄 Por Extensão", stats.per_ext)}
            </div>
            
            <div class="card">
                <h3>🏆 Maiores Arquivos</h3>
                <ol>
                    {''.join(f'<li>{html.escape(Path(p).name)} — {human_size(s)}</li>' for p, s in stats.largest)}
                </ol>
            </div>
        </div>
        
        <div class="table-container">
            <h2>📋 Detalhamento Completo</h2>
            <table>
                <thead>
                    <tr>
                        <th>Origem</th>
                        <th>Destino</th>
                        <th>Categoria</th>
                        <th>Data</th>
                        <th>Tamanho</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(table_rows)}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>'''
    
    report_path.write_text(html_content, encoding='utf-8')
    return report_path


# ================================== CLI ==================================== #

def get_default_sources() -> List[Path]:
    """Retorna pastas padrão para organizar"""
    home = Path.home()
    candidates = [
        home / "Downloads"
    ]
    return [p for p in candidates if p.exists()]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="File Organizer Pro v1.0 - Organização inteligente com reversão",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Exemplos:
          %(prog)s --dest "C:/Organizado" --dry-run
          %(prog)s --dest "C:/Organizado" --open-report  
          %(prog)s --sources "C:/Downloads" --dest "D:/Arquivos" --delete-duplicates
        """)
    )
    
    parser.add_argument("--sources", nargs="*", type=Path, 
                       help="Pastas a organizar (padrão: Downloads, Desktop, Documents)")
    parser.add_argument("--dest", required=True, type=Path,
                       help="Pasta de destino para organização")
    parser.add_argument("--rules", type=Path,
                       help="Arquivo JSON com regras customizadas")
    parser.add_argument("--dry-run", action="store_true",
                       help="Simula sem modificar arquivos (RECOMENDADO na primeira vez)")
    parser.add_argument("--delete-duplicates", action="store_true",
                       help="Remove duplicados em vez de mover para pasta Duplicates")
    parser.add_argument("--open-report", action="store_true",
                       help="Abre relatório automaticamente")
    parser.add_argument("--clean-empty", action="store_true",
                       help="Remove pastas vazias após organização")
    
    args = parser.parse_args(argv)
    
    # Configura origens
    sources = [Path(s).expanduser() for s in args.sources] if args.sources else get_default_sources()
    dest_root = Path(args.dest).expanduser().resolve()
    
    # Carrega regras
    rules = DEFAULT_RULES
    if args.rules and args.rules.exists():
        try:
            with open(args.rules, 'r', encoding='utf-8') as f:
                custom_rules = json.load(f)
                rules.update(custom_rules)
                print(f"[INFO] Regras customizadas carregadas: {args.rules}")
        except Exception as e:
            print(f"[AVISO] Erro ao carregar regras: {e}. Usando padrão.")
    
    print("=" * 60)
    print("📂 FILE ORGANIZER PRO v1.0")
    print("=" * 60)
    print(f"📁 Origens: {', '.join(str(s) for s in sources)}")
    print(f"🎯 Destino: {dest_root}")
    
    if args.dry_run:
        print("🧪 MODO SIMULAÇÃO - Nada será modificado")
    
    # Planejamento
    actions, stats = plan_organization(sources, dest_root, rules)
    
    if not actions:
        print("ℹ️  Nenhum arquivo encontrado para organizar.")
        return 0
    
    print(f"\n📊 Encontrados: {stats.total_files} arquivos")
    print(f"🔄 Para processar: {stats.processed} arquivos") 
    print(f"📋 Duplicados: {stats.duplicates} arquivos")
    
    if args.dry_run:
        print(f"💾 Espaço que seria organizado: {human_size(stats.moved_bytes)}")
    else:
        print(f"💾 Espaço a organizar: {human_size(stats.moved_bytes)}")
    
    # Confirmação se não for dry-run
    if not args.dry_run:
        response = input("\n🤔 Continuar com a organização? (s/N): ").lower()
        if response not in ['s', 'sim', 'y', 'yes']:
            print("❌ Organização cancelada.")
            return 0
    
    # Execução
    print(f"\n{'🧪 Simulando' if args.dry_run else '🚀 Organizando'}...")
    execute_organization(actions, dest_root, args.dry_run, args.delete_duplicates)
    
    # Limpeza de pastas vazias (só executa se não for dry-run)
    if args.clean_empty and not args.dry_run:
        print("\n🧹 Removendo pastas vazias...")
        removed = cleanup_empty_folders(dest_root)
        if removed:
            print(f"✅ {removed} pastas vazias removidas")
    
    # Relatório - AGORA SEMPRE GERA!
    print(f"\n📝 Gerando relatório{'de simulação' if args.dry_run else ''}...")
    report_path = generate_report(actions, stats, dest_root, args.dry_run)
    print(f"✅ Relatório: {report_path}")
    
    if args.open_report:
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(report_path))
            elif sys.platform == "darwin":
                os.system(f'open "{report_path}"')
            else:
                os.system(f'xdg-open "{report_path}"')
        except Exception:
            print("⚠️  Não foi possível abrir o relatório automaticamente")
    
    print(f"\n🎉 {'Simulação' if args.dry_run else 'Organização'} concluída!")
    
    if args.dry_run:
        print("💡 Para executar de verdade, rode sem --dry-run")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n👋 Operação cancelada pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)