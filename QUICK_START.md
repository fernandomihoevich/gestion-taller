# ⚡ QUICK START - Publicar en la Web (5 Minutos)

## Paso 1: Crear BD en Supabase (5 min)

### 1.1 Crear Cuenta
1. Ve a https://supabase.com
2. Click "Sign Up" (arriba a la derecha)
3. Elige "Continue with GitHub" (es más fácil)
4. Autoriza a Supabase

### 1.2 Crear Nuevo Proyecto
1. En el dashboard, click en botón verde "New project"
2. Llenar el formulario:
   - **Name:** `gestion-taller`
   - **Password:** Algo como `MiSuperPassword123!` (guarda bien, lo vas a necesitar)
   - **Region:** Sudamérica (o la más cercana a ti)
3. Click "Create new project"

### 1.3 Esperar (2-3 minutos)
- Verás un mensaje "Creating your database..."
- **Espera pacientemente**, Supabase está creando el servidor

### 1.4 Obtener Connection String - PASO IMPORTANTE ⚠️

**Cuando termine de crear (te va a redirigir automáticamente), sigue estos pasos EXACTAMENTE:**

1. En el menú **IZQUIERDO**, haz click en **"Settings"** (ícono de engranaje)
   
2. En el submenu, haz click en **"Database"**

3. Baja hasta encontrar la sección **"Connection string"**

4. Verás un **dropdown** (selector) que dice **"Drivers"** o similar
   - Haz click y selecciona **"Python"**

5. Verás una línea de texto larga que empieza con `postgresql://`
   
6. **COPIA TODO** (Ctrl+C o click en el ícono de copiar)

**La URL debe verse así:**
```
postgresql://postgres:MiSuperPassword123!@db.xxxxx.supabase.co:5432/postgres
```

### 1.5 Guardar la URL
- Abre un **Bloc de Notas** o **Word**
- **PEGA la URL** que acabas de copiar
- **Guarda el archivo** con un nombre como `conexion_supabase.txt`
- **NO CIERRES este archivo**, lo vas a necesitar en pasos siguientes

## Paso 2: Crear Tablas en Supabase (1 min)

1. En Supabase: SQL Editor → New Query
2. Abre [GUIA_SUPABASE.md](GUIA_SUPABASE.md#paso-2-crear-las-tablas-en-supabase) → copia TODO el código SQL
3. Click "Run"
4. ✅ Tablas creadas

## Paso 3: Configurar Localmente (1 min)

**IMPORTANTE:** Tu `app.py` no necesita cambios - funciona igual

```powershell
cd c:\Users\Usuario\Documents\Gestion_taller

# Instalar dependencia
pip install psycopg2-binary

# Editar archivo secrets.toml (solo REEMPLAZAR contraseña y dominio)
# c:\Users\Usuario\Documents\Gestion_taller\.streamlit\secrets.toml
```

Contenido de `secrets.toml`:
```toml
DATABASE_URL = "postgresql://postgres:TU_CONTRASEÑA@db.xxxxx.supabase.co:5432/postgres"
```

Prueba localmente:
```powershell
streamlit run app.py
```

## Paso 4: Subir a GitHub (< 1 min)

```powershell
git init
git add .
git commit -m "Ready for web"
git remote add origin https://github.com/TU_USUARIO/gestion-taller.git
git branch -M main
git push -u origin main
```

## Paso 5: Deploy a Streamlit Cloud (3 min)

### 5.1 Abrir Streamlit Cloud
1. Ve a https://share.streamlit.io
2. Haz login con tu cuenta de GitHub (la misma que usaste para crear el repo)

### 5.2 Crear Nueva App
1. Click en botón azul "New app" (arriba a la derecha)
2. En el formulario:
   - **Repository:** `TU_USUARIO/gestion-taller` (selecciona de la lista)
   - **Branch:** `main`
   - **File path:** `app.py`
3. Click "Deploy"
4. ⏳ **Espera 2-3 minutos** mientras se instalan las dependencias

### 5.3 Esperar a que Termines el Deploy
- La página mostrará "Your app is starting..."
- Cuando termines, verás tu app funcionando
- **NO hará nada aún** porque le falta la BD (falta el paso 6)

---

## Paso 6: Agregar Secrets en Streamlit Cloud (2 min)

### 6.1 Entrar a Configuración
1. En la esquina **SUPERIOR DERECHA** de tu app, haz click en los **3 puntos** (`⋮`)
2. Selecciona "Settings"

### 6.2 Ir a Pestaña Secrets
1. En el menú lateral izquierdo, haz click en **"Secrets"**
2. Verás un cuadro de texto con este contenido:
   ```
   # Everything in this section will be available as an environment
   # variable. See https://docs.streamlit.io/streamlit-cloud/get-started/deploy-an-app/connect-to-data-repositories-and-secrets#pass-secrets-to-your-app
   ```

### 6.3 Agregar Tu DATABASE_URL
1. **AL FINAL del texto** (después de ese comentario), agrega esto:
   ```toml
   DATABASE_URL = "postgresql://postgres:TU_CONTRASEÑA@db.xxxxx.supabase.co:5432/postgres"
   ```
   
   **Reemplaza:**
   - `TU_CONTRASEÑA` → la contraseña de Supabase
   - `xxxxx` → los números/letras de tu proyecto Supabase

2. Click en botón **"Save"** (abajo a la derecha)

### 6.4 ¡Listo!
- Streamlit **automáticamente reinicia** la app
- Ahora SÍ va a conectar a Supabase
- En **1-2 minutos** verás tu app funcionando
- URL final: `https://TU_USUARIO-gestion-taller.streamlit.app`

---

## 🎯 Resumen Visual Pasos 5 y 6

| Paso | Acción | Resultado |
|------|--------|-----------|
| 5.1 | Abrir share.streamlit.io | Conecta con GitHub |
| 5.2 | Click "New app" → Selecciona repo | Deploy comienza |
| 5.3 | Espera 2-3 min | App lista (pero sin BD) |
| 6.1 | ⋮ → Settings | Abre configuración |
| 6.2 | Click "Secrets" | Ve el editor de secrets |
| 6.3 | Pega DATABASE_URL | Agrega conexión a BD |
| 6.4 | Click "Save" | ✅ APP VIVA EN LA WEB |

---

## 📋 Checklist Rápido

- [ ] Supabase cuenta creada ✓
- [ ] Connection string copiada ✓
- [ ] Tablas SQL creadas en Supabase ✓
- [ ] secrets.toml editado localmente ✓
- [ ] `pip install psycopg2-binary` ✓
- [ ] Git configurado y pushed ✓
- [ ] Streamlit Cloud deployed ✓
- [ ] DATABASE_URL agregado en Secrets ✓

---

## ⚠️ Troubleshooting

**"Connection refused"** → Verifica que la URL en `secrets.toml` sea correcta (copia de Supabase)

**"Table already exists"** → Normal, Supabase las crea bien

**"Permission denied"** → Asegúrate de usar la URL correcta (username/password correcto)

**"Timeout"** → Streamlit puede tardar 5+ minutos el primer deploy

---

**¿Preguntas?** Abre `GUIA_SUPABASE.md` para instrucciones más detalladas paso a paso.
