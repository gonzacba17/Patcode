from tools.plugin_system import PluginInterface
from typing import Dict, Any, List
from pathlib import Path
import ast
import logging

logger = logging.getLogger(__name__)


class DocsGeneratorPlugin(PluginInterface):
    """Plugin para generar documentación automática"""
    
    @property
    def name(self) -> str:
        return "docs_generator"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Genera docstrings, README y documentación API automáticamente"
    
    @property
    def author(self) -> str:
        return "PatCode Team"
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera documentación
        
        Args esperados en context['args']:
            - action: 'docstrings', 'readme', 'api', 'all'
            - file: archivo específico para docstrings
            - output: directorio de salida (default: docs/)
        """
        action = context.get('args', {}).get('action', 'readme')
        
        handlers = {
            'docstrings': self._generate_docstrings,
            'readme': self._generate_readme,
            'api': self._generate_api_docs,
            'all': self._generate_all
        }
        
        handler = handlers.get(action)
        if not handler:
            return {
                'success': False,
                'result': '',
                'error': f"Acción desconocida: {action}"
            }
        
        return handler(context)
    
    def _generate_docstrings(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Genera docstrings faltantes en archivos Python"""
        
        file_path = context.get('args', {}).get('file')
        
        if not file_path:
            return {
                'success': False,
                'result': '',
                'error': 'Se requiere especificar un archivo con --file'
            }
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {
                'success': False,
                'result': '',
                'error': f"Archivo no encontrado: {file_path}"
            }
        
        if file_path.suffix != '.py':
            return {
                'success': False,
                'result': '',
                'error': 'Solo se soportan archivos Python (.py)'
            }
        
        code = file_path.read_text()
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                'success': False,
                'result': '',
                'error': f"Error de sintaxis en {file_path}: {e}"
            }
        
        missing_docs = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                docstring = ast.get_docstring(node)
                
                if not docstring:
                    missing_docs.append({
                        'type': 'class' if isinstance(node, ast.ClassDef) else 'function',
                        'name': node.name,
                        'line': node.lineno
                    })
        
        if not missing_docs:
            return {
                'success': True,
                'result': f"✅ Todas las funciones/clases tienen docstrings en {file_path.name}",
                'data': {'missing': []}
            }
        
        agent = context.get('agent')
        if not agent:
            return {
                'success': False,
                'result': '',
                'error': 'Agente no disponible'
            }
        
        agent.file_manager.load_file(file_path)
        
        prompt = f"""Analiza el código de {file_path.name} y genera docstrings en formato Google para estas funciones/clases que no tienen documentación:

{', '.join([f"{item['type']} {item['name']}" for item in missing_docs])}

Para cada una, genera:
1. Descripción breve
2. Args (si aplica)
3. Returns (si aplica)
4. Raises (si aplica)

Formato:
```python
def function_name():
    \"\"\"
    Descripción breve.
    
    Args:
        param1 (type): Descripción
    
    Returns:
        type: Descripción
    \"\"\"
```
"""
        
        try:
            suggestions = agent.chat(prompt)
            
            return {
                'success': True,
                'result': f"📝 {len(missing_docs)} docstrings sugeridos",
                'data': {
                    'missing': missing_docs,
                    'suggestions': suggestions
                }
            }
        
        except Exception as e:
            return {
                'success': False,
                'result': '',
                'error': f"Error generando docstrings: {e}"
            }
    
    def _generate_readme(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Genera/actualiza README.md del proyecto"""
        
        current_dir = context['current_dir']
        readme_path = current_dir / 'README.md'
        
        project_info = self._analyze_project(current_dir)
        
        agent = context.get('agent')
        if not agent:
            return {
                'success': False,
                'result': '',
                'error': 'Agente no disponible'
            }
        
        prompt = f"""Genera un README.md profesional para este proyecto basado en esta información:

**Estructura del proyecto:**
{project_info['structure']}

**Archivos principales:**
{', '.join(project_info['main_files'])}

**Lenguaje:** {project_info['language']}
**Dependencias encontradas:** {', '.join(project_info['dependencies'][:10])}

El README debe incluir:
1. Título y descripción breve
2. Características principales
3. Instalación
4. Uso básico con ejemplos
5. Estructura del proyecto
6. Contribución
7. Licencia

Usa formato Markdown con emojis apropiados. Sé profesional pero accesible."""
        
        try:
            readme_content = agent.chat(prompt)
            
            if context.get('args', {}).get('save', False):
                readme_path.write_text(readme_content)
                result_msg = f"✅ README.md {'actualizado' if readme_path.exists() else 'creado'}: {readme_path}"
            else:
                result_msg = "README.md generado (no guardado)"
            
            return {
                'success': True,
                'result': result_msg,
                'data': {
                    'content': readme_content,
                    'project_info': project_info
                }
            }
        
        except Exception as e:
            return {
                'success': False,
                'result': '',
                'error': f"Error generando README: {e}"
            }
    
    def _generate_api_docs(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Genera documentación API en formato Markdown"""
        
        current_dir = context['current_dir']
        output_dir = Path(context.get('args', {}).get('output', 'docs/'))
        
        api_files = self._find_api_files(current_dir)
        
        if not api_files:
            return {
                'success': False,
                'result': '',
                'error': 'No se encontraron archivos con definiciones de API'
            }
        
        agent = context.get('agent')
        if not agent:
            return {
                'success': False,
                'result': '',
                'error': 'Agente no disponible'
            }
        
        docs = []
        
        for api_file in api_files:
            agent.file_manager.load_file(api_file)
            
            prompt = f"""Analiza {api_file.name} y genera documentación API en formato Markdown.

Para cada endpoint/ruta, documenta:
1. Método HTTP (GET, POST, etc.)
2. Ruta
3. Descripción
4. Parámetros (query, path, body)
5. Respuestas (códigos de estado y ejemplos)
6. Autenticación requerida (si aplica)

Formato:
## GET /api/users
Obtiene lista de usuarios.

**Parámetros:**
- `limit` (query, opcional): Número máximo de resultados

**Respuesta 200:**
```json
{{"users": [...]}}
```
"""
            
            try:
                api_doc = agent.chat(prompt)
                docs.append({
                    'file': api_file.name,
                    'content': api_doc
                })
            except Exception as e:
                logger.error(f"Error documentando {api_file}: {e}")
        
        full_docs = "# API Documentation\n\n"
        for doc in docs:
            full_docs += f"## {doc['file']}\n\n{doc['content']}\n\n---\n\n"
        
        if context.get('args', {}).get('save', False):
            output_dir.mkdir(parents=True, exist_ok=True)
            api_docs_path = output_dir / 'API.md'
            api_docs_path.write_text(full_docs)
            result_msg = f"✅ API docs creados: {api_docs_path}"
        else:
            result_msg = "API docs generados (no guardados)"
        
        return {
            'success': True,
            'result': result_msg,
            'data': {
                'content': full_docs,
                'files_documented': len(docs)
            }
        }
    
    def _generate_all(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Genera toda la documentación"""
        results = []
        
        readme_result = self._generate_readme(context)
        results.append(('README', readme_result))
        
        api_result = self._generate_api_docs(context)
        results.append(('API', api_result))
        
        successful = [name for name, r in results if r['success']]
        failed = [name for name, r in results if not r['success']]
        
        if failed:
            return {
                'success': False,
                'result': f"✅ {len(successful)} exitosos, ❌ {len(failed)} fallidos: {', '.join(failed)}",
                'data': {'results': results}
            }
        
        return {
            'success': True,
            'result': f"✅ Toda la documentación generada ({len(successful)} archivos)",
            'data': {'results': results}
        }
    
    def _analyze_project(self, path: Path) -> Dict[str, Any]:
        """Analiza estructura del proyecto"""
        
        if (path / 'requirements.txt').exists():
            language = 'Python'
            deps_file = path / 'requirements.txt'
            dependencies = deps_file.read_text().split('\n')
        elif (path / 'package.json').exists():
            language = 'Node.js'
            import json
            try:
                pkg = json.loads((path / 'package.json').read_text())
                dependencies = list(pkg.get('dependencies', {}).keys())
            except:
                dependencies = []
        else:
            language = 'Unknown'
            dependencies = []
        
        main_files = []
        for pattern in ['main.py', 'app.py', 'index.js', 'server.js', '__init__.py']:
            if (path / pattern).exists():
                main_files.append(pattern)
        
        structure = []
        for item in path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                structure.append(f"{item.name}/")
            elif item.is_file():
                structure.append(item.name)
        
        return {
            'language': language,
            'dependencies': dependencies,
            'main_files': main_files,
            'structure': '\n'.join(sorted(structure)[:20])
        }
    
    def _find_api_files(self, path: Path) -> List[Path]:
        """Encuentra archivos con definiciones de API"""
        api_files = []
        
        for py_file in path.rglob('*.py'):
            if py_file.name.startswith('test_'):
                continue
            
            try:
                content = py_file.read_text()
                
                if any(pattern in content for pattern in [
                    '@app.route', '@router.', 'APIRouter', 
                    'app.get', 'app.post', 'app.put', 'app.delete'
                ]):
                    api_files.append(py_file)
            except:
                continue
        
        return api_files
