from django.db import models


class BuildData(models.Model):
    project = models.CharField(max_length=200, db_index=True)
    use = models.CharField(max_length=200, db_index=True)
    role = models.CharField(max_length=200, db_index=True)
    data_field = models.CharField(max_length=200, db_index=True)

    value = models.CharField(max_length=1024)

    class Meta:
        unique_together = (("project", "use", "role", "data_field",),)


class ProjectBuildNumber(models.Model):
    project = models.CharField(max_length=200, db_index=True)
