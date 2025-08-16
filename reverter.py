#!/usr/bin/env python3
"""
Reversor do Organizador Caótico 🔄
---------------------------------
Script para desfazer a organização lendo o relatório HTML gerado.

Uso:
python reversor.py --report "caminho/para/relatorio.html" --dry-run
"""

import argparse
import re
import shutil
from pathlib import Path
from typing import List, Tuple
import html


def parse_html_report(report_path: Path) -> List[Tuple[Path, Path, str]]:
    """
    Extrai as operações do relatório HTML.
    Retorna: [(origem_original, destino_atual, status)]
    """
    content = report_path.read_text(encoding='utf-8')
    
    # Regex para extrair linhas da tabela
    # Procura por: <td>origem</td><td>destino</td><td>categoria</td><td>data</td><td>tamanho</td><td>status</td>
    pattern = r'<tr><td>([^<]+)</td><td>([^<]+)</td><td>[^<]+</td><td>[^<]+</td><td>[^<]+</td><td>([^<]+)</td></tr>'
    
    moves = []
    for match in re.finditer(pattern, content):
        origem = html.unescape(match.group(1).strip())
        destino = html.unescape(match.group(2).strip())
        status = html.unescape(match.group(3).strip())
        
        # Só processa arquivos que foram efetivamente movidos
        if status == "Movido":
            moves.append((Path(origem), Path(destino), status))
    
    return moves


def restore_file_structure(moves: List[Tuple[Path, Path, str]], dry_run: bool = True) -> None:
    """
    Restaura a estrutura original dos arquivos.
    """
    success_count = 0
    error_count = 0
    
    print(f"[INFO] Encontradas {len(moves)} operações para reverter")
    
    for i, (origem_path, destino_atual, status) in enumerate(moves, 1):
        try:
            if not destino_atual.exists():
                print(f"[WARN] Arquivo não encontrado: {destino_atual}")
                continue
            
            # Recria a estrutura de pastas original
            origem_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Verifica se o arquivo original já existe
            if origem_path.exists():
                print(f"[WARN] Arquivo já existe no destino: {origem_path}")
                # Cria nome único
                counter = 1
                while True:
                    stem = origem_path.stem
                    suffix = origem_path.suffix
                    new_path = origem_path.parent / f"{stem}_restaurado_{counter}{suffix}"
                    if not new_path.exists():
                        origem_path = new_path
                        break
                    counter += 1
            
            if dry_run:
                print(f"[{i:4d}/{len(moves)}] [SIMULA] {destino_atual} -> {origem_path}")
            else:
                shutil.move(str(destino_atual), str(origem_path))
                print(f"[{i:4d}/{len(moves)}] [OK] Restaurado: {origem_path.name}")
                success_count += 1
                
        except Exception as e:
            print(f"[{i:4d}/{len(moves)}] [ERRO] {destino_atual}: {e}")
            error_count += 1
    
    if not dry_run:
        print(f"\n[RESULTADO] {success_count} arquivos restaurados, {error_count} erros")


def clean_empty_folders(root_path: Path, dry_run: bool = True) -> None:
    """
    Remove pastas vazias criadas pela organização.
    """
    if not root_path.exists():
        return
        
    removed = 0
    for folder in root_path.rglob("*"):
        if folder.is_dir():
            try:
                # Tenta remover se estiver vazia
                if not any(folder.iterdir()):
                    if dry_run:
                        print(f"[SIMULA] Removeria pasta vazia: {folder}")
                    else:
                        folder.rmdir()
                        print(f"[OK] Pasta vazia removida: {folder}")
                        removed += 1
            except OSError:
                pass  # Pasta não vazia ou erro de permissão
    
    if not dry_run and removed > 0:
        print(f"[INFO] {removed} pastas vazias removidas")


def main():
    parser = argparse.ArgumentParser(description="Reverte a organização usando o relatório HTML")
    parser.add_argument("--report", required=True, type=Path, help="Caminho para o relatório HTML")
    parser.add_argument("--organized-folder", type=Path, help="Pasta onde os arquivos foram organizados (para limpeza)")
    parser.add_argument("--dry-run", action="store_true", help="Simula a reversão sem mover arquivos")
    parser.add_argument("--clean-empty", action="store_true", help="Remove pastas vazias após restauração")
    
    args = parser.parse_args()
    
    if not args.report.exists():
        print(f"[ERRO] Relatório não encontrado: {args.report}")
        return 1
    
    print(f"[INFO] Analisando relatório: {args.report}")
    
    try:
        moves = parse_html_report(args.report)
        
        if not moves:
            print("[WARN] Nenhuma operação de movimento encontrada no relatório")
            return 1
        
        if args.dry_run:
            print("[INFO] *** MODO SIMULAÇÃO ATIVO ***")
        
        restore_file_structure(moves, args.dry_run)
        
        if args.clean_empty and args.organized_folder:
            print(f"\n[INFO] Limpando pastas vazias em {args.organized_folder}")
            clean_empty_folders(args.organized_folder, args.dry_run)
        
        if args.dry_run:
            print("\n[INFO] Execute sem --dry-run para aplicar as mudanças")
        else:
            print("\n[SUCESSO] Restauração concluída!")
        
        return 0
        
    except Exception as e:
        print(f"[ERRO] Falha na restauração: {e}")
        return 1


if __name__ == "__main__":
    exit(main())