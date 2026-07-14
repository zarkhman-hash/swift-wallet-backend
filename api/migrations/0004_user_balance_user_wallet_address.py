import api.models
from django.db import migrations, models
import secrets

def gen_unique_wallet_addresses(apps, schema_editor):
    User = apps.get_model('api', 'User')
    for user in User.objects.all():
        if not user.wallet_address:
            user.wallet_address = "0x" + secrets.token_hex(20)
            user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_transfer_admin_meta'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='balance',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=20),
        ),
        migrations.AddField(
            model_name='user',
            name='wallet_address',
            field=models.CharField(max_length=42, null=True, blank=True),
        ),
        migrations.RunPython(gen_unique_wallet_addresses, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='user',
            name='wallet_address',
            field=models.CharField(default=api.models.generate_mock_wallet_address, max_length=42, unique=True),
        ),
    ]

