import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("childcheck")

class Model(base):
    class Meta:
        db_table = 'photo_comments'

    id = pw.AutoField()
    photo_id = pw.IntegerField(null=False, index=True)
    user_id = pw.IntegerField(null=False, index=True)
    content = pw.CharField(max_length=50, null=False)
    created_at = pw.DateTimeField(constraints=[pw.SQL('DEFAULT CURRENT_TIMESTAMP')])
