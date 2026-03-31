import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("childcheck")

class Model(base):
    class Meta:
        db_table = "push_subscriptions"

    id = pw.AutoField(primary_key=True)
    user_id = pw.CharField(max_length=32, index=True)
    endpoint = pw.TextField()
    p256dh = pw.TextField()
    auth = pw.TextField()
    device_type = pw.CharField(max_length=20, default='unknown')
    created_at = pw.DateTimeField(constraints=[pw.SQL('DEFAULT CURRENT_TIMESTAMP')])
