import os
import json
import asyncio
from instagrapi import Client
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from models import Lead, Message, Tenant
import uuid
from datetime import datetime

class InstagramService:
    def __init__(self):
        self.clients = {} # {tenant_id: Client}

    def get_client(self, tenant: Tenant):
        if tenant.id in self.clients:
            return self.clients[tenant.id]
        
        client = Client()
        integ = tenant.integrations or {}
        username = integ.get("instagram_user")
        password = integ.get("instagram_password")
        
        if not username or not password:
            return None
            
        session_file = f"/home/skywork/workspace/{username}_session.json"
        if os.path.exists(session_file):
            client.load_settings(session_file)
            try:
                client.get_timeline_feed()
                self.clients[tenant.id] = client
                return client
            except:
                os.remove(session_file)
        
        try:
            client.login(username, password)
            client.dump_settings(session_file)
            self.clients[tenant.id] = client
            return client
        except Exception as e:
            print(f"Instagram login failed for {username}: {e}")
            return None

    async def sync_dms(self, db: Session, tenant_id: str):
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant: return
        
        cl = self.get_client(tenant)
        if not cl: return
        
        try:
            threads = cl.direct_threads(20)
            for thread in threads:
                user = thread.users[0]
                username = user.username
                full_name = user.full_name or username
                # O instagrapi expõe a foto do perfil no objeto user
                profile_pic = getattr(user, 'profile_pic_url', None)
                
                lead = db.query(Lead).filter(
                    Lead.tenant_id == tenant_id, 
                    Lead.phone == username,
                    Lead.channel == "instagram"
                ).first()
                
                if not lead:
                    lead = Lead(
                        tenant_id=tenant_id,
                        name=full_name,
                        phone=username,
                        channel="instagram",
                        origin="instagram",
                        pipeline_stage="novo"
                    )
                    db.add(lead)
                    db.flush()
                
                # ATUALIZAR FOTO E NOME SEMPRE
                lead.name = full_name
                pdata = dict(lead.profile_data or {})
                if profile_pic:
                    pdata['picture'] = str(profile_pic)
                pdata['instagram_user'] = username
                lead.profile_data = pdata
                flag_modified(lead, "profile_data")

                for msg in thread.messages[:15]:
                    # Verificar se a mensagem já existe
                    existing = db.query(Message).filter(
                        Message.lead_id == lead.id, 
                        Message.content == msg.text,
                        Message.created_at == msg.timestamp
                    ).first()
                    
                    if not existing and msg.text:
                        # Se o user_id da msg for igual ao do client logado, fomos nós (AI/Human)
                        sender_type = "ai" if str(msg.user_id) == str(cl.user_id) else "lead"
                        
                        new_msg = Message(
                            tenant_id=tenant_id,
                            lead_id=lead.id,
                            sender_type=sender_type,
                            content=msg.text,
                            created_at=msg.timestamp
                        )
                        db.add(new_msg)
                        lead.last_contact_at = msg.timestamp
            
            db.commit()
        except Exception as e:
            print(f"Error syncing Instagram DMs: {e}")

    def send_message(self, tenant: Tenant, username: str, text: str):
        cl = self.get_client(tenant)
        if not cl: return False
        
        try:
            user_id = cl.user_id_from_username(username)
            cl.direct_send(text, [user_id])
            return True
        except Exception as e:
            print(f"Error sending Instagram message to {username}: {e}")
            return False

instagram_service = InstagramService()
