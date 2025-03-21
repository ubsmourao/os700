# supabase_client.py
import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Configure SUPABASE_URL e SUPABASE_KEY nas variáveis de ambiente.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
