-- Plantilla semilla usada por ESP-08 mientras no existan plantillas específicas por fuente (ESP-13).
INSERT INTO prompt_template (category, identifier, name, template, created_by, updated_by)
VALUES (
    'vigilancia',
    'generico',
    'Clasificación genérica de vigilancia',
    'Clasifica la siguiente noticia contra el catálogo de componentes de OneWatch.\n\nTítulo: {titulo}\nTexto: {texto}',
    'seed',
    'seed'
)
ON CONFLICT (category, identifier) DO NOTHING;
