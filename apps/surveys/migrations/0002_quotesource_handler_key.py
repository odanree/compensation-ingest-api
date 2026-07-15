from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("surveys", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="quotesource",
            name="handler_key",
            field=models.CharField(
                db_index=True,
                default="solar_quote",
                help_text="Registered ingest handler that processes this source's submissions.",
                max_length=50,
            ),
        ),
    ]
