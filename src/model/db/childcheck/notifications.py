import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("childcheck")

class Model(base):
    class Meta:
        db_table = "notifications"

    id = pw.AutoField(primary_key=True)
    user_id = pw.CharField(max_length=32, index=True)
    type = pw.CharField(max_length=32)
    title = pw.CharField(max_length=128)
    message = pw.TextField(null=True)
    link = pw.CharField(max_length=256, default='')
    is_read = pw.BooleanField(default=False)
    created_at = pw.DateTimeField(constraints=[pw.SQL('DEFAULT CURRENT_TIMESTAMP')])
