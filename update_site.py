from django.contrib.sites.models import Site

s = Site.objects.get_current()
s.domain = 'localhost:8080'
s.name = 'Skyconnect Local'
s.save()
print(f"✓ Site updated to: {s.domain}")
