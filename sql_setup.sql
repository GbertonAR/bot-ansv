-- SQL para crear la tabla 'roles'
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_rol TEXT UNIQUE NOT NULL,
    descripcion TEXT
);

-- SQL para insertar roles iniciales (solo si no existen)
-- Puedes ejecutar estas sentencias una por una o en un bloque,
-- dependiendo de tu cliente de SQLite.
INSERT OR IGNORE INTO roles (id, nombre_rol, descripcion) VALUES (1, 'Usuario Estandar', 'Usuario general del bot.');
INSERT OR IGNORE INTO roles (id, nombre_rol, descripcion) VALUES (2, 'Agente de Soporte', 'Encargado de gestionar tickets de soporte.');
INSERT OR IGNORE INTO roles (id, nombre_rol, descripcion) VALUES (3, 'Administrador Global', 'Acceso completo a la gestión del bot y reportes.');
INSERT OR IGNORE INTO roles (id, nombre_rol, descripcion) VALUES (4, 'Operador CEL', 'Personal que opera en un Centro Emisor de Licencias.');
INSERT OR IGNORE INTO roles (id, nombre_rol, descripcion) VALUES (5, 'Instructor CEL', 'Personal instructor en un Centro Emisor de Licencias.');
INSERT OR IGNORE INTO roles (id, nombre_rol, descripcion) VALUES (6, 'Prestador', 'Tercero que presta servicios en el proceso de LNC.');

-- SQL para crear la tabla 'usuarios'
CREATE TABLE IF NOT EXISTS usuarios (
    id TEXT PRIMARY KEY,
    nombre TEXT,
    email TEXT NOT NULL,
    celular TEXT NOT NULL,
    id_municipio INTEGER,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_rol INTEGER NOT NULL DEFAULT 1, -- Por defecto 'Usuario Estandar'
    FOREIGN KEY (id_municipio) REFERENCES municipios(id),
    FOREIGN KEY (id_rol) REFERENCES roles(id)
);

-- SQL para crear la tabla 'interacciones_log'
CREATE TABLE IF NOT EXISTS interacciones_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario TEXT NOT NULL,
    timestamp_consulta DATETIME DEFAULT CURRENT_TIMESTAMP,
    tipo_consulta TEXT NOT NULL,
    texto_consulta TEXT NOT NULL,
    timestamp_respuesta DATETIME,
    texto_respuesta TEXT,
    tiempo_respuesta_ms INTEGER,
    modelo_ia_usado TEXT,
    relevancia_ia INTEGER,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
);

-- SQL para crear la tabla 'tickets'
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario TEXT NOT NULL,
    asunto TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    estado TEXT NOT NULL DEFAULT 'Abierto', -- 'Abierto', 'En Proceso', 'Cerrado', 'Pendiente'
    prioridad TEXT NOT NULL DEFAULT 'Media', -- 'Baja', 'Media', 'Alta', 'Urgente'
    id_agente_asignado TEXT,
    fecha_cierre DATETIME,
    comentarios_cierre TEXT,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
    FOREIGN KEY (id_agente_asignado) REFERENCES usuarios(id)
);

-- SQL para crear la tabla 'parametros_seteos'
CREATE TABLE IF NOT EXISTS parametros_seteos (
    clave TEXT PRIMARY KEY NOT NULL,
    valor TEXT,
    descripcion TEXT
);

-- SQL para insertar parámetros iniciales (solo si no existen)
INSERT OR IGNORE INTO parametros_seteos (clave, valor, descripcion) VALUES
('ENTORNO_EJECUCION', 'LOCAL', 'Define el entorno de ejecución del bot (LOCAL o AZURE).'),
('BOT_PORT', '8850', 'Puerto en el que se ejecuta el servidor web del bot.'),
('AZURE_OPENAI_ENDPOINT', 'TU_AZURE_OPENAI_ENDPOINT', 'URL del endpoint de Azure OpenAI (ej. https://turesource.openai.azure.com/).'),
('AZURE_OPENAI_CHAT_MODEL_NAME', 'gpt-35-turbo', 'Nombre del despliegue del modelo de chat en Azure OpenAI.'),
('AZURE_OPENAI_EMBEDDING_MODEL_NAME', 'text-embedding-ada-002', 'Nombre del despliegue del modelo de embeddings en Azure OpenAI.'),
('ORG_NOMBRE', 'Agencia Nacional de Seguridad Vial (ANSV)', 'Nombre de la organización.'),
('ORG_DIRECCION', 'Av. Santa Fe 1234, CABA', 'Dirección física de la organización.'),
('ORG_EMAIL', 'contacto@ansv.gob.ar', 'Dirección de correo electrónico de contacto de la organización.');
