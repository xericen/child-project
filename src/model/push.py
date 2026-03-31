import json
from pywebpush import webpush, WebPushException

PushSubscriptions = wiz.model("db/childcheck/push_subscriptions")
push_config = wiz.config("push")

class PushService:
    @staticmethod
    def send_to_user(user_id, title, body, url="/note", noti_type="general"):
        subs = PushSubscriptions.select().where(PushSubscriptions.user_id == str(user_id))
        payload = json.dumps({
            "title": title,
            "body": body,
            "url": url,
            "type": noti_type
        })
        expired = []
        for sub in subs:
            try:
                webpush(
                    subscription_info={
                        "endpoint": sub.endpoint,
                        "keys": {
                            "p256dh": sub.p256dh,
                            "auth": sub.auth
                        }
                    },
                    data=payload,
                    vapid_private_key=push_config.vapid.private_key,
                    vapid_claims={"sub": push_config.vapid.claims_email}
                )
            except WebPushException as e:
                if e.response and e.response.status_code in (404, 410):
                    expired.append(sub.id)
            except Exception:
                pass
        if expired:
            PushSubscriptions.delete().where(PushSubscriptions.id.in_(expired)).execute()

    @staticmethod
    def subscribe(user_id, endpoint, p256dh, auth, device_type="unknown"):
        existing = PushSubscriptions.select().where(
            (PushSubscriptions.user_id == str(user_id)) &
            (PushSubscriptions.endpoint == endpoint)
        ).first()
        if existing:
            return existing.id
        sub = PushSubscriptions.create(
            user_id=str(user_id),
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            device_type=device_type
        )
        return sub.id

    @staticmethod
    def unsubscribe(user_id, endpoint):
        PushSubscriptions.delete().where(
            (PushSubscriptions.user_id == str(user_id)) &
            (PushSubscriptions.endpoint == endpoint)
        ).execute()

Model = PushService()
