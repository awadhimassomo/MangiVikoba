from django.db import migrations, models


def add_group_type(apps, schema_editor):
    Kikoba = apps.get_model('groups', 'Kikoba')
    # Set a default value for existing records
    Kikoba.objects.update(group_type='standard')


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0007_entryfeepayment_notes_entryfeepayment_payment_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='kikoba',
            name='group_type',
            field=models.CharField(
                choices=[
                    ('standard', 'Standard VIKOBA (Variable-Share ASCA)'),
                    ('fixed_share', 'Fixed-Share VIKOBA'),
                    ('interest_refund', 'Interest Refund VIKOBA'),
                    ('rosca', 'ROSCA (Rotating Savings)'),
                    ('welfare', 'Welfare/Help Group (WCG)'),
                ],
                default='standard',
                max_length=20,
                null=True,
                help_text='Type of the group which determines the financial model used.'
            ),
        ),
        migrations.RunPython(add_group_type, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='kikoba',
            name='group_type',
            field=models.CharField(
                choices=[
                    ('standard', 'Standard VIKOBA (Variable-Share ASCA)'),
                    ('fixed_share', 'Fixed-Share VIKOBA'),
                    ('interest_refund', 'Interest Refund VIKOBA'),
                    ('rosca', 'ROSCA (Rotating Savings)'),
                    ('welfare', 'Welfare/Help Group (WCG)'),
                ],
                default='standard',
                max_length=20,
                help_text='Type of the group which determines the financial model used.'
            ),
        ),
    ]
