# autenticacao.py

import bcrypt
from supabase_client import supabase

def authenticate(username, password):
    """
    Verifica se 'username' existe na tabela 'usuarios' do Supabase
    e se a senha 'password' confere com o hash armazenado (bcrypt).
    Retorna True se autenticar, False caso contrário.
    """
    try:
        resp = supabase.table("usuarios").select("password").eq("username", username).execute()
        data = resp.data
        if data:
            stored = data[0]['password']  # Hash armazenado como string
            # Converte para bytes se necessário
            if isinstance(stored, str):
                stored = stored.encode('utf-8')
            # Verifica a senha
            if bcrypt.checkpw(password.encode('utf-8'), stored):
                return True
        return False
    except Exception as e:
        print(f"Erro na autenticação: {e}")
        return False

def add_user(username, password, is_admin=False):
    """
    Cria um novo usuário na tabela 'usuarios'.
    - username: nome de usuário
    - password: senha em texto puro (será hasheada com bcrypt)
    - is_admin: se True, role='admin'; senão 'user'
    Retorna True se criar com sucesso, False se falhar.
    """
    try:
        # Verifica se já existe
        resp = supabase.table("usuarios").select("username").eq("username", username).execute()
        if resp.data:
            print("Usuário já existe.")
            return False
        
        # Hash da senha
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
    Retorna True se o usuário tiver role='admin', caso contrário False.
    """
    try:
        resp = supabase.table("usuarios").select("role").eq("username", username).execute()
        data = resp.data
        if data and data[0]['role'] == 'admin':
            return True
        return False
    except Exception as e:
        print(f"Erro ao verificar admin: {e}")
        return False

def list_users():
    """
    Retorna uma lista de tuplas (username, role) para cada usuário.
    """
    try:
        resp = supabase.table("usuarios").select("username, role").execute()
        return [(u["username"], u["role"]) for u in resp.data]
    except Exception as e:
        print(f"Erro ao listar usuários: {e}")
        return []

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

def force_change_password(admin_username, target_username, new_password):
    """
    Permite que o admin troque a senha de qualquer usuário sem precisar da senha antiga.
    """
    if not is_admin(admin_username):
        print("Apenas administradores podem alterar a senha de usuários.")
        return False
    try:
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        supabase.table("usuarios").update({"password": hashed}).eq("username", target_username).execute()
        print(f"Senha do usuário '{target_username}' atualizada pelo admin '{admin_username}'.")
        return True
    except Exception as e:
        print(f"Erro ao forçar alteração de senha: {e}")
        return False