import bcrypt
from supabase_client import supabase

def authenticate(username, password):
    """
    Verifica se 'username' existe na tabela 'usuarios' e se a senha 'password'
    confere com o hash armazenado (bcrypt).
    Retorna True se autenticar, caso contrário False.
    """
    try:
        resp = supabase.table("usuarios").select("password").eq("username", username).execute()
        data = resp.data
        if data:
            stored = data[0]['password']  # Hash armazenado como string
            # Converte para bytes se for string
            if isinstance(stored, str):
                stored = stored.encode('utf-8')
            # Verifica a senha com bcrypt
            if bcrypt.checkpw(password.encode('utf-8'), stored):
                return True
        return False
    except Exception as e:
        print(f"Erro na autenticação: {e}")
        return False

def add_user(username, password, is_admin=False):
    """
    Cria um novo usuário no Supabase com 'role=user' ou 'role=admin'.
    Armazena a senha usando bcrypt.
    Retorna True se bem-sucedido, caso contrário False.
    """
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
    """
    Retorna True se o usuário tiver role='admin', senão False.
    """
    try:
        resp = supabase.table("usuarios").select("role").eq("username", username).execute()
        data = resp.data
        return data and data[0]['role'] == 'admin'
    except Exception as e:
        print(f"Erro ao verificar admin: {e}")
        return False

def list_users():
    """
    Retorna uma lista de tuplas (username, role) de todos os usuários.
    """
    try:
        resp = supabase.table("usuarios").select("username, role").execute()
        return [(u["username"], u["role"]) for u in resp.data]
    except Exception as e:
        print(f"Erro ao listar usuários: {e}")
        return []

def change_password(username, old_password, new_password):
    """
    Permite que o usuário troque a própria senha,
    exigindo a senha antiga para autenticação.
    """
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
    """
    Remove um usuário, desde que 'admin_username' seja admin.
    """
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

def update_user_role(admin_username, target_username, new_role):
    """
    Admin altera a role de um usuário (user ou admin).
    """
    if not is_admin(admin_username):
        print("Apenas admins podem alterar função de usuários.")
        return False
    try:
        supabase.table("usuarios").update({"role": new_role}).eq("username", target_username).execute()
        print(f"Função do usuário '{target_username}' atualizada para '{new_role}'.")
        return True
    except Exception as e:
        print(f"Erro ao atualizar função do usuário: {e}")
        return False