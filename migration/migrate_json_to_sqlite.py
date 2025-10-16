"""
Script para migrar memoria de JSON a SQLite.
Ejecutar una sola vez durante la transición.

Uso:
    python3 -m migration.migrate_json_to_sqlite
"""
import sys
import json
import uuid
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.memory.sqlite_memory_manager import SQLiteMemoryManager
from agents.memory.models import Message
from utils.logger import setup_logger

logger = setup_logger(__name__)


def migrate_json_to_sqlite():
    """Migra memory.json a memory.db"""
    
    json_path = Path("agents/memory/memory.json")
    backup_path = Path("agents/memory/memory.json.backup")
    db_path = Path("agents/memory/memory.db")
    
    if not json_path.exists():
        logger.warning("No existe memory.json, nada que migrar")
        print("⚠️  No se encontró agents/memory/memory.json")
        return
    
    if db_path.exists():
        response = input("⚠️  La base de datos ya existe. ¿Sobrescribir? (s/N): ")
        if response.lower() != 's':
            print("Migración cancelada")
            return
        db_path.unlink()
    
    logger.info(f"Creando backup en {backup_path}")
    print(f"📦 Creando backup en {backup_path}")
    import shutil
    shutil.copy2(json_path, backup_path)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"JSON cargado: {len(data)} mensajes")
    print(f"📄 JSON cargado: {len(data)} mensajes")
    
    manager = SQLiteMemoryManager(db_path)
    session_id = str(uuid.uuid4())
    
    print(f"🔄 Migrando mensajes...")
    migrated = 0
    errors = 0
    
    for item in data:
        try:
            message = Message(
                role=item.get('role', 'user'),
                content=item.get('content', ''),
                timestamp=item.get('timestamp', datetime.now().isoformat()),
                session_id=session_id,
                tokens=item.get('tokens'),
                metadata=item.get('metadata')
            )
            
            manager.add_message(message)
            migrated += 1
            
            if migrated % 10 == 0:
                print(f"  Migrados: {migrated}/{len(data)}", end='\r')
            
        except Exception as e:
            logger.error(f"Error migrando mensaje: {e}")
            errors += 1
    
    print(f"\n✅ Migración completada: {migrated} mensajes")
    if errors > 0:
        print(f"⚠️  Errores: {errors}")
    
    logger.info(f"Migración completada: {migrated} mensajes, {errors} errores")
    logger.info(f"Session ID: {session_id}")
    logger.info(f"Backup guardado en: {backup_path}")
    
    summary = manager.get_session_summary(session_id)
    if summary:
        print(f"\n📊 Resumen de la sesión migrada:")
        print(f"  Session ID: {session_id}")
        print(f"  Mensajes totales: {summary.message_count}")
        print(f"  Tokens totales: {summary.total_tokens}")
        print(f"  Primer mensaje: {summary.first_message}")
        print(f"  Último mensaje: {summary.last_message}")
    
    stats = manager.get_stats()
    print(f"\n📈 Estadísticas globales:")
    print(f"  Total mensajes: {stats['total_messages']}")
    print(f"  Total sesiones: {stats['total_sessions']}")
    print(f"  Tamaño DB: {stats['db_size_kb']:.2f} KB")
    
    print(f"\n💾 Base de datos creada: {db_path}")
    print(f"📦 Backup guardado: {backup_path}")
    print("\n✨ Puedes eliminar memory.json si todo funciona correctamente")


if __name__ == "__main__":
    try:
        migrate_json_to_sqlite()
    except KeyboardInterrupt:
        print("\n\n⏸️  Migración interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.exception("Error en migración")
        print(f"\n❌ Error fatal: {e}")
        print("Ver logs/patcode.log para más detalles")
        sys.exit(1)
