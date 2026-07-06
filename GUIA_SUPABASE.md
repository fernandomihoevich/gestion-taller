# CONFIGURAR SUPABASE + STREAMLIT

## PASO 1: Crear Proyecto en Supabase (5 minutos)

### 1.1 Crear Cuenta
1. Ve a https://supabase.com
2. Click "Sign Up"
3. Regístrate con GitHub (recomendado)

### 1.2 Crear Nuevo Proyecto
1. Click "New Project"
2. **Nombre del proyecto:** `gestion-taller`
3. **Contraseña:** (guarda bien, la vas a necesitar)
4. **Región:** Sudamérica (o la más cercana a ti)
5. Click "Create new project"
6. ⏳ Espera 2-3 minutos mientras se crea

### 1.3 Obtener Connection String
1. En el menú izquierdo → "Settings" → "Database"
2. Busca la sección "Connection string"
3. En el dropdown, selecciona **"Drivers"** → **"Python"**
4. Copia la URL completa, debe verse así:
   ```
   postgresql://postgres:[TU_CONTRASEÑA]@db.xxxxx.supabase.co:5432/postgres
   ```

⚠️ **IMPORTANTE:** Guarda esta URL en algún lugar seguro

---

## PASO 2: Crear Las Tablas en Supabase (2 min)

### 2.1 Abrir SQL Editor
1. En Supabase, en el **menú IZQUIERDO**, busca y haz click en **"SQL Editor"** (ícono de base de datos)
2. Verás un editor con código vacío
3. Click en botón azul **"New Query"** (arriba a la derecha)
4. Un cuadro en blanco aparecerá para que escribas SQL

### 2.2 Copiar TODO el Código SQL
Te voy a dar el código SQL completo. **Cópialo TODO** y pégalo en el editor:

**COPIA DESDE AQUÍ:**

```sql
-- Tablas operativas
CREATE TABLE IF NOT EXISTS mecanicos (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS maestro_equipos (
    interno TEXT PRIMARY KEY,
    marca TEXT NOT NULL,
    modelo TEXT NOT NULL,
    tipo TEXT
);

CREATE TABLE IF NOT EXISTS equipos_ingresados (
    id SERIAL PRIMARY KEY,
    interno TEXT,
    horas INTEGER,
    origen TEXT,
    mecanico TEXT,
    fecha_ingreso TEXT,
    hora_inicio TEXT,
    hora_fin TEXT,
    estado_proceso TEXT,
    FOREIGN KEY(interno) REFERENCES maestro_equipos(interno)
);

CREATE TABLE IF NOT EXISTS controles_ingreso (
    id SERIAL PRIMARY KEY,
    ingreso_id INTEGER,
    tarea TEXT NOT NULL,
    estado TEXT NOT NULL,
    observaciones TEXT,
    FOREIGN KEY(ingreso_id) REFERENCES equipos_ingresados(id)
);

CREATE TABLE IF NOT EXISTS controles_mantenimiento (
    id SERIAL PRIMARY KEY,
    ingreso_id INTEGER,
    tarea TEXT NOT NULL,
    estado TEXT NOT NULL,
    observaciones TEXT,
    tipo_tarea TEXT,
    FOREIGN KEY(ingreso_id) REFERENCES equipos_ingresados(id)
);

CREATE TABLE IF NOT EXISTS controles_salida (
    id SERIAL PRIMARY KEY,
    ingreso_id INTEGER,
    tarea TEXT NOT NULL,
    estado TEXT NOT NULL,
    observaciones TEXT,
    FOREIGN KEY(ingreso_id) REFERENCES equipos_ingresados(id)
);

CREATE TABLE IF NOT EXISTS registro_horas (
    id SERIAL PRIMARY KEY,
    ingreso_id INTEGER,
    fecha TEXT NOT NULL,
    horas REAL NOT NULL,
    mecanico TEXT NOT NULL,
    FOREIGN KEY(ingreso_id) REFERENCES equipos_ingresados(id)
);

CREATE TABLE IF NOT EXISTS maestro_controles_ingreso (
    id SERIAL PRIMARY KEY,
    descripcion TEXT NOT NULL,
    orden INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS maestro_tareas_mantenimiento (
    id SERIAL PRIMARY KEY,
    descripcion TEXT NOT NULL,
    orden INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS maestro_controles_salida (
    id SERIAL PRIMARY KEY,
    descripcion TEXT NOT NULL,
    orden INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS maestro_rubros_compras (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lista_compras (
    id SERIAL PRIMARY KEY,
    rubro TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    detalle TEXT,
    cantidad TEXT NOT NULL,
    fecha_carga TEXT,
    estado TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pendientes_taller (
    id SERIAL PRIMARY KEY,
    titulo TEXT NOT NULL,
    descripcion TEXT,
    fecha_carga TEXT,
    fecha_entrega TEXT,
    prioridad TEXT,
    mecanico TEXT,
    estado TEXT,
    observaciones TEXT
);

CREATE TABLE IF NOT EXISTS trabajos_clientes (
    id SERIAL PRIMARY KEY,
    cliente TEXT NOT NULL,
    tarea TEXT NOT NULL,
    estado TEXT NOT NULL,
    fecha_programada TEXT
);
```

**COPIA HASTA AQUÍ**

