# ⚡ INÍCIO RÁPIDO - 5 MINUTOS

## 🚀 Comece Aqui

```bash
# 1. Entrar na pasta
cd PraiasSP-Tools

# 2. Criar virtual environment
python -m venv venv

# 3. Ativar (escolha um)
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Instalar
pip install -r requirements.txt

# 5. Testar
bash test.sh

# 6. Rodar
python api/index.py

# 7. Abrir navegador
# http://localhost:5000
```

## ✅ Se der erro

1. **Instalar Python 3.11+**

   - https://www.python.org/downloads/

2. **Instalar pip**

   ```bash
   python -m pip install --upgrade pip
   ```

3. **Se porta 5000 está em uso**

   ```bash
   # Windows
   netstat -ano | findstr :5000
   taskkill /PID <PID> /F

   # macOS/Linux
   lsof -ti:5000 | xargs kill -9
   ```

4. **Se há erro de permissão**
   ```bash
   chmod +x test.sh
   chmod +x build.sh
   chmod +x deploy.sh
   ```

## 📚 Próximo Passo

Ler `README.md` para documentação completa.

---

**Tudo funcionando?** Parabéns! 🎉

Você agora tem a base do Riviera Ingestor rodando localmente.
