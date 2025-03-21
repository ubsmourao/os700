# database.py
from supabase_client import supabase
import bcrypt

def check_or_create_admin_user():
    try:
        resp = supabase.table("usuarios").select("username").eq("username", "admin").execute()
        if not resp.data:
            admin_password = "admin"  # Altere para algo mais seguro
            hashed = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            supabase.table("usuarios").insert({"username": "admin", "password": hashed, "role": "admin"}).execute()
            print("Usuário 'admin' criado com sucesso.")
        else:
            print("Usuário 'admin' já existe.")
    except Exception as e:
        print(f"Erro ao verificar/criar admin: {e}")
