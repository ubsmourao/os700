# autenticacao.py
# autenticacao.py
import bcrypt
from supabase_client import supabase

def authenticate(username, password):
    try:
        resp = supabase.table("usuarios").select("password").eq("username", username).execute()
        data = resp.data
        if data:
            stored = data[0]['password']
            if isinstance(stored, str):
                stored = stored.encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), stored):
                return True
        return False
    except Exception as e:
        print(f"Erro na autenticação: {e}")
        return False

def add_user(username, password, is_admin=False):
    try:
        # Verifica se já existe
        resp = supabase.table("usuarios").select("username").eq("username", username).execute()
        if resp.data:
            print("Usuário já existe.")
            return False
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        role = 'admin' if is_admin else 'user'
        supabase.table("usuarios").insert({"username": username, "password": hashed, "role": role}).execute()
        print(f"Usuário '{username}' criado como {role}.")
        return True
    except Exception as e:
        print(f"Erro ao adicionar usuário: {e}")
        return False

def is_admin(username):
    try:
        resp = supabase.table("usuarios").select("role").eq("username", username).execute()
        data = resp.data
        return data and data[0]['role'] == 'admin'
    except Exception as e:
        print(f"Erro ao verificar admin: {e}")
        return False

def list_users():
    try:
        resp = supabase.table("usuarios").select("username, role").execute()
        return [(u["username"], u["role"]) for u in resp.data]
    except Exception as e:
        print(f"Erro ao listar usuários: {e}")
        return []

def change_password(username, old_password, new_password):
    if authenticate(username, old_password):
        try:
            new_hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            supabase.table("usuarios").update({"password": new_hashed}).eq("username", username).execute()
            print("Senha alterada com sucesso.")
            return True
        except Exception as e:
            print(f"Erro ao alterar senha: {e}")
            return False
    else:
        print("Senha antiga incorreta.")
        return False

def remove_user(admin_username, target_username):
    if is_admin(admin_username):
        try:
            supabase.table("usuarios").delete().eq("username", target_username).execute()
            print(f"Usuário '{target_username}' removido.")
            return True
        except Exception as e:
            print(f"Erro ao remover usuário: {e}")
            return False
    else:
        print("Apenas admins podem remover usuários.")
        return False
