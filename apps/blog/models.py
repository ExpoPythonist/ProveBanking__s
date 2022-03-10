from django.db import models


class Blog(models.Model):
    MAIN = 1
    ENTERPRISE = 2
    KIND_CHOICES = (
        (MAIN, 'Main blog'),
        (ENTERPRISE, 'Enterprise blog'),
    )
    heading = models.CharField(max_length=255)
    url = models.URLField()
    created = models.DateTimeField(auto_now_add=True)
    kind = models.PositiveSmallIntegerField(default=MAIN, choices=KIND_CHOICES)

    class Meta:
        ordering = ('-created', )

    def __unicode__(self):
        return self.heading