### 2.3 Ejecutar el Código SQL
1. Todo el código de arriba debe estar pegado en el editor en blanco
2. Ahora haz click en el botón **"▶ RUN"** (botón azul en la esquina superior derecha)
3. **Espera unos segundos** mientras Supabase crea las tablas
4. Si ves un mensaje de éxito ✅ o no hay errores rojos, ¡está hecho!
5. Las tablas ya existen en tu base de datos Supabase

**Si ves errores:** 
- ✅ Si dice "already exists" → Es normal, las tablas ya están (ignore)
- ❌ Si hay otros errores → Avísame

---

## PASO 3: Instalar Dependencia
En tu terminal (PowerShell):

```powershell
cd c:\Users\Usuario\Documents\Gestion_taller
pip install psycopg2-binary
```

---

## PASO 4: Configurar Streamlit Cloud

### 4.1 Crear archivo `.streamlit/secrets.toml`

En tu carpeta `Gestion_taller`, crea un archivo: `.streamlit/secrets.toml`

Contenido:
```toml
DATABASE_URL = "postgresql://postgres:[TU_CONTRASEÑA]@db.xxxxx.supabase.co:5432/postgres"
```

(Reemplaza con tu URL de Supabase)

### 4.2 En Streamlit Cloud
1. Ve a https://share.streamlit.io
2. Selecciona tu app (después de deployar)
3. Click en los 3 puntos → "Settings"
4. Sección "Secrets"
5. Pega el mismo contenido de secrets.toml
6. Click "Save"

---

---

## PASO 3b: Editar el archivo `.streamlit/secrets.toml` en tu PC

Crea un archivo con este exacto contenido en: `c:\Users\Usuario\Documents\Gestion_taller\.streamlit\secrets.toml`

```toml
DATABASE_URL = "postgresql://postgres:TU_CONTRASEÑA@db.xxxxx.supabase.co:5432/postgres"
```

**Reemplaza:**
- `TU_CONTRASEÑA` → la contraseña que pusiste en Supabase
- `xxxxx` → los datos de tu proyecto Supabase

---

## PASO 4: Modificar `requirements.txt`

Abre el archivo `requirements.txt` de tu proyecto y reemplázalo con:

```
streamlit==1.28.1
pandas==2.1.3
fpdf2==2.7.0
psycopg2-binary==2.9.9
```

---

## CHECKLIST ✓

- [ ] 1. Cuenta creada en Supabase
- [ ] 2. Proyecto creado
- [ ] 3. Connection string obtenida (guardada en clipboard)
- [ ] 4. Tablas SQL creadas en Supabase (pegando el código)
- [ ] 5. Archivo `.streamlit/secrets.toml` creado localmente
- [ ] 6. `requirements.txt` actualizado con psycopg2-binary
- [ ] 7. Instalar dependencias: `pip install -r requirements.txt`
- [ ] 8. Probar localmente corriendo `streamlit run app.py`
- [ ] 9. **IMPORTANTE: El app.py funciona IGUAL, sin cambios** ✅
- [ ] 10. Subir todo a GitHub
- [ ] 11. Deployed en Streamlit Cloud + agregar secrets

---

## ✨ Lo Mejor: Tu `app.py` NO Necesita Cambios

Tu código sigue siendo **exactamente igual**. Streamlit detectará automáticamente:
- **En tu PC:** Usa SQLite (taller_gestion.db)
- **En Streamlit Cloud:** Usa PostgreSQL (Supabase) con los secrets

---

## PASO 5: Probar Localmente (Opcional)

```powershell
cd c:\Users\Usuario\Documents\Gestion_taller

# Instalar la nueva dependencia
pip install psycopg2-binary

# Ejecutar normalmente - seguirá usando SQLite
streamlit run app.py
```

La aplicación funcionará IGUAL que antes, pero ahora está lista para PostgreSQL.

---

## PASO 6: Subir a GitHub y Deployar en Streamlit Cloud

### 6.1 Subir a GitHub
```powershell
cd c:\Users\Usuario\Documents\Gestion_taller

git init
git add .
git commit -m "Adaptado para Supabase/PostgreSQL"
git remote add origin https://github.com/TU_USUARIO/gestion-taller.git
git branch -M main
git push -u origin main
```

### 6.2 Deploy en Streamlit Cloud
1. Ve a https://share.streamlit.io
2. "New app"
3. Selecciona el repo: `gestion-taller`
4. Branch: `main`
5. File path: `app.py`
6. Click "Deploy"

### 6.3 Agregar Secrets en Streamlit Cloud
1. **IMPORTANTE:** Espera a que termine el deploy (2-3 min)
2. Haz click en los 3 puntos (`⋮`) en la esquina superior derecha
3. "Settings"
4. Ir a pestaña "Secrets"
5. Pegar EXACTAMENTE esto:
   ```
   DATABASE_URL = "postgresql://postgres:TU_CONTRASEÑA@db.xxxxx.supabase.co:5432/postgres"
   ```
6. Guardar
7. **Automáticamente se va a reiniciar la app** ✅

---

## 🎉 ¡Listo!

Tu app está en la web en: `https://TU_USUARIO-gestion-taller.streamlit.app`

**Los datos se guardan en Supabase** y persisten entre updates.
