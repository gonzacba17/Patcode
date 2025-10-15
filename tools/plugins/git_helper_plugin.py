from tools.plugin_system import PluginInterface
from typing import Dict, Any, List
from pathlib import Path
import subprocess
import logging

logger = logging.getLogger(__name__)


class GitHelperPlugin(PluginInterface):
    """Plugin para operaciones Git inteligentes"""
    
    @property
    def name(self) -> str:
        return "git_helper"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Asistente Git con commits semánticos y análisis de cambios"
    
    @property
    def author(self) -> str:
        return "PatCode Team"
    
    @property
    def dependencies(self) -> List[str]:
        return []
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta operaciones Git
        
        Args esperados en context['args']:
            - action: 'status', 'diff', 'commit', 'log', 'suggest_commit'
            - message: mensaje de commit (para action='commit')
            - files: archivos específicos (opcional)
        """
        action = context.get('args', {}).get('action', 'status')
        
        if not self._is_git_repo(context['current_dir']):
            return {
                'success': False,
                'result': '',
                'error': 'No estás en un repositorio Git'
            }
        
        handlers = {
            'status': self._handle_status,
            'diff': self._handle_diff,
            'commit': self._handle_commit,
            'log': self._handle_log,
            'suggest_commit': self._handle_suggest_commit
        }
        
        handler = handlers.get(action)
        if not handler:
            return {
                'success': False,
                'result': '',
                'error': f"Acción desconocida: {action}"
            }
        
        return handler(context)
    
    def _is_git_repo(self, path: Path) -> bool:
        """Verifica si estamos en un repo Git"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _handle_status(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Git status con análisis"""
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=context['current_dir'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'result': '',
                    'error': result.stderr
                }
            
            lines = result.stdout.strip().split('\n')
            if not lines or lines == ['']:
                return {
                    'success': True,
                    'result': '✅ Working directory clean',
                    'data': {'modified': [], 'untracked': [], 'staged': []}
                }
            
            modified = []
            untracked = []
            staged = []
            
            for line in lines:
                if not line or len(line) < 3:
                    continue
                
                parts = line.split(maxsplit=1)
                if len(parts) < 2:
                    continue
                    
                status = parts[0][:2] if len(parts[0]) >= 2 else parts[0]
                file = parts[1] if len(parts) > 1 else ''
                
                if not file:
                    continue
                
                if status == '??':
                    untracked.append(file)
                elif len(status) >= 2 and status[1] == 'M' and status[0] == ' ':
                    modified.append(file)
                elif len(status) >= 1 and status[0] != ' ' and status[0] != '?':
                    staged.append(file)
            
            summary = []
            if staged:
                summary.append(f"📦 {len(staged)} staged")
            if modified:
                summary.append(f"✏️  {len(modified)} modified")
            if untracked:
                summary.append(f"❓ {len(untracked)} untracked")
            
            return {
                'success': True,
                'result': ', '.join(summary),
                'data': {
                    'modified': modified,
                    'untracked': untracked,
                    'staged': staged
                }
            }
        
        except Exception as e:
            return {
                'success': False,
                'result': '',
                'error': str(e)
            }
    
    def _handle_diff(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Git diff con análisis"""
        files = context.get('args', {}).get('files', [])
        
        cmd = ['git', 'diff']
        if files:
            cmd.extend(files)
        
        try:
            result = subprocess.run(
                cmd,
                cwd=context['current_dir'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'result': '',
                    'error': result.stderr
                }
            
            diff = result.stdout
            
            if not diff:
                return {
                    'success': True,
                    'result': 'No changes to show',
                    'data': {'diff': ''}
                }
            
            lines = diff.split('\n')
            additions = sum(1 for line in lines if line.startswith('+') and not line.startswith('+++'))
            deletions = sum(1 for line in lines if line.startswith('-') and not line.startswith('---'))
            
            summary = f"+{additions} -{deletions}"
            
            return {
                'success': True,
                'result': summary,
                'data': {
                    'diff': diff,
                    'additions': additions,
                    'deletions': deletions
                }
            }
        
        except Exception as e:
            return {
                'success': False,
                'result': '',
                'error': str(e)
            }
    
    def _handle_commit(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un commit"""
        message = context.get('args', {}).get('message')
        
        if not message:
            return {
                'success': False,
                'result': '',
                'error': 'Se requiere un mensaje de commit'
            }
        
        try:
            result = subprocess.run(
                ['git', 'commit', '-m', message],
                cwd=context['current_dir'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'result': '',
                    'error': result.stderr
                }
            
            return {
                'success': True,
                'result': f"✅ Commit creado: {message[:50]}...",
                'data': {'output': result.stdout}
            }
        
        except Exception as e:
            return {
                'success': False,
                'result': '',
                'error': str(e)
            }
    
    def _handle_log(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Muestra log de commits"""
        limit = context.get('args', {}).get('limit', 10)
        
        try:
            result = subprocess.run(
                ['git', 'log', f'-{limit}', '--oneline'],
                cwd=context['current_dir'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'result': '',
                    'error': result.stderr
                }
            
            return {
                'success': True,
                'result': result.stdout,
                'data': {'commits': result.stdout.split('\n')}
            }
        
        except Exception as e:
            return {
                'success': False,
                'result': '',
                'error': str(e)
            }
    
    def _handle_suggest_commit(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Sugiere mensaje de commit semántico usando LLM"""
        
        diff_result = self._handle_diff(context)
        if not diff_result['success']:
            return diff_result
        
        diff = diff_result['data'].get('diff', '')
        
        if not diff:
            return {
                'success': False,
                'result': '',
                'error': 'No hay cambios para commitear'
            }
        
        agent = context.get('agent')
        if not agent:
            return {
                'success': False,
                'result': '',
                'error': 'Agente no disponible'
            }
        
        prompt = f"""Analiza este git diff y sugiere un mensaje de commit siguiendo Conventional Commits:

Formato: <type>(<scope>): <description>

Types: feat, fix, docs, style, refactor, test, chore

Diff:
```
{diff[:2000]}
```

Responde SOLO con el mensaje de commit, sin explicaciones adicionales."""
        
        try:
            suggested_message = agent.chat(prompt)
            
            return {
                'success': True,
                'result': suggested_message.strip(),
                'data': {
                    'diff_summary': f"+{diff_result['data']['additions']} -{diff_result['data']['deletions']}"
                }
            }
        
        except Exception as e:
            return {
                'success': False,
                'result': '',
                'error': f"Error generando sugerencia: {e}"
            }
