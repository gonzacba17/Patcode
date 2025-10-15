from tools.plugin_system import PluginInterface
from typing import Dict, Any, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DockerHelperPlugin(PluginInterface):
    """Plugin para generación de configuraciones Docker"""
    
    @property
    def name(self) -> str:
        return "docker_helper"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Genera Dockerfile, docker-compose.yml y .dockerignore optimizados"
    
    @property
    def author(self) -> str:
        return "PatCode Team"
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera configuraciones Docker
        
        Args esperados en context['args']:
            - action: 'dockerfile', 'compose', 'dockerignore', 'all'
            - language: 'python', 'node', 'go', etc. (auto-detecta si no se especifica)
            - framework: 'fastapi', 'flask', 'express', etc. (opcional)
        """
        action = context.get('args', {}).get('action', 'all')
        language = context.get('args', {}).get('language')
        
        if not language:
            language = self._detect_language(context['current_dir'])
        
        handlers = {
            'dockerfile': self._generate_dockerfile,
            'compose': self._generate_compose,
            'dockerignore': self._generate_dockerignore,
            'all': self._generate_all
        }
        
        handler = handlers.get(action)
        if not handler:
            return {
                'success': False,
                'result': '',
                'error': f"Acción desconocida: {action}"
            }
        
        return handler(context, language)
    
    def _detect_language(self, path: Path) -> str:
        """Auto-detecta el lenguaje del proyecto"""
        if (path / 'requirements.txt').exists() or (path / 'pyproject.toml').exists():
            return 'python'
        elif (path / 'package.json').exists():
            return 'node'
        elif (path / 'go.mod').exists():
            return 'go'
        elif (path / 'Gemfile').exists():
            return 'ruby'
        elif (path / 'pom.xml').exists() or (path / 'build.gradle').exists():
            return 'java'
        else:
            return 'unknown'
    
    def _generate_dockerfile(self, context: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Genera Dockerfile optimizado"""
        
        templates = {
            'python': self._dockerfile_python,
            'node': self._dockerfile_node,
            'go': self._dockerfile_go
        }
        
        template_func = templates.get(language)
        if not template_func:
            return {
                'success': False,
                'result': '',
                'error': f"Lenguaje no soportado: {language}"
            }
        
        dockerfile_content = template_func(context)
        
        if context.get('args', {}).get('save', False):
            dockerfile_path = context['current_dir'] / 'Dockerfile'
            dockerfile_path.write_text(dockerfile_content)
            result_msg = f"✅ Dockerfile creado: {dockerfile_path}"
        else:
            result_msg = "Dockerfile generado (no guardado)"
        
        return {
            'success': True,
            'result': result_msg,
            'data': {'content': dockerfile_content, 'language': language}
        }
    
    def _dockerfile_python(self, context: Dict[str, Any]) -> str:
        """Template Dockerfile para Python"""
        framework = context.get('args', {}).get('framework', 'fastapi')
        
        if framework == 'fastapi':
            return '''# Dockerfile optimizado para FastAPI
FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (cache de layers)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Usuario no-root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Puerto
EXPOSE 8000

# Comando
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
        elif framework == 'flask':
            return '''# Dockerfile optimizado para Flask
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
'''
        else:
            return '''# Dockerfile genérico para Python
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
'''
    
    def _dockerfile_node(self, context: Dict[str, Any]) -> str:
        """Template Dockerfile para Node.js"""
        return '''# Dockerfile optimizado para Node.js
FROM node:18-alpine AS builder

WORKDIR /app

# Copiar package files
COPY package*.json ./
RUN npm ci --only=production

# Build stage
FROM node:18-alpine

WORKDIR /app

# Copiar dependencias del builder
COPY --from=builder /app/node_modules ./node_modules
COPY . .

# Usuario no-root
RUN addgroup -g 1001 -S nodejs && adduser -S nodejs -u 1001
USER nodejs

EXPOSE 3000

CMD ["node", "index.js"]
'''
    
    def _dockerfile_go(self, context: Dict[str, Any]) -> str:
        """Template Dockerfile para Go"""
        return '''# Dockerfile multi-stage para Go
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copiar go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copiar código y compilar
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .

# Runtime stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

COPY --from=builder /app/main .

EXPOSE 8080

CMD ["./main"]
'''
    
    def _generate_compose(self, context: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Genera docker-compose.yml"""
        
        compose_content = '''version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENV=production
    volumes:
      - .:/app
    restart: unless-stopped

  # redis:
  #   image: redis:alpine
  #   ports:
  #     - "6379:6379"
  
  # postgres:
  #   image: postgres:15-alpine
  #   environment:
  #     POSTGRES_PASSWORD: password
  #     POSTGRES_DB: myapp
  #   ports:
  #     - "5432:5432"
  #   volumes:
  #     - postgres_data:/var/lib/postgresql/data

# volumes:
#   postgres_data:
'''
        
        if context.get('args', {}).get('save', False):
            compose_path = context['current_dir'] / 'docker-compose.yml'
            compose_path.write_text(compose_content)
            result_msg = f"✅ docker-compose.yml creado: {compose_path}"
        else:
            result_msg = "docker-compose.yml generado (no guardado)"
        
        return {
            'success': True,
            'result': result_msg,
            'data': {'content': compose_content}
        }
    
    def _generate_dockerignore(self, context: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Genera .dockerignore"""
        
        templates = {
            'python': '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.pytest_cache/
.coverage
htmlcov/
*.egg-info/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Git
.git/
.gitignore

# Docs
docs/
*.md

# Tests
tests/
test_*.py

# CI/CD
.github/
.gitlab-ci.yml
''',
            'node': '''# Node
node_modules/
npm-debug.log
yarn-error.log
.npm/
.yarn/

# IDE
.vscode/
.idea/
*.swp

# Git
.git/
.gitignore

# Docs
docs/
*.md

# Tests
tests/
**/*.test.js
**/*.spec.js

# CI/CD
.github/
.gitlab-ci.yml
''',
            'go': '''# Go
*.exe
*.exe~
*.dll
*.so
*.dylib
*.test
*.out
vendor/

# IDE
.vscode/
.idea/
*.swp

# Git
.git/
.gitignore

# Docs
docs/
*.md

# Tests
*_test.go

# CI/CD
.github/
.gitlab-ci.yml
'''
        }
        
        content = templates.get(language, templates['python'])
        
        if context.get('args', {}).get('save', False):
            dockerignore_path = context['current_dir'] / '.dockerignore'
            dockerignore_path.write_text(content)
            result_msg = f"✅ .dockerignore creado: {dockerignore_path}"
        else:
            result_msg = ".dockerignore generado (no guardado)"
        
        return {
            'success': True,
            'result': result_msg,
            'data': {'content': content}
        }
    
    def _generate_all(self, context: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Genera todos los archivos Docker"""
        results = []
        
        dockerfile_result = self._generate_dockerfile(context, language)
        results.append(dockerfile_result)
        
        compose_result = self._generate_compose(context, language)
        results.append(compose_result)
        
        dockerignore_result = self._generate_dockerignore(context, language)
        results.append(dockerignore_result)
        
        all_success = all(r['success'] for r in results)
        
        if all_success:
            return {
                'success': True,
                'result': '✅ Todos los archivos Docker generados',
                'data': {
                    'dockerfile': dockerfile_result['data'],
                    'compose': compose_result['data'],
                    'dockerignore': dockerignore_result['data']
                }
            }
        else:
            errors = [r['error'] for r in results if not r['success']]
            return {
                'success': False,
                'result': '',
                'error': '; '.join(errors)
            }
