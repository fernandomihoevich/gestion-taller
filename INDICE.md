# 🚀 CONFIGURAR APP PARA LA WEB - ÍNDICE COMPLETO

## 📚 Documentos en la Carpeta

| Archivo | Propósito | Lee si... |
|---------|----------|----------|
| **QUICK_START.md** | ⚡ Plan en 5 min | Tienes prisa y quieres ir rápido |
| **GUIA_SUPABASE.md** | 📖 Guía detallada | Prefieres instrucciones paso a paso |
| **.streamlit/secrets_example.toml** | 🔑 Configuración | Necesitas ver dónde poner la URL |
| **requirements.txt** | 📦 Dependencias | Ya tiene psycopg2-binary |
| **app.py** | 💻 Código | ✅ NO necesita cambios |

---

## 🎯 Flujo Rápido (30 min total)

### 1️⃣ Crear Base de Datos en Supabase (10 min)
👉 [GUIA_SUPABASE.md - PASO 1 y 2](GUIA_SUPABASE.md#paso-1-crear-proyecto-en-supabase-5-minutos)

### 2️⃣ Configurar Localmente (5 min)
👉 [GUIA_SUPABASE.md - PASO 3b](GUIA_SUPABASE.md#paso-3b-editar-el-archivo-streamlitsecrettoml-en-tu-pc)

### 3️⃣ Subir a GitHub (5 min)
👉 [QUICK_START.md - PASO 4](QUICK_START.md#paso-4-subir-a-github--1-min)

### 4️⃣ Publicar en Streamlit Cloud (Automático, 5 min)
👉 [QUICK_START.md - PASO 5](QUICK_START.md#paso-5-deploy-a-streamlit-cloud-automático)

---

## ✨ Lo Mejor

✅ Tu código **NO cambia**  
✅ Sigue funcionando con SQLite en tu PC  
✅ Usa PostgreSQL automáticamente en Streamlit Cloud  
✅ Los datos se guardan en Supabase (base de datos profesional)  

---

## 📝 Archivo `.streamlit/secrets.toml` (Para tu PC)

```toml
DATABASE_URL = "postgresql://postgres:TU_CONTRASEÑA@db.xxxxx.supabase.co:5432/postgres"
```

**Cómo obtener estos datos:**
1. Ve a tu proyecto en Supabase
2. Settings → Database
3. Connection String → Python
4. Copia la URL y reemplaza en el archivo

---

## 🚀 Comando para Instalar y Probar

```powershell
cd c:\Users\Usuario\Documents\Gestion_taller

# 1. Instalar dependencia PostgreSQL
pip install psycopg2-binary

# 2. Probar localmente (seguirá usando SQLite)
streamlit run app.py

# 3. Subir a GitHub
git init
git add .
git commit -m "Ready for web"
git remote add origin https://github.com/TU_USUARIO/gestion-taller.git
git branch -M main
git push -u origin main
```

---

## 🔗 Enlaces Importantes

- **Supabase:** https://supabase.com
- **Streamlit Cloud:** https://share.streamlit.io
- **GitHub:** https://github.com (necesitas crear repo)

---

## ❓ ¿Qué Necesitas Hacer AHORA?

1. [ ] Leer `QUICK_START.md` o `GUIA_SUPABASE.md`
2. [ ] Crear cuenta en Supabase
3. [ ] Crear proyecto y obtener connection string
4. [ ] Editar `.streamlit/secrets.toml` localmente
5. [ ] Probar con `streamlit run app.py`
6. [ ] Hacer `git push` a GitHub
7. [ ] Deployar en Streamlit Cloud

**Tiempo total: ~30 minutos** ⏱️

---

## 💬 Notas

- El archivo `secrets.toml` que crees localmente **nunca se sube a GitHub** (está en .gitignore)
- Streamlit Cloud tiene su propio panel para agregar secrets
- Tu app detectará automáticamente si está local (SQLite) o en la nube (PostgreSQL)
- Los datos en Supabase persisten entre updates automáticos

¡**Vamos a publicar tu app!** 🚀